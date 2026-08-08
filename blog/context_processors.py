from django.conf import settings
from django.utils import timezone

def branding_context(request):

   # Добавляет брендинг проекта во все шаблоны.

    return {
        'PROJECT_NAME': getattr(settings, 'PROJECT_NAME', 'Еда на любой вкус'),
        'PROJECT_SLUG': getattr(settings, 'PROJECT_SLUG', ''),
        'PROJECT_SLOGAN': getattr(settings, 'PROJECT_SLOGAN', ''),
    }

def greeting_context(request):

    current_time = timezone.localtime(timezone.now())  # локальное время
    hour = current_time.hour

    if 5 <= hour < 12:
        greeting = 'Доброе утро!'
    elif 12 <= hour < 17:
        greeting = 'Добрый день!'
    elif 17 <= hour < 23:
        greeting = 'Добрый вечер!'
    else:
        greeting = 'Доброй ночи!'

    return {
        'GREETING': greeting,
    }

def breadcrumbs(request):
    """Автоматически определяет хлебные крошки на основе URL."""

    crumbs = [
        {'title': 'Главная', 'url': '/'},
    ]

    # Пытаемся определить текущий маршрут
    try:
        from django.urls import resolve, reverse
        match = resolve(request.path_info)
        view_name = match.view_name
        kwargs = match.kwargs
    except:
        view_name = None
        kwargs = {}

    if view_name:
        # Главная
        if view_name == 'blog:index':
            pass  # оставляем только "Главная"

        # Детальная страница рецепта
        elif view_name == 'blog:article_detail':
            crumbs.append({'title': 'Каталог рецептов', 'url': reverse('blog:index')})
            # Название рецепта из request.breadcrumb_title (задаётся в views.py)
            title = getattr(request, 'breadcrumb_title', None) or 'Рецепт'
            crumbs.append({'title': title, 'url': None})

        # Добавить рецепт
        elif view_name == 'blog:article_create':
            crumbs.append({'title': 'Каталог рецептов', 'url': reverse('blog:index')})
            crumbs.append({'title': 'Добавить рецепт', 'url': None})

        # Редактировать рецепт
        elif view_name == 'blog:article_update':
            crumbs.append({'title': 'Каталог рецептов', 'url': reverse('blog:index')})
            crumbs.append({'title': 'Редактирование', 'url': None})

        # Удаление рецепта
        elif view_name == 'blog:article_delete':
            crumbs.append({'title': 'Каталог рецептов', 'url': reverse('blog:index')})
            crumbs.append({'title': 'Удаление', 'url': None})

        # Профиль
        elif view_name == 'blog:profile':
            crumbs.append({'title': 'Профиль', 'url': None})

        # Профиль автора
        elif view_name == 'blog:author_profile':
            crumbs.append({'title': 'Профиль автора', 'url': None})

        # Избранное
        elif view_name == 'blog:favorites':
            crumbs.append({'title': 'Избранное', 'url': None})

        # Холодильник
        elif view_name == 'blog:fridge':
            crumbs.append({'title': 'Холодильник', 'url': None})

        # Результаты холодильника
        elif view_name == 'blog:fridge_results':
            crumbs.append({'title': 'Холодильник', 'url': reverse('blog:fridge')})
            crumbs.append({'title': 'Результаты', 'url': None})

        # Модерация
        elif view_name == 'blog:moderate':
            crumbs.append({'title': 'Модерация', 'url': None})

        # Вход
        elif view_name == 'login':
            crumbs.append({'title': 'Вход', 'url': None})

        # Регистрация
        elif view_name in ('register', 'blog:register'):
            crumbs.append({'title': 'Регистрация', 'url': None})

    return {'breadcrumbs': crumbs}