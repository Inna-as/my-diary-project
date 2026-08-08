import os
import json
from django.core.management.base import BaseCommand
from blog.models import FoodCategory, Ingredient, Article, RecipeIngredient


class Command(BaseCommand):
    help = 'Парсер JSON рецептов с умным парсингом количества'

    def parse_amount(self, value_str):
        """
        Умный парсер количества ингредиентов.
        - Числа, дроби, диапазоны → конвертирует
        - Текст, null, пусто → 1.0
        """
        if value_str is None or value_str == '':
            return 1.0

        if isinstance(value_str, (int, float)):
            return float(value_str)

        value_str = str(value_str).strip().replace(',', '.').replace(' ', '')

        if not value_str:
            return 1.0

        try:

            if '-' in value_str:
                parts = value_str.split('-')
                if len(parts) == 2:
                    try:
                        return (float(parts[0]) + float(parts[1])) / 2.0
                    except ValueError:
                        pass


            if '/' in value_str:
                parts = value_str.split('/')
                if len(parts) == 2:
                    try:
                        numerator = float(parts[0])
                        denominator = float(parts[1])
                        if denominator != 0:
                            return numerator / denominator
                    except ValueError:
                        pass


            if '~' in value_str:
                parts = value_str.split('~')
                if len(parts) == 2:
                    try:
                        return (float(parts[0]) + float(parts[1])) / 2.0
                    except ValueError:
                        pass

            return float(value_str)

        except (ValueError, TypeError):
            return 1.0

    def handle(self, *args, **options):
        base_dir = "recipes"

        self.stdout.write(self.style.WARNING("⏳ Запуск импорта рецептов..."))

        if not os.path.exists(base_dir):
            self.stdout.write(self.style.ERROR(f"❌ Папка '{base_dir}' не найдена!"))
            return

        # === КАТЕГОРИИ ИНГРЕДИЕНТОВ ===
        categories = [
            "Мясо и птица",
            "Рыба и морепродукты",
            "Овощи и зелень",
            "Молочные продукты",
            "Бакалея",
            "Фрукты и ягоды",
            "Колбасные изделия",
            "Субпродукты",
            "Разное"
        ]
        cat_objects = {}
        for cat_name in categories:
            obj, _ = FoodCategory.objects.get_or_create(name=cat_name)
            cat_objects[cat_name] = obj

        # КАТЕГОРИИ РЕЦЕПТОВ (ПОЛЕ category В Article)

        RECIPE_CATEGORY_MAP = {
            # ===== DESSERT (Десерт) =====
            'десерт': 'dessert',
            'торт': 'dessert',
            'пирог': 'dessert',
            'чизкейк': 'dessert',
            'тирамису': 'dessert',
            'пудинг': 'dessert',
            'желе': 'dessert',
            'мусс': 'dessert',
            'парфе': 'dessert',
            'варенье': 'dessert',
            'джем': 'dessert',
            'конфитюр': 'dessert',

            # ===== FIRST (Первые блюда / супы) =====
            'суп': 'first',
            'борщ': 'first',
            'солянка': 'first',
            'рассольник': 'first',
            'щи': 'first',
            'окрошка': 'first',
            'минестроне': 'first',
            'уха': 'first',
            'свекольник': 'first',
            'похлебка': 'first',
            'бульон': 'first',
            'крем-суп': 'first',
            'суп-пюре': 'first',

            # ===== BAKING (Выпечка) =====
            'блины': 'baking',
            'оладьи': 'baking',
            'сырники': 'baking',
            'панкейки': 'baking',
            'вафли': 'baking',
            'печенье': 'baking',
            'пирожки': 'baking',
            'булочки': 'baking',
            'калачи': 'baking',
            'бублики': 'baking',
            'баранки': 'baking',
            'сушки': 'baking',
            'пряники': 'baking',
            'кексы': 'baking',
            'маффины': 'baking',
            'выпечка': 'baking',
            'кулич': 'baking',
            'лаваш': 'baking',
            'хлеб': 'baking',
            'батон': 'baking',
            'гренки': 'baking',

            # ===== SECOND (Вторые блюда) =====
            'котлеты': 'second',
            'пельмени': 'second',
            'плов': 'second',
            'гуляш': 'second',
            'рагу': 'second',
            'шашлык': 'second',
            'стейк': 'second',
            'азу': 'second',
            'бефстроганов': 'second',
            'шницель': 'second',
            'антрекот': 'second',
            'бифштекс': 'second',
            'тефтели': 'second',
            'фрикадельки': 'second',
            'биточки': 'second',
            'голубцы': 'second',
            'жаркое': 'second',
            'зразы': 'second',
            'долма': 'second',
            'манты': 'second',
            'хинкали': 'second',
            'чучвара': 'second',
            'лазанья': 'second',
            'каннеллони': 'second',
            'равиоли': 'second',
            'паста': 'second',
            'спагетти': 'second',
            'каша': 'second',
            'собо': 'second',
            'макароны': 'second',
            'рис': 'second',
            'гречка': 'second',
            'овсянка': 'second',
            'манка': 'second',
            'пшено': 'second',
            'перловка': 'second',
            'картофель': 'second',
            'картошка': 'second',
            'фарш': 'second',
            'мясо': 'second',
            'курица': 'second',
            'свинина': 'second',
            'говядина': 'second',
            'индейка': 'second',
            'утка': 'second',
            'гусь': 'second',
            'рыба': 'second',
            'грибы': 'second',
            'овощи': 'second',
            'филе': 'second',
            'грудка': 'second',

            # ===== SALAD (Салаты) ===== 👈👈👈 ВАЖНО!
            'салат': 'salad',
            'винегрет': 'salad',
            'оливье': 'salad',
            'цезарь': 'salad',
            'шуба': 'salad',
            'греческий': 'salad',

            # ===== APPETIZER (Закуски) =====
            'закуска': 'appetizer',
            'канапе': 'appetizer',
            'тарталетки': 'appetizer',
            'намазка': 'appetizer',
            'паштет': 'appetizer',
            'сальтисон': 'appetizer',
            'буженина': 'appetizer',
            'шпроты': 'appetizer',
            'соленья': 'appetizer',
            'маринады': 'appetizer',

            # ===== SNACK (Перекусы) =====
            'бутерброд': 'snack',
            'сэндвич': 'snack',
            'гамбургер': 'snack',
            'чизбургер': 'snack',
            'чипсы': 'snack',
            'сухарики': 'snack',
            'орехи': 'snack',
            'семечки': 'snack',

            # ===== DRINK (Напитки) =====
            'напиток': 'drink',
            'кофе': 'drink',
            'чай': 'drink',
            'компот': 'drink',
            'морс': 'drink',
            'квас': 'drink',
            'смузи': 'drink',
            'коктейль': 'drink',
            'лимонад': 'drink',
            'содовая': 'drink',
            'глинтвейн': 'drink',
            'пунш': 'drink',
            'сбитень': 'drink',
        }
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()

        if not admin_user:
            self.stdout.write(self.style.ERROR("❌ Сначала создайте суперпользователя!"))
            return

        imported_count = 0
        category_stats = {cat: 0 for cat in RECIPE_CATEGORY_MAP.values()}
        category_stats['main'] = 0  # Категория по умолчанию

        self.stdout.write(self.style.SUCCESS("🚀 Начинаем импорт..."))

        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            recipe = json.load(f)
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Ошибка чтения {file}: {e}"))
                        continue

                    # Название рецепта
                    title = recipe.get('title', '').strip()
                    if not title:
                        continue

                    # Инструкции
                    instruction_data = recipe.get('instruction', [])
                    if isinstance(instruction_data, list):
                        instructions = "\n\n".join([
                            step.get('text', '') for step in instruction_data
                            if isinstance(step, dict) and step.get('text')
                        ])
                    else:
                        instructions = str(instruction_data)

                    if not instructions.strip():
                        continue

                    # Проверка дубликатов
                    if Article.objects.filter(title=title).exists():
                        self.stdout.write(self.style.WARNING(f"⏭️ Рецепт '{title}' уже существует"))
                        continue


                    # ОПРЕДЕЛЯЕМ КАТЕГОРИЮ РЕЦЕПТА

                    recipe_category = 'main'


                    title_lower = title.lower()
                    for keyword, category in RECIPE_CATEGORY_MAP.items():
                        if keyword in title_lower:
                            recipe_category = category
                            break

                    # Создание рецепта
                    try:
                        article = Article(
                            title=title,
                            author=admin_user,
                            instructions=instructions,
                            is_published=True,
                            category=recipe_category
                        )
                        article.save()

                        if not article.id:
                            self.stdout.write(self.style.ERROR(f"❌ Рецепт '{title}' не сохранился!"))
                            continue

                        self.stdout.write(self.style.SUCCESS(
                            f"✅ Создан рецепт: {title} (id={article.id}, category={recipe_category})"))


                        if recipe_category in category_stats:
                            category_stats[recipe_category] += 1
                        else:
                            category_stats['main'] += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Ошибка создания рецепта '{title}': {e}"))
                        import traceback
                        self.stdout.write(self.style.ERROR(traceback.format_exc()))
                        continue

                    # === ИНГРЕДИЕНТЫ ===
                    ingredients_data = recipe.get('ingredients', [])

                    for ing_section in ingredients_data:
                        if not isinstance(ing_section, dict):
                            continue

                        ingredients_list = ing_section.get('list', [])

                        for ing_data in ingredients_list:
                            if not isinstance(ing_data, dict):
                                continue

                            # Название ингредиента
                            ing_name_raw = ing_data.get('name', '')
                            if ing_name_raw is None:
                                ing_name_raw = ''
                            ing_name = str(ing_name_raw).strip().lower()

                            if not ing_name:
                                continue

                            # Количество
                            value_raw = ing_data.get('value', None)
                            amount = self.parse_amount(value_raw)

                            # Единица измерения
                            unit_raw = ing_data.get('type', 'г')
                            if unit_raw is None:
                                unit = 'г'
                            else:
                                unit = str(unit_raw).strip() or 'г'


                            # ОПРЕДЕЛЯЕМ КАТЕГОРИЮ ИНГРЕДИЕНТА


                            # Категория 1: КОЛБАСНЫЕ ИЗДЕЛИЯ
                            if any(x in ing_name for x in [
                                'колбаса', 'колбасный', 'колбасные', 'сосиски', 'сосисочные',
                                'сардельки', 'сарделька', 'ветчина', 'ветчинная', 'прошутто',
                                'пастрома', 'бекон', 'шпик', 'панчетта', 'грудинка', 'грудинку',
                                'грудинка копченая', 'грудинка вяленая', 'окорок', 'окорока',
                                'окорочка', 'рулет', 'рулеты', 'рулеты мясные', 'буженина',
                                'карбонад', 'корейка', 'корейка копченая', 'шейка', 'шейка копченая',
                                'шейка вяленая', 'рулька', 'рульки', 'суджук', 'сала', 'салю'
                            ]):
                                current_cat = cat_objects["Колбасные изделия"]

                            # Категория 2: РЫБА И МОРЕПРОДУКТЫ
                            elif any(x in ing_name for x in [
                                'лосось', 'семга', 'форель', 'треска', 'судак', 'окунь', 'щука', 'карп',
                                'сом', 'селёдка', 'сельдь', 'скумбрия', 'горбуша', 'тунец', 'минтай',
                                'хек', 'пикша', 'сардины', 'анчоусы', 'палтус', 'камбала', 'навага',
                                'мойва', 'корюшка', 'толстолобик', 'амур', 'белуга', 'осетрина',
                                'угорь', 'макрель', 'сазан', 'карась', 'налим', 'севрюга', 'стерлядь',
                                'креветки', 'кальмары', 'осьминог', 'мидии', 'устрицы', 'гребешок',
                                'краб', 'омар', 'лобстер', 'лангуст', 'раки', 'икра'
                            ]):
                                current_cat = cat_objects["Рыба и морепродукты"]

                            # Категория 3: МЯСО И ПТИЦА (БЕЗ КОЛБАС!)
                            elif any(x in ing_name for x in [
                                'курица', 'куры', 'куропатка', 'цыплёнок', 'цыпленок',
                                'индейка', 'индюшатина',
                                'гусь', 'утка', 'перепёлка', 'перепел', 'фазан',
                                'куриная грудка', 'куриные грудки', 'грудка куриная',
                                'куриное бедро', 'куриные бедра', 'бедро куриное', 'бёдрышки',
                                'куриная голень', 'куриные голени', 'голень куриная',
                                'куриное крыло', 'куриные крылья', 'крылышки',
                                'куриный окорочок', 'куриные окорочка', 'окорочок',
                                'куриная спинка', 'куриные спинки',
                                'куриный хребет', 'куриные хребты',
                                'куриный каркас',
                                'свинина', 'говядина', 'телятина', 'баранина', 'ягнятина',
                                'козлятина', 'кролик', 'крольчатина', 'оленина', 'конина',
                                'свиная шея', 'свиная шейка', 'шейка свиная',
                                'свиные рёбра', 'свиные ребра', 'ребрышки', 'рёбрышки',
                                'свиная грудинка', 'грудинка свиная',
                                'свиная корейка', 'корейка свиная',
                                'свиная вырезка', 'вырезка свиная',
                                'свиная лопатка', 'лопатка свиная',
                                'свиная рулька', 'рулька свиная',
                                'свиные ножки', 'ножки свиные',
                                'говяжья грудинка', 'грудинка говяжья',
                                'говяжья вырезка', 'вырезка говяжья',
                                'говяжья лопатка', 'лопатка говяжья',
                                'говяжий окорок', 'окорок говяжий',
                                'баранья нога', 'бараньи рёбра',
                                'окорок', 'шейка', 'лопатка',
                                'сало', 'шпик', 'балык',
                                'стейк', 'антрекот', 'бифштекс', 'шницель', 'ромштекс',
                                'эскалоп', 'карбонад',
                                'мякоть', 'мясо', 'фарш'
                            ]):
                                current_cat = cat_objects["Мясо и птица"]

                            #Категория 4: СУБПРОДУКТЫ
                            elif any(x in ing_name for x in [
                                # Основные субпродукты
                                'печень', 'печёнка', 'печенка',
                                'почки',
                                'сердце', 'сердечки',
                                'язык',
                                'мозги',
                                'лёгкие', 'лёгкое', 'легкое',
                                'рубец',
                                'вымя',
                                'селезёнка', 'селезенка',

                                # Менее популярные
                                'трахея', 'трахеи',
                                'хвост', 'хвосты',
                                'уши', 'ухо',
                                'голова', 'головы',

                                # Технические
                                'обрезь'
                            ]):
                                current_cat = cat_objects["Субпродукты"]

                            # Категория 5: ОВОЩИ И ЗЕЛЕНЬ
                            elif any(x in ing_name for x in [
                                'томат', 'помидор', 'огурец', 'лук', 'чеснок', 'картофель', 'картошка',
                                'морковь', 'свёкла', 'свекла', 'капуста', 'кабачок', 'тыква',
                                'баклажан', 'перец', 'болгарский', 'сладкий', 'горошек', 'кукуруза',
                                'горох', 'фасоль', 'чечевица', 'нут', 'бобы',
                                'сельдерей', 'спаржа', 'брокколи', 'цветная', 'брюква', 'репа', 'редис', 'редька',
                                'имбирь', 'хрен', 'горчица', 'артишок', 'кольраби', 'пастернак', 'топинамбур',
                                'укроп', 'петрушка', 'кинза', 'базилик', 'орегано', 'тимьян', 'розмарин',
                                'лавровый', 'рукола', 'шпинат', 'мята', 'мелисса', 'чебрец', 'эстрагон',
                                'душица', 'лавр', 'лист', 'зелень', 'зелёный', 'веточка', 'стебель', 'пучок',
                                'грибы', 'шампиньоны', 'вешенки', 'опята', 'маслята', 'белый гриб', 'лисички',
                                'рыжики', 'подосиновик', 'подберёзовик', 'подберезовик', 'сморчки', 'строчки',
                                'чили', 'кайенский', 'паприка', 'халапеньо', 'хабанеро',
                                'горький', 'острый', 'стручок'
                            ]):
                                current_cat = cat_objects["Овощи и зелень"]

                            # Категория 6: МОЛОЧНЫЕ ПРОДУКТЫ
                            elif any(x in ing_name for x in [
                                'молоко', 'сливки', 'сметана', 'йогурт', 'кефир', 'ряженка', 'простокваша',
                                'творог', 'творожный', 'сыр', 'брынза', 'фета', 'моцарелла',
                                'пармезан', 'рикотта', 'маскарпоне', 'камамбер', 'бри', 'дорблю',
                                'гауда', 'эдам', 'чеддер', 'эмменталь', 'российский', 'пошехонский',
                                'сливочный', 'молочный', 'масло сливочное',

                            ]):
                                current_cat = cat_objects["Молочные продукты"]

                            # Категория 7: БАКАЛЕЯ
                            elif any(x in ing_name for x in [
                                # Мука, сахар, соль
                                'мука', 'сахар', 'сахарная пудра', 'соль',

                                # Масла
                                'подсолнечное масло', 'оливковое масло', 'растительное масло',
                                'кукурузное масло', 'рапсовое масло', 'льняное масло',
                                'горчичное масло', 'кунжутное масло', 'арахисовое масло',

                                # Крупы
                                'рис', 'гречка', 'гречневая крупа',
                                'овсянка', 'овсяная крупа', 'геркулес',
                                'манка', 'манная крупа',
                                'пшено', 'перловка', 'перловая крупа',
                                'ячневая крупа', 'кукурузная крупа',
                                'булгур', 'киноа', 'просо', 'сорго',

                                # Макаронные изделия
                                'макароны', 'паста', 'спагетти', 'вермишель', 'лапша',
                                'равиоли', 'каннелони', 'лазанья',

                                # Хлеб и выпечка
                                'лаваш', 'хлеб', 'булочки', 'батон',
                                'сухари', 'панировочные сухари', 'гренки',

                                # Какао и шоколад
                                'какао', 'какао-порошок', 'шоколад',

                                # Специи
                                'ваниль', 'ванилин',
                                'корица', 'кардамон', 'гвоздика',
                                'бадьян', 'анис', 'фенугрек', 'пажитник',
                                'кумин', 'зира', 'куркума', 'шафран',
                                'мускатный орех', 'мускат',
                                'карри', 'хмели-сунели', 'аджика',

                                # Орехи
                                'орехи', 'миндаль', 'фундук', 'арахис', 'кешью',
                                'грецкие орехи', 'кедровые орехи', 'фисташки',

                                # Семечки и семена
                                'семечки', 'кунжут', 'лён', 'семена льна',
                                'тыквенные семечки', 'подсолнечные семечки',

                                # Кокос
                                'кокос', 'кокосовая стружка',

                                # Соусы и пасты
                                'томатная паста', 'кетчуп', 'майонез', 'соевый соус',

                                # Уксус и кислоты
                                'уксус', 'лимонный сок',

                                # Мёд
                                'мёд', 'мед'
                            ]):

                                current_cat = cat_objects["Бакалея"]

                            # Категория 8: ЯГОДЫ И ФРУКТЫ
                            elif any(x in ing_name for x in [
                                # Фрукты
                                'яблоко', 'яблоки',
                                'груша', 'груши',
                                'банан', 'бананы',
                                'апельсин', 'апельсины',
                                'мандарин', 'мандарины',
                                'лимон', 'лайм',
                                'киви', 'ананас',
                                'персик', 'персики',
                                'абрикос', 'абрикосы',
                                'слива', 'сливы',
                                'айва', 'хурма',
                                'гранат', 'инжир',
                                'финики', 'финик',
                                'арбуз', 'дыня',
                                'виноград',

                                # Ягоды
                                'черешня', 'вишня',
                                'клубника', 'земляника',
                                'малина', 'ежевика',
                                'смородина', 'черная смородина', 'красная смородина',
                                'черника', 'голубика',
                                'брусника', 'клюква',
                                'калина', 'рябина',
                                'облепиха', 'шиповник',
                                'крыжовник', 'черемуха',

                                # Сухофрукты
                                'изюм', 'курага', 'чернослив',
                                'сушёные яблоки', 'сушеные яблоки',
                                'сушёные груши', 'сушеные груши',
                                'сухофрукты', 'цукаты'
                            ]):
                                current_cat = cat_objects["Фрукты и ягоды"]


                            # Категория 9: РАЗНОЕ
                            else:
                                current_cat = cat_objects["Разное"]

                            # Создаём или получаем ингредиент
                            ingredient, created = Ingredient.objects.get_or_create(
                                name=ing_name,
                                defaults={'category': current_cat}
                            )

                            # Добавляем ингредиент к рецепту
                            try:
                                if not article.id:
                                    self.stdout.write(self.style.ERROR(
                                        f"❌ Ошибка: объект article не имеет id"
                                    ))
                                    continue

                                recipe_ingredient = RecipeIngredient(
                                    recipe=article,
                                    ingredient=ingredient,
                                    amount=amount,
                                    unit=unit
                                )
                                recipe_ingredient.save()
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(
                                    f"⚠️ Ошибка добавления ингредиента '{ing_name}': {e}"
                                ))
                                import traceback
                                self.stdout.write(self.style.WARNING(traceback.format_exc()))
                                continue

                    imported_count += 1

        # Выводим статистику по категориям рецептов
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("📊 Статистика по категориям рецептов:"))
        for category, count in sorted(category_stats.items()):
            if count > 0:
                self.stdout.write(self.style.SUCCESS(f"   - {category}: {count} рецептов"))

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS(
            f"🎉 Импорт завершён! Обработано рецептов: {imported_count}"
        ))