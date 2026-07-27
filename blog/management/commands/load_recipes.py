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
            # Диапазон: "4-5", "400-500"
            if '-' in value_str:
                parts = value_str.split('-')
                if len(parts) == 2:
                    try:
                        return (float(parts[0]) + float(parts[1])) / 2.0
                    except ValueError:
                        pass

            # Дробь: "1/2", "1/3", "3/4"
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

            # Тильда: "4~5"
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

        # ============================================
        # ============================================
        # КАТЕГОРИИ РЕЦЕПТОВ (ПОЛЕ category В Article)
        # ============================================
        RECIPE_CATEGORY_MAP = {
            # ===== DESSERT (Десерты) =====
            'варенье': 'dessert',
            'апельсин': 'dessert',
            'апельсиновый': 'dessert',
            'десерт': 'dessert',
            'торт': 'dessert',
            'пирог': 'dessert',
            'чизкейк': 'dessert',
            'тирамису': 'dessert',
            'пудинг': 'dessert',
            'желе': 'dessert',
            'мусс': 'dessert',
            'парфе': 'dessert',
            'крем': 'dessert',
            'молочный': 'dessert',
            'сладкий': 'dessert',
            'шоколадный': 'dessert',
            'ванильный': 'dessert',
            'фруктовый': 'dessert',
            'ягодный': 'dessert',
            'ореховый': 'dessert',
            'кокосовый': 'dessert',
            'кофейный': 'dessert',
            'лимонный': 'dessert',
            'клубничный': 'dessert',
            'малиновый': 'dessert',
            'вишневый': 'dessert',
            'черничный': 'dessert',
            'смородиновый': 'dessert',
            'клюквенный': 'dessert',
            'брусничный': 'dessert',
            'калиновый': 'dessert',
            'рябиновый': 'dessert',
            'облепиховый': 'dessert',
            'шиповниковый': 'dessert',
            'абрикосовый': 'dessert',
            'персиковый': 'dessert',
            'сливовый': 'dessert',
            'яблочный': 'dessert',
            'грушевый': 'dessert',
            'ананасовый': 'dessert',
            'кививый': 'dessert',
            'манговый': 'dessert',
            'банановый': 'dessert',
            'хурмовый': 'dessert',
            'гранатовый': 'dessert',
            'инжирный': 'dessert',
            'фиговый': 'dessert',
            'финиковый': 'dessert',
            'арбузный': 'dessert',
            'дынный': 'dessert',
            'виноградный': 'dessert',
            'черешневый': 'dessert',
            'земляничный': 'dessert',
            'ежевичный': 'dessert',
            'голубичный': 'dessert',
            'крыжовниковый': 'dessert',
            'черемуховый': 'dessert',

            # ===== SOUP (Супы) =====
            'борщ': 'soup',
            'борщовый': 'soup',
            'суп': 'soup',
            'солянка': 'soup',
            'рассольник': 'soup',
            'щи': 'soup',
            'окрошка': 'soup',
            'минестроне': 'soup',
            'лапша': 'soup',
            'уха': 'soup',
            'рыбный': 'soup',
            'куриный': 'soup',
            'мясной': 'soup',
            'овощной': 'soup',
            'грибной': 'soup',
            'свекольник': 'soup',
            'щавелевый': 'soup',
            'солянка': 'soup',
            'похлебка': 'soup',
            'бульон': 'soup',
            'холодный': 'soup',

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
            'мучной': 'baking',
            'песочный': 'baking',
            'сдобный': 'baking',
            'дрожжевой': 'baking',
            'бисквитный': 'baking',
            'заварной': 'baking',
            'слоеный': 'baking',
            'вафельный': 'baking',
            'лаваш': 'baking',
            'хлеб': 'baking',
            'батон': 'baking',
            'сухари': 'baking',
            'гренки': 'baking',
            'панировочные': 'baking',

            # ===== MAIN (Основные блюда) =====
            'картофель': 'main',
            'котлеты': 'main',
            'пельмени': 'main',
            'плов': 'main',
            'гуляш': 'main',
            'рагу': 'main',
            'шашлык': 'main',
            'стейк': 'main',
            'азу': 'main',
            'бефстроганов': 'main',
            'шницель': 'main',
            'антрекот': 'main',
            'бифштекс': 'main',
            'тефтели': 'main',
            'фрикадельки': 'main',
            'биточки': 'main',
            'голубцы': 'main',
            'перц': 'main',  # 注意：可能需要根据具体情况匹配全名，如"перец"
            'жаркое': 'main',
            'зразы': 'main',
            'картошка': 'main',
            'картофельный': 'main',
            'собо': 'main',
            'долма': 'main',
            'манты': 'main',
            'хинкали': 'main',
            'чучвара': 'main',
            'солянка': 'soup',  # 重新定义：солянка是soup
            'макароны': 'main',
            'паста': 'main',
            'спагетти': 'main',
            'вермишель': 'main',
            'лапша': 'soup',  # 重新定义：лапша是soup
            'равиоли': 'main',
            'каннеллони': 'main',
            'лазанья': 'main',
            'рис': 'main',
            'гречка': 'main',
            'гречневая': 'main',
            'овсянка': 'main',
            'овсяная': 'main',
            'манка': 'main',
            'пшено': 'main',
            'перловка': 'main',
            'ячневая': 'main',
            'кукурузная': 'main',
            'булгур': 'main',
            'киноа': 'main',
            'просо': 'main',
            'сорго': 'main',
            'каша': 'main',
            'кукуруза': 'main',
            'горошек': 'main',
            'грибы': 'main',
            'овощи': 'main',
            'мясо': 'main',
            'курица': 'main',
            'индейка': 'main',
            'гусь': 'main',
            'утка': 'main',
            'филе': 'main',
            'грудка': 'main',
            'ножка': 'main',
            'крылышки': 'main',
            'бедро': 'main',
            'свинина': 'main',
            'сало': 'main',
            'шейка': 'main',
            'окорок': 'main',
            'ребра': 'main',
            'лопатка': 'main',
            'корейка': 'main',
            'вырезка': 'main',
            'говядина': 'main',
            'говяжий': 'main',
            'рулька': 'main',
            'грудинка': 'main',
            'телятина': 'main',
            'баранина': 'main',
            'ягнятина': 'main',
            'фарш': 'main',

            # ===== APPETIZER (Закуски - SALAT в эту категорию!) =====
            'винегрет': 'appetizer',
            'салат': 'appetizer',
            'греческий': 'appetizer',
            'цезарь': 'appetizer',
            'оливье': 'appetizer',
            'шуба': 'appetizer',
            'грибной': 'appetizer',
            'овощной': 'appetizer',
            'мясной': 'appetizer',
            'рыбный': 'appetizer',
            'куриный': 'appetizer',
            'консервированный': 'appetizer',
            'морковный': 'appetizer',
            'капустный': 'appetizer',
            'огуречный': 'appetizer',
            'помидорный': 'appetizer',
            'свекольный': 'appetizer',
            'картофельный': 'appetizer',
            'фруктовый': 'appetizer',
            'ягодный': 'appetizer',
            'закуска': 'appetizer',
            'канапе': 'appetizer',
            'тарталетки': 'appetizer',
            'намазка': 'appetizer',
            'паштет': 'appetizer',
            'сальтисон': 'appetizer',
            'буженина': 'appetizer',
            'рулет': 'appetizer',
            'шпроты': 'appetizer',
            'рыбные': 'appetizer',
            'икра': 'appetizer',
            'селедка': 'appetizer',
            'соленья': 'appetizer',
            'маринады': 'appetizer',
            'соленые': 'appetizer',
            'маринованные': 'appetizer',
            'квашеные': 'appetizer',
            'соленые огурцы': 'appetizer',
            'квашеная капуста': 'appetizer',
            'соленые помидоры': 'appetizer',
            'маринованные грибы': 'appetizer',
            'соленая рыба': 'appetizer',
            'соленое сало': 'appetizer',
            'маринованные овощи': 'appetizer',
            'закуски': 'appetizer',

            # ===== SNACK (Перекусы) =====
            'бутерброд': 'snack',
            'сэндвич': 'snack',
            'гамбургер': 'snack',
            'чизбургер': 'snack',
            'орехи': 'snack',
            'семечки': 'snack',
            'чипсы': 'snack',
            'сухарики': 'snack',

            # ===== DRINK (Напитки) =====
            'кофе': 'drink',
            'чай': 'drink',
            'сок': 'drink',
            'компот': 'drink',
            'морс': 'drink',
            'квас': 'drink',
            'смузи': 'drink',
            'коктейль': 'drink',
            'лимонад': 'drink',
            'содовая': 'drink',
            'минеральная': 'drink',
            'газированная': 'drink',
            'энергетик': 'drink',
            'алкогольный': 'drink',
            'водка': 'drink',
            'коньяк': 'drink',
            'виски': 'drink',
            'ром': 'drink',
            'джин': 'drink',
            'текила': 'drink',
            'ликер': 'drink',
            'вино': 'drink',
            'шампанское': 'drink',
            'пиво': 'drink',
            'сидр': 'drink',
            'медовуха': 'drink',
            'глинтвейн': 'drink',
            'пунш': 'drink',
            'грог': 'drink',
            'эгг-ног': 'drink',
            'холодный': 'drink',
            'горячий': 'drink',
            'безалкогольный': 'drink',
            'молочный': 'drink',
            'шоколадный': 'drink',
            'фруктовый': 'drink',
            'ягодный': 'drink',
            'овощной': 'drink',
            'зеленый': 'drink',
            'куркума': 'drink',
            'имбирный': 'drink',
            'мятный': 'drink',
            'напиток': 'drink',
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

                    # ============================================
                    # ОПРЕДЕЛЯЕМ КАТЕГОРИЮ РЕЦЕПТА
                    # ============================================
                    recipe_category = 'main'  # Категория по умолчанию

                    # Пробуем определить категорию по названию рецепта
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
                            category=recipe_category  # ← Добавили категорию!
                        )
                        article.save()

                        if not article.id:
                            self.stdout.write(self.style.ERROR(f"❌ Рецепт '{title}' не сохранился!"))
                            continue

                        self.stdout.write(self.style.SUCCESS(
                            f"✅ Создан рецепт: {title} (id={article.id}, category={recipe_category})"))

                        # Считаем статистику по категориям
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

                            # Количество (умный парсер!)
                            value_raw = ing_data.get('value', None)
                            amount = self.parse_amount(value_raw)

                            # Единица измерения
                            unit_raw = ing_data.get('type', 'г')
                            if unit_raw is None:
                                unit = 'г'
                            else:
                                unit = str(unit_raw).strip() or 'г'

                            # ============================================
                            # ОПРЕДЕЛЯЕМ КАТЕГОРИЮ ИНГРЕДИЕНТА (ПОЛНЫЕ СПИСКИ!)
                            # ============================================

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

                                # Масла (только конкретные!)
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
                                # Фрукты (единственное + множественное число)
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