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