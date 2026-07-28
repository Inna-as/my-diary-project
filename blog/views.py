from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db.models import Count, Q
from django.http import JsonResponse
from .models import (
    Article, FoodCategory, Ingredient, RecipeIngredient,
    IngredientSubstitution, FavoriteRecipe, CustomUser, Comment
)
from .forms import CustomUserCreationForm, UserProfileForm, ArticleForm
import time


# ============ ГЛАВНАЯ СТРАНИЦА ============
def index_view(request):
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'new')

    articles_list = Article.objects.annotate(
        favorites_count=Count('favored_by'),
        comments_count=Count('comments')
    )

    if sort_by == 'old':
        articles_list = articles_list.order_by('created_at')
    elif sort_by == 'popular':
        articles_list = articles_list.order_by('-favorites_count', '-created_at')
    else:
        articles_list = articles_list.order_by('-created_at')

    if query:
        words = query.split()
        search_filter = Q()
        for word in words:
            word_filter = (
                    Q(title__icontains=word) |
                    Q(instructions__icontains=word)
            )
            search_filter &= word_filter
        articles_list = articles_list.filter(search_filter)

    paginator = Paginator(articles_list, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by,
    }
    return render(request, 'blog/index.html', context)


# ============ ДЕТАЛЬНАЯ СТРАНИЦА РЕЦЕПТА (ОБНОВЛЕНО) ============
def article_detail_view(request, pk):
    article = get_object_or_404(
        Article.objects.annotate(comments_count=Count('comments')),
        pk=pk
    )
    recipe_ingredients = article.recipe_ingredients.select_related('ingredient', 'ingredient__category').all()
    portions = int(request.GET.get('portions', 1))

    ingredients_with_amounts = []
    for ri in recipe_ingredients:
        ingredients_with_amounts.append({
            'ingredient': ri.ingredient,
            'amount': ri.amount * portions,
            'unit': ri.unit,
        })

    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = FavoriteRecipe.objects.filter(
            user=request.user,
            recipe=article
        ).exists()

    can_edit = False
    if request.user.is_authenticated:
        can_edit = (request.user == article.author) or request.user.is_superuser

    # Загружаем комментарии с ответами (2 уровня)
    comments = article.comments.select_related('author', 'parent').prefetch_related('replies__author').order_by('-created_at')

    # Обработка создания комментария или ответа
    if request.method == 'POST' and 'comment_text' in request.POST:
        if request.user.is_authenticated:
            comment_text = request.POST.get('comment_text', '').strip()
            parent_id = request.POST.get('parent_id', '').strip()

            if comment_text:
                # Если есть parent_id - создаём ответ на комментарий
                if parent_id:
                    try:
                        parent_comment = Comment.objects.get(id=parent_id)
                        Comment.objects.create(
                            article=article,
                            author=request.user,
                            text=comment_text,
                            parent=parent_comment  # <-- Добавляем связь с родительским комментарием
                        )
                    except Comment.DoesNotExist:
                        # Если родительский комментарий не найден - создаём обычный комментарий
                        Comment.objects.create(
                            article=article,
                            author=request.user,
                            text=comment_text
                        )
                else:
                    # Обычный комментарий
                    Comment.objects.create(
                        article=article,
                        author=request.user,
                        text=comment_text
                    )
                return redirect('blog:article_detail', pk=pk)

    likes_count = article.favored_by.count()

    context = {
        'article': article,
        'recipe_ingredients': recipe_ingredients,
        'ingredients_with_amounts': ingredients_with_amounts,
        'portions': portions,
        'is_favorite': is_favorite,
        'can_edit': can_edit,
        'comments': comments,
        'likes_count': likes_count,
    }
    return render(request, 'blog/article_detail.html', context)

# ============ РЕГИСТРАЦИЯ ============
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('blog:index')
    else:
        form = CustomUserCreationForm()

    return render(request, 'blog/register.html', {'form': form})


# ============ СОЗДАНИЕ РЕЦЕПТА ============
@login_required
def article_create_view(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)  # Не сохраняем сразу в БД
            article.author = request.user       # Добавляем автора
            article.save()                      # Теперь сохраняем
            return redirect('blog:article_detail', pk=article.pk)
    else:
        form = ArticleForm()

    return render(request, 'blog/article_form.html', {'form': form})

# ============ РЕДАКТИРОВАНИЕ РЕЦЕПТА ============
@login_required
def article_update_view(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            return redirect('blog:article_detail', pk=article.pk)
    else:
        form = ArticleForm(instance=article)

    return render(request, 'blog/article_form.html', {'form': form})


# ============ УДАЛЕНИЕ РЕЦЕПТА ============
@login_required
def article_delete_view(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if request.method == 'POST':
        article.delete()
        return redirect('blog:index')

    return render(request, 'blog/article_confirm_delete.html', {'article': article})


# ============ ПРОФИЛЬ АВТОРА ============
def author_profile_view(request, username):
    author = get_object_or_404(CustomUser, username=username)
    total_articles = author.article_set.count()
    author_articles = author.article_set.all().order_by('-created_at')

    return render(request, 'blog/author_profile.html', {
        'author': author,
        'total_articles': total_articles,
        'author_articles': author_articles
    })


# ============ ЛИЧНЫЙ КАБИНЕТ ============
@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile')
    else:
        form = UserProfileForm(instance=request.user)

    user_recipes_count = request.user.article_set.count()
    user_favorites_count = request.user.favorite_recipes.count()
    favorite_recipes = request.user.favorite_recipes.all().order_by('-id')[:6]

    context = {
        'form': form,
        'user_recipes_count': user_recipes_count,
        'user_favorites_count': user_favorites_count,
        'favorite_recipes': favorite_recipes,
    }
    return render(request, 'blog/profile.html', context)


# ============ УМНЫЙ ХОЛОДИЛЬНИК - ГЛАВНАЯ СТРАНИЦА ============
@login_required
def fridge_view(request):
    """Главная страница умного холодильника"""
    categories = FoodCategory.objects.prefetch_related('ingredients').all()

    context = {
        'categories': categories,
    }
    return render(request, 'blog/fridge.html', context)


# ============ УМНЫЙ ХОЛОДИЛЬНИК - РЕЗУЛЬТАТЫ (ОБНОВЛЕНО) ============
@login_required
def fridge_results_view(request):
    """
    Оптимизированная функция результатов поиска.
    Поддерживает:
    - Поиск по ингредиентам
    - Поиск только по категории блюда
    - Поиск по категории + ингредиенты
    """
    # Получаем выбранную категорию блюда (с значением по умолчанию)
    selected_category = (request.POST.get('category') or
                         request.GET.get('category') or '')

    # Получаем ингредиенты из разных источников
    selected_ingredients = []
    ingredients_text = ''

    if request.method == 'POST':
        # Приоритет текстовому вводу
        ingredients_text = request.POST.get('ingredients_text', '').strip()

        if ingredients_text:
            # Парсим текстовый ввод и ищем ингредиенты по названию
            ingredient_names = [name.strip() for name in ingredients_text.split(',') if name.strip()]

            # Поиск ингредиентов по названию (нечувствительный к регистру)
            for name in ingredient_names:
                matching_ingredients = Ingredient.objects.filter(name__icontains=name)
                selected_ingredients.extend([ing.id for ing in matching_ingredients])
        else:
            # Если текста нет, используем чекбоксы
            ingredients_list = request.POST.getlist('ingredients')
            selected_ingredients = [int(i) for i in ingredients_list if i.isdigit()]
    else:
        # GET запрос - берем из сессии
        selected_ingredients = request.session.get('selected_ingredients', [])
        selected_category = request.session.get('selected_category', '')
        ingredients_text = request.session.get('ingredients_text', '')

    # Убираем дубликаты и сохраняем в сессию
    selected_ingredients = list(set(selected_ingredients))
    request.session['selected_ingredients'] = selected_ingredients
    request.session['selected_category'] = selected_category
    request.session['ingredients_text'] = ingredients_text

    # Словарь с названиями категорий
    category_names = {
        'dessert': 'Десерт',
        'appetizer': 'Закуска',
        'first': 'Первые блюда',
        'second': 'Вторые блюда',
        'snack': 'Перекус',
        'drink': 'Напиток',
        'salad': 'Салат',
        'soup': 'Суп',
        'main': 'Основное блюдо',
        'baking': 'Выпечка',
    }

    # НОВАЯ ЛОГИКА: Если выбрана только категория (без ингредиентов)
    if selected_category and not selected_ingredients:
        print(f"🟡 Поиск только по категории: {selected_category}")

        # Получаем все рецепты из выбранной категории
        recipes = Article.objects.filter(
            category=selected_category
        ).prefetch_related('recipe_ingredients__ingredient')

        print(f"🟡 Найдено рецептов в категории: {recipes.count()}")

        # Подготавливаем результаты для отображения
        results = []
        for recipe in recipes:
            recipe_ingredients = recipe.recipe_ingredients.all()

            # Исправлено: собираем ингредиенты из recipe_ingredients
            ingredient_list = []
            for ri in recipe_ingredients:
                ingredient_list.append(ri.ingredient)  # Добавляем сам ингредиент, а не ri

            results.append({
                'recipe': recipe,
                'matches': 0,
                'total': len(recipe_ingredients),
                'missing': len(recipe_ingredients),
                'missing_ingredients': ingredient_list,
                'is_category_only': True
            })

        context = {
            'can_cook': [],
            'missing_one': [],
            'missing_two': [],
            'missing_three_plus': results,
            'selected_ingredients': selected_ingredients,
            'selected_count': len(selected_ingredients),
            'selected_category': selected_category,
            'ingredients_text': ingredients_text,
            'no_results': len(results) == 0,
            'has_suggestions': False,
            'is_category_only': True,
            'category_name': category_names.get(selected_category, selected_category),
        }
        return render(request, 'blog/fridge_results.html', context)
    # Если нет выбранных ингредиентов и нет категории - редирект
    if not selected_ingredients:
        return redirect('blog:fridge')

    print(f"🔵 Выбрано ингредиентов: {len(selected_ingredients)}, категория: {selected_category}")
    print(f"🔵 Текст ввода: {ingredients_text}")

    # ОПТИМИЗАЦИЯ 1: Фильтруем рецепты только по тем, что содержат выбранные ингредиенты
    recipes = Article.objects.filter(
        recipe_ingredients__ingredient__id__in=selected_ingredients
    ).distinct()

    # ОПТИМИЗАЦИЯ 2: Фильтрация по категории блюда
    if selected_category:
        recipes = recipes.filter(category=selected_category)

    # Загружаем связанные данные оптимизировано
    recipes = recipes.prefetch_related('recipe_ingredients__ingredient')

    print(f"🔵 После фильтрации осталось рецептов: {recipes.count()}")

    # ОПТИМИЗАЦИЯ 3: Загружаем все заменители один раз в память
    substitutions_qs = IngredientSubstitution.objects.select_related('replacement').all()
    substitutions_map = {}
    for sub in substitutions_qs:
        source_id = sub.source_id
        replacement_id = sub.replacement_id
        if source_id not in substitutions_map:
            substitutions_map[source_id] = []
        substitutions_map[source_id].append(replacement_id)

    results = []
    for recipe in recipes:
        recipe_ingredients = recipe.recipe_ingredients.all()
        recipe_ingredient_ids = [ri.ingredient.id for ri in recipe_ingredients]

        all_ingredient_ids = set(recipe_ingredient_ids)

        # Добавляем подстановки из памяти (без запросов к БД)
        for ri in recipe_ingredients:
            source_id = ri.ingredient.id
            substitutions = substitutions_map.get(source_id, [])
            all_ingredient_ids.update(substitutions)

        selected_set = set(selected_ingredients)
        matches = selected_set & all_ingredient_ids
        total_needed = len(recipe_ingredients)
        missing = total_needed - len(matches)

        # Показываем ВСЕ найденные рецепты, даже если не все ингредиенты совпадают
        if matches:
            results.append({
                'recipe': recipe,
                'matches': len(matches),
                'total': total_needed,
                'missing': missing,
                'missing_ingredients': get_missing_ingredients(
                    recipe_ingredients, selected_ingredients, substitutions_map
                )
            })

    # Если нет результатов, но были выбранные ингредиенты - покажем сообщение
    if not results:
        # Попробуем найти рецепты с ПОХОЖИМИ ингредиентами
        similar_ingredients = []
        for ing_id in selected_ingredients:
            try:
                ing = Ingredient.objects.get(id=ing_id)
                similar = Ingredient.objects.filter(
                    name__icontains=ing.name
                ).exclude(id=ing_id)[:5]
                similar_ingredients.extend(similar)
            except Ingredient.DoesNotExist:
                pass

        if similar_ingredients:
            similar_ids = [ing.id for ing in similar_ingredients]
            recipes_similar = Article.objects.filter(
                recipe_ingredients__ingredient__id__in=similar_ids
            ).distinct().prefetch_related('recipe_ingredients__ingredient')

            for recipe in recipes_similar:
                recipe_ingredients = recipe.recipe_ingredients.all()
                recipe_ingredient_ids = [ri.ingredient.id for ri in recipe_ingredients]

                all_ingredient_ids = set(recipe_ingredient_ids)
                for ri in recipe_ingredients:
                    source_id = ri.ingredient.id
                    substitutions = substitutions_map.get(source_id, [])
                    all_ingredient_ids.update(substitutions)

                selected_set = set(selected_ingredients)
                matches = selected_set & all_ingredient_ids
                total_needed = len(recipe_ingredients)
                missing = total_needed - len(matches)

                results.append({
                    'recipe': recipe,
                    'matches': len(matches),
                    'total': total_needed,
                    'missing': missing,
                    'missing_ingredients': get_missing_ingredients(
                        recipe_ingredients, selected_ingredients, substitutions_map
                    ),
                    'is_suggested': True
                })

    # Сортируем по количеству недостающих ингредиентов
    results.sort(key=lambda x: x['missing'])

    can_cook = [r for r in results if r['missing'] == 0]
    missing_one = [r for r in results if r['missing'] == 1]
    missing_two = [r for r in results if r['missing'] == 2]
    missing_three_plus = [r for r in results if r['missing'] >= 3]

    context = {
        'can_cook': can_cook,
        'missing_one': missing_one,
        'missing_two': missing_two,
        'missing_three_plus': missing_three_plus,
        'selected_ingredients': selected_ingredients,
        'selected_count': len(selected_ingredients),
        'selected_category': selected_category,
        'ingredients_text': ingredients_text,
        'no_results': len(results) == 0,
        'has_suggestions': any(r.get('is_suggested', False) for r in results),
        'is_category_only': False,
        'category_name': category_names.get(selected_category, ''),  # Добавили и сюда!
    }
    return render(request, 'blog/fridge_results.html', context)


def get_missing_ingredients(recipe_ingredients, selected_ingredients, substitutions_map=None):
    """Возвращает список недостающих ингредиентов (оптимизировано)"""
    missing = []
    selected_set = set(selected_ingredients)

    if substitutions_map is None:
        substitutions_qs = IngredientSubstitution.objects.select_related('replacement').all()
        substitutions_map = {}
        for sub in substitutions_qs:
            source_id = sub.source_id
            replacement_id = sub.replacement_id
            if source_id not in substitutions_map:
                substitutions_map[source_id] = []
            substitutions_map[source_id].append(replacement_id)

    for ri in recipe_ingredients:
        ingredient_id = ri.ingredient.id
        substitutions = substitutions_map.get(ingredient_id, [])

        if ingredient_id not in selected_set:
            has_substitution = any(sub in selected_set for sub in substitutions)
            if not has_substitution:
                missing.append(ri.ingredient)

    return missing

# ============ УМНЫЙ ХОЛОДИЛЬНИК - ПОИСК (JSON) ============
@login_required
def fridge_search_view(request):
    """
    Оптимизированный JSON-поиск.
    Фильтруем только релевантные рецепты и сортируем по количеству совпадений.
    """
    selected_ingredients = request.session.get('selected_ingredients', [])
    selected_category = request.GET.get('category') or request.session.get('selected_category', '')

    if not selected_ingredients:
        return JsonResponse({'recipes': []})

    # ОПТИМИЗАЦИЯ 1: Фильтруем рецепты по ингредиентам
    recipes = Article.objects.filter(
        recipe_ingredients__ingredient__id__in=selected_ingredients
    ).distinct()

    # ОПТИМИЗАЦИЯ 2: Фильтрация по категории блюда
    if selected_category:
        recipes = recipes.filter(category=selected_category)

    # Загружаем связанные данные
    recipes = recipes.prefetch_related('recipe_ingredients__ingredient')

    # ОПТИМИЗАЦИЯ 3: Загружаем все заменители один раз в память
    substitutions_qs = IngredientSubstitution.objects.select_related('replacement').all()
    substitutions_map = {}
    for sub in substitutions_qs:
        source_id = sub.source_id
        replacement_id = sub.replacement_id
        if source_id not in substitutions_map:
            substitutions_map[source_id] = []
        substitutions_map[source_id].append(replacement_id)

    results = []
    for recipe in recipes:
        recipe_ingredients = recipe.recipe_ingredients.all()
        recipe_ingredient_ids = [ri.ingredient.id for ri in recipe_ingredients]

        all_ingredient_ids = set(recipe_ingredient_ids)

        # Добавляем подстановки из памяти (без запросов к БД)
        for ri in recipe_ingredients:
            source_id = ri.ingredient.id
            substitutions = substitutions_map.get(source_id, [])
            all_ingredient_ids.update(substitutions)

        selected_set = set(selected_ingredients)
        matches = selected_set & all_ingredient_ids
        total_needed = len(recipe_ingredients)
        missing = total_needed - len(matches)

        if matches:
            results.append({
                'id': recipe.id,
                'title': recipe.title,
                'description': recipe.description[:150] + '...' if recipe.description else '',
                'image': recipe.image.url if recipe.image else '/static/images/default-recipe.jpg',
                'matches': len(matches),
                'total': total_needed,
                'missing': missing,
                'category': recipe.get_category_display(),
            })

    # Сортируем по количеству совпадений
    results.sort(key=lambda x: x['matches'], reverse=True)

    return JsonResponse({'recipes': results})


@login_required
def fridge_save_view(request):
    """Сохранить выбранные ингредиенты в сессию (JSON)"""
    import json
    data = json.loads(request.body)
    ingredients = data.get('ingredients', [])
    request.session['selected_ingredients'] = ingredients
    return JsonResponse({'success': True})


# ============ ИЗБРАННОЕ ============
@login_required
def favorite_view(request, recipe_id):
    """Добавление/удаление рецепта из избранного (JSON)"""
    article = get_object_or_404(Article, pk=recipe_id)

    favorite, created = FavoriteRecipe.objects.get_or_create(
        user=request.user,
        recipe=article
    )

    if not created:
        favorite.delete()
        is_favorited = False
    else:
        is_favorited = True

    likes_count = article.favored_by.count()

    return JsonResponse({
        'success': True,
        'is_favorited': is_favorited,
        'likes_count': likes_count,
    })


@login_required
def favorites_view(request):
    favorite_recipes = FavoriteRecipe.objects.filter(
        user=request.user
    ).select_related('recipe').order_by('-id')

    context = {
        'favorite_recipes': favorite_recipes,
    }
    return render(request, 'blog/favorites.html', context)