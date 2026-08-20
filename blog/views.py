import threading
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
import re

from .models import (
    Article, FoodCategory, Ingredient, RecipeIngredient,
    FavoriteRecipe, CustomUser, Comment, CommentReport
)
from .forms import CustomUserCreationForm, UserProfileForm, ArticleForm

# ═══════════════════════════════════════════════════════
#  АВТОМАТИЧЕСКАЯ МОДЕРАЦИЯ КОММЕНТАРИЕВ
# ═══════════════════════════════════════════════════════

SPAM_WORDS = [
    'купить', 'заработок', 'заработать', 'кредит',
    'ставка', 'казино', 'бесплатный сыр', 'миллион',
    'подпишись', 'подписывайся', 'розыгрыш', 'акция',
]

BAD_WORDS = [
    'дурак', 'идиот', 'дебил', 'тупой',
]

MAX_LINKS_FOR_NEWBIE = 2
TRUST_THRESHOLD = 5
NEWBIE_THRESHOLD = 3


def auto_moderate_comment(text, user):

    text_lower = text.lower()
    spam_hits = sum(1 for word in SPAM_WORDS if word in text_lower)
    links_count = len(re.findall(r'https?://', text_lower))

    approved_count = Comment.objects.filter(
        author=user, is_approved=True
    ).count()
    is_trusted = approved_count >= TRUST_THRESHOLD

    if links_count > MAX_LINKS_FOR_NEWBIE:
        return 'blocked'
    if spam_hits >= 3:
        return 'blocked'
    if is_trusted and spam_hits == 0 and links_count <= 1:
        return 'approved'
    if spam_hits > 0:
        return 'visible_pending'
    if approved_count < NEWBIE_THRESHOLD:
        return 'visible_pending'
    return 'approved'


def _get_pending_count(user):

    if not user.is_authenticated:
        return 0
    if user.is_staff or user.is_superuser:
        return Comment.objects.filter(is_approved=True, auto_approved=False).count()
    return Comment.objects.filter(
        is_approved=True, auto_approved=False, article__author=user
    ).count()


# ============ ГЛАВНАЯ ============
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

    paginator = Paginator(articles_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    recipe_of_day = None
    published_recipes = Article.objects.filter(is_published=True).order_by('id')
    if published_recipes.exists():
        today = timezone.now().date()
        index = today.toordinal() % published_recipes.count()
        recipe_of_day = published_recipes[index]

    context = {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by,
        'recipe_of_day': recipe_of_day,
        'pending_count': _get_pending_count(request.user),
    }
    return render(request, 'blog/index.html', context)


# ============ ДЕТАЛЬНАЯ СТРАНИЦА ============
def article_detail_view(request, pk):
    article = get_object_or_404(
        Article.objects.annotate(comments_count=Count('comments')),
        pk=pk
    )
    recipe_ingredients = article.recipe_ingredients.select_related(
        'ingredient', 'ingredient__category'
    ).all()
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
            user=request.user, recipe=article
        ).exists()

    can_edit = False
    if request.user.is_authenticated:
        can_edit = (request.user == article.author) or request.user.is_superuser

    # ─── ФИЛЬТРАЦИЯ КОММЕНТАРИЕВ ───
    comments = article.comments.filter(is_approved=True).select_related(
        'author', 'parent'
    ).prefetch_related('replies__author').order_by('-created_at')

    # ─── СОЗДАНИЕ КОММЕНТАРИЯ ───
    if request.method == 'POST' and 'comment_text' in request.POST:
        if request.user.is_authenticated:
            comment_text = request.POST.get('comment_text', '').strip()
            parent_id = request.POST.get('parent_id', '').strip()

            if comment_text:
                parent_comment = None
                if parent_id:
                    try:
                        parent_comment = Comment.objects.get(id=parent_id)
                    except Comment.DoesNotExist:
                        pass

                verdict = auto_moderate_comment(comment_text, request.user)

                if verdict == 'blocked':
                    Comment.objects.create(
                        article=article, author=request.user,
                        text=comment_text, parent=parent_comment,
                        is_spam=True, is_approved=False,
                    )
                    messages.warning(request, '⚠️ Комментарий не опубликован — похож на спам.')
                elif verdict == 'approved':
                    Comment.objects.create(
                        article=article, author=request.user,
                        text=comment_text, parent=parent_comment,
                        is_approved=True, auto_approved=True,
                    )
                else:  # visible_pending
                    Comment.objects.create(
                        article=article, author=request.user,
                        text=comment_text, parent=parent_comment,
                        is_approved=True,
                        auto_approved=False,
                    )
                    messages.info(request, '✅ Комментарий опубликован. Модератор проверит его позже.')

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
        'pending_count': _get_pending_count(request.user),
        'breadcrumb_title': article.title,
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

# ============ СОЗДАНИЕ / РЕДАКТИРОВАНИЕ / УДАЛЕНИЕ ============

@login_required
def article_create_view(request):
    ingredients_qs = Ingredient.objects.all().order_by('name')

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()

            # ─── Сохраняем ингредиенты ───
            i = 0
            while f'ingredient_name_{i}' in request.POST:
                name = request.POST.get(f'ingredient_name_{i}', '').strip()
                ing_id = request.POST.get(f'ingredient_id_{i}', '').strip()
                amount = request.POST.get(f'amount_{i}', '').strip()
                unit = request.POST.get(f'unit_{i}', '').strip()

                if name and amount and unit:
                    # Если ID передан и ингредиент существует — используем его
                    if ing_id and Ingredient.objects.filter(id=int(ing_id)).exists():
                        ingredient = Ingredient.objects.get(id=int(ing_id))
                    else:
                        # Ищем по имени
                        ingredient = Ingredient.objects.filter(name__iexact=name).first()
                        if not ingredient:
                            # Создаём новый ингредиент
                            other_cat, _ = FoodCategory.objects.get_or_create(
                                name='Прочее',
                                defaults={'name': 'Прочее'}
                            )
                            ingredient = Ingredient.objects.create(
                                name=name,
                                category=other_cat
                            )

                    RecipeIngredient.objects.create(
                        recipe=article,
                        ingredient=ingredient,
                        amount=float(amount),
                        unit=unit,
                    )
                i += 1
            return redirect('blog:article_detail', pk=article.pk)
    else:
        form = ArticleForm()

    return render(request, 'blog/article_form.html', {
        'form': form,
        'ingredients': ingredients_qs,
        'pending_count': _get_pending_count(request.user),
    })


@login_required
def article_update_view(request, pk):
    article = get_object_or_404(Article, pk=pk)
    ingredients_qs = Ingredient.objects.all().order_by('name')

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            article = form.save()

            # ─── Удаляем старые ингредиенты и создаём новые ───
            article.recipe_ingredients.all().delete()
            i = 0
            while f'ingredient_name_{i}' in request.POST:
                name = request.POST.get(f'ingredient_name_{i}', '').strip()
                ing_id = request.POST.get(f'ingredient_id_{i}', '').strip()
                amount = request.POST.get(f'amount_{i}', '').strip()
                unit = request.POST.get(f'unit_{i}', '').strip()

                if name and amount and unit:
                    # Если ID передан и ингредиент существует — используем его
                    if ing_id and Ingredient.objects.filter(id=int(ing_id)).exists():
                        ingredient = Ingredient.objects.get(id=int(ing_id))
                    else:
                        # Ищем по имени
                        ingredient = Ingredient.objects.filter(name__iexact=name).first()
                        if not ingredient:
                            # Создаём новый ингредиент
                            other_cat, _ = FoodCategory.objects.get_or_create(
                                name='Прочее',
                                defaults={'name': 'Прочее'}
                            )
                            ingredient = Ingredient.objects.create(
                                name=name,
                                category=other_cat
                            )

                    RecipeIngredient.objects.create(
                        recipe=article,
                        ingredient=ingredient,
                        amount=float(amount),
                        unit=unit,
                    )
                i += 1

            return redirect('blog:article_detail', pk=article.pk)
    else:
        form = ArticleForm(instance=article)

    return render(request, 'blog/article_form.html', {
        'form': form,
        'ingredients': ingredients_qs,
        'pending_count': _get_pending_count(request.user),
    })

@login_required
def article_delete_view(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        article.delete()
        return redirect('blog:index')
    return render(request, 'blog/article_confirm_delete.html', {
        'article': article,
        'pending_count': _get_pending_count(request.user),
    })


# ============ ПРОФИЛИ ============
def author_profile_view(request, username):
    author = get_object_or_404(CustomUser, username=username)
    total_articles = author.article_set.count()

    # ❤️ Сумма всех лайков на рецептах автора
    total_likes = 0
    for article in author.article_set.all():
        total_likes += article.favored_by.count()

    # 💬 Количество комментариев под рецептами автора
    total_comments_on_recipes = Comment.objects.filter(article__author=author).count()

    # ⭐ Рейтинг автора (формула простая)
    rating = total_likes + total_articles * 2 + total_comments_on_recipes

    # Определяем уровень
    if rating >= 100:
        level = '🥇 Мастер-шеф'
    elif rating >= 50:
        level = '🥈 Опытный кулинар'
    elif rating >= 20:
        level = '🥉 Домашний повар'
    elif rating >= 5:
        level = '👨‍🍳 Новичок'
    else:
        level = '🌱 Начинающий'

    author_articles_list = author.article_set.all().order_by('-created_at')
    paginator = Paginator(author_articles_list, 12)
    page_number = request.GET.get('page')
    author_articles = paginator.get_page(page_number)

    return render(request, 'blog/author_profile.html', {
        'author': author,
        'total_articles': total_articles,
        'total_likes': total_likes,
        'total_comments_on_recipes': total_comments_on_recipes,
        'rating': rating,
        'level': level,
        'author_articles': author_articles,
        'pending_count': _get_pending_count(request.user),
    })


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
        'pending_count': _get_pending_count(request.user),
    }
    return render(request, 'blog/profile.html', context)


# ============ ХОЛОДИЛЬНИК ============
@login_required
def fridge_view(request):
    categories = FoodCategory.objects.prefetch_related('ingredients').all()
    return render(request, 'blog/fridge.html', {
        'categories': categories,
        'pending_count': _get_pending_count(request.user),
    })


def get_missing_ingredients(recipe_ingredients, selected_ingredients):
    missing = []
    selected_set = set(selected_ingredients)
    for ri in recipe_ingredients:
        if ri.ingredient.id not in selected_set:
            missing.append(ri.ingredient)
    return missing


@login_required
def fridge_results_view(request):
    selected_category = (request.POST.get('category') or
                         request.GET.get('category') or '')

    selected_ingredients = []
    ingredients_text = ''

    if request.method == 'POST':
        ingredients_text = request.POST.get('ingredients_text', '').strip()
        if ingredients_text:
            ingredient_names = [name.strip() for name in ingredients_text.split(',') if name.strip()]
            for name in ingredient_names:
                matching_ingredients = Ingredient.objects.filter(name__icontains=name)
                selected_ingredients.extend([ing.id for ing in matching_ingredients])
        else:
            ingredients_list = request.POST.getlist('ingredients')
            selected_ingredients = [int(i) for i in ingredients_list if i.isdigit()]
    else:
        selected_ingredients = request.session.get('selected_ingredients', [])
        selected_category = request.session.get('selected_category', '')
        ingredients_text = request.session.get('ingredients_text', '')

    selected_ingredients = list(set(selected_ingredients))
    request.session['selected_ingredients'] = selected_ingredients
    request.session['selected_category'] = selected_category
    request.session['ingredients_text'] = ingredients_text

    category_names = {
        'dessert': 'Десерт', 'appetizer': 'Закуска', 'first': 'Первые блюда',
        'second': 'Вторые блюда', 'snack': 'Перекус', 'drink': 'Напиток',
        'salad': 'Салат', 'soup': 'Суп', 'main': 'Основное блюдо', 'baking': 'Выпечка',
    }

    if selected_category and not selected_ingredients:
        recipes = Article.objects.filter(
            category=selected_category
        ).prefetch_related('recipe_ingredients__ingredient')

        results = []
        for recipe in recipes:
            recipe_ingredients = recipe.recipe_ingredients.all()
            ingredient_list = [ri.ingredient for ri in recipe_ingredients]
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
            'pending_count': _get_pending_count(request.user),
        }
        return render(request, 'blog/fridge_results.html', context)

    if not selected_ingredients:
        return redirect('blog:fridge')

    recipes = Article.objects.filter(
        recipe_ingredients__ingredient__id__in=selected_ingredients
    ).distinct()

    if selected_category:
        recipes = recipes.filter(category=selected_category)

    recipes = recipes.prefetch_related('recipe_ingredients__ingredient')

    results = []
    selected_set = set(selected_ingredients)

    for recipe in recipes:
        recipe_ingredients = recipe.recipe_ingredients.all()
        recipe_ingredient_ids = set(ri.ingredient.id for ri in recipe_ingredients)
        total_needed = len(recipe_ingredients)
        matches = selected_set & recipe_ingredient_ids
        missing = total_needed - len(matches)
        if matches:
            results.append({
                'recipe': recipe,
                'matches': len(matches),
                'total': total_needed,
                'missing': missing,
                'missing_ingredients': get_missing_ingredients(
                    recipe_ingredients, selected_ingredients
                )
            })

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
        'has_suggestions': False,
        'is_category_only': False,
        'category_name': category_names.get(selected_category, ''),
        'pending_count': _get_pending_count(request.user),
    }
    return render(request, 'blog/fridge_results.html', context)


@login_required
def fridge_search_view(request):
    selected_ingredients = request.session.get('selected_ingredients', [])
    selected_category = request.GET.get('category') or request.session.get('selected_category', '')
    if not selected_ingredients:
        return JsonResponse({'recipes': []})

    recipes = Article.objects.filter(
        recipe_ingredients__ingredient__id__in=selected_ingredients
    ).distinct()

    if selected_category:
        recipes = recipes.filter(category=selected_category)
    recipes = recipes.prefetch_related('recipe_ingredients__ingredient')

    results = []
    selected_set = set(selected_ingredients)
    for recipe in recipes:
        recipe_ingredients = recipe.recipe_ingredients.all()
        recipe_ingredient_ids = set(ri.ingredient.id for ri in recipe_ingredients)
        total_needed = len(recipe_ingredients)
        matches = selected_set & recipe_ingredient_ids
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

    results.sort(key=lambda x: x['matches'], reverse=True)
    return JsonResponse({'recipes': results})


@login_required
def fridge_save_view(request):
    import json
    data = json.loads(request.body)
    ingredients = data.get('ingredients', [])
    request.session['selected_ingredients'] = ingredients
    return JsonResponse({'success': True})


# ============ ИЗБРАННОЕ ============
@login_required
def favorite_view(request, recipe_id):
    article = get_object_or_404(Article, pk=recipe_id)
    favorite, created = FavoriteRecipe.objects.get_or_create(
        user=request.user, recipe=article
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
        'pending_count': _get_pending_count(request.user),
    }
    return render(request, 'blog/favorites.html', context)


# ═══════════════════════════════════════════════════════
#  МОДЕРАЦИЯ
# ═══════════════════════════════════════════════════════

@login_required
def moderate_view(request):
    """Очередь комментариев на модерации + жалобы."""
    user = request.user

    # ─── КОММЕНТАРИИ, ТРЕБУЮЩИЕ ПРОВЕРКИ ───
    if user.is_staff or user.is_superuser:
        pending = Comment.objects.filter(
            is_approved=True, auto_approved=False,
        ).select_related('article', 'author').order_by('-created_at')
    else:
        pending = Comment.objects.filter(
            is_approved=True, auto_approved=False,
            article__author=user,
        ).select_related('article', 'author').order_by('-created_at')

    # ─── ЖАЛОБЫ ───
    reports = None
    if user.is_staff or user.is_superuser:
        reports = CommentReport.objects.select_related(
            'comment', 'comment__article', 'comment__author', 'reporter'
        ).order_by('-created_at')

    tab = request.GET.get('tab', 'pending')

    context = {
        'pending_comments': pending,         # ← вернул как было в шаблоне
        'pending_count': pending.count(),
        'reports': reports,
        'tab': tab,
    }
    return render(request, 'blog/moderate.html', context)


# ═══════════════════════════════════════════════════════
#  AJAX: ОДОБРИТЬ КОММЕНТАРИЙ
# ═══════════════════════════════════════════════════════

@login_required
def moderate_approve_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if not (
        request.user.is_staff
        or request.user.is_superuser
        or request.user == comment.article.author
    ):
        return JsonResponse({'success': False, 'error': 'Нет прав'}, status=403)

    comment.auto_approved = True
    comment.save()

    return JsonResponse({'success': True})


# ═══════════════════════════════════════════════════════
#  AJAX: ОДОБРИТЬ ВСЕ
# ═══════════════════════════════════════════════════════

@login_required
def moderate_approve_all_view(request):

    user = request.user
    if not (user.is_staff or user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Только для модераторов'}, status=403)

    updated = Comment.objects.filter(is_approved=True, auto_approved=False).update(
        auto_approved=True
    )
    return JsonResponse({'success': True, 'approved_count': updated})


# ═══════════════════════════════════════════════════════
#  AJAX: УДАЛИТЬ КОММЕНТАРИЙ
# ═══════════════════════════════════════════════════════

@login_required
def moderate_delete_view(request, comment_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Нет прав'}, status=403)
    comment = get_object_or_404(Comment, id=comment_id)
    comment.delete()
    return JsonResponse({'success': True})


# ═══════════════════════════════════════════════════════
#  AJAX: ПОЖАЛОВАТЬСЯ
# ═══════════════════════════════════════════════════════

@login_required
def comment_report_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author == request.user:
        return JsonResponse(
            {'success': False, 'error': 'Нельзя жаловаться на свой комментарий'},
            status=400
        )
    if CommentReport.objects.filter(comment=comment, reporter=request.user).exists():
        return JsonResponse(
            {'success': False, 'error': 'Вы уже жаловались на этот комментарий'},
            status=400
        )
    reason = request.POST.get('reason', 'spam')
    CommentReport.objects.create(
        comment=comment, reporter=request.user, reason=reason,
    )
    comment.report_count += 1
    comment.save()
    if comment.report_count >= 3:
        comment.is_approved = False
        comment.save()
    return JsonResponse({'success': True, 'report_count': comment.report_count})


# ═══════════════════════════════════════════════════════
#  AJAX: СЧЁТЧИК ДЛЯ БЕЙДЖА
# ═══════════════════════════════════════════════════════

@login_required
def moderate_count_view(request):
    user = request.user
    if user.is_staff or user.is_superuser:
        count = Comment.objects.filter(is_approved=True, auto_approved=False).count()
    else:
        count = Comment.objects.filter(
            is_approved=True, auto_approved=False,
            article__author=user,
        ).count()
    return JsonResponse({'count': count})


# ═══════════════════════════════════════════════════════
#  AJAX: ОТКЛОНИТЬ ЖАЛОБУ
# ═══════════════════════════════════════════════════════

@login_required
def report_dismiss_view(request, report_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Нет прав'}, status=403)
    report = get_object_or_404(CommentReport, id=report_id)
    report.delete()
    return JsonResponse({'success': True})
# ═══════════════════════════════════════════════════════
#  AJAX: ДОБАВИТЬ КОММЕНТАРИЙ (без перезагрузки)
# ═══════════════════════════════════════════════════════

@login_required
def add_comment_ajax_view(request, article_id):

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Только POST'}, status=405)

    article = get_object_or_404(Article, pk=article_id)
    comment_text = request.POST.get('text', '').strip()
    parent_id = request.POST.get('parent_id', '').strip()

    if not comment_text:
        return JsonResponse({'success': False, 'error': 'Пустой комментарий'}, status=400)

    parent_comment = None
    if parent_id:
        try:
            parent_comment = Comment.objects.get(id=parent_id)
        except Comment.DoesNotExist:
            pass

    verdict = auto_moderate_comment(comment_text, request.user)

    if verdict == 'blocked':
        return JsonResponse({
            'success': False,
            'error': 'Комментарий похож на спам и не был опубликован.',
            'blocked': True,
        })

    is_approved = verdict in ('approved', 'visible_pending')
    auto_approved = verdict == 'approved'

    comment = Comment.objects.create(
        article=article,
        author=request.user,
        text=comment_text,
        parent=parent_comment,
        is_approved=is_approved,
        auto_approved=auto_approved,
    )

    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'text': comment.text,
            'author': comment.author.username,
            'author_avatar': comment.author.avatar.url if comment.author.avatar else None,
            'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M'),
            'is_pending': not auto_approved,
            'parent_id': comment.parent.id if comment.parent else None,
        }
    })