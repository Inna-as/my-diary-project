import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Django берет ключ и режим отладки из скрытого файла .env
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG') == 'True'

ALLOWED_HOSTS = []

# ==================== РЕГИСТРАЦИЯ ПРИЛОЖЕНИЙ ====================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_bootstrap5',
    'blog',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'blog.middleware.SimplePerformanceMiddleware',
]

ROOT_URLCONF = 'my_diary_project.urls'

# ==================== НАСТРОЙКА ШАБЛОНОВ ====================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'my_diary_project.wsgi.application'

# ==================== НАСТРОЙКА БАЗЫ ДАННЫХ ====================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'my_culinary_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'root'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# ==================== ВАЛИДАЦИЯ ПАРОЛЕЙ ====================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==================== ЯЗЫКОВЫЕ НАСТРОЙКИ ====================

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# ==================== СТАТИЧЕСКИЕ ФАЙЛЫ ====================

# URL-префикс для статических файлов
STATIC_URL = '/static/'

# Где Django ищет статические файлы внутри проекта
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Куда Django соберет статические файлы для продакшена
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ==================== МЕДИА ФАЙЛЫ ====================

# URL-префикс для медиафайлов
MEDIA_URL = '/media/'

# Где хранить загруженные медиафайлы
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== НАСТРОЙКА КЕШИРОВАНИЯ ====================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# ==================== НАСТРОЙКИ АВТОРИЗАЦИИ ====================

LOGIN_REDIRECT_URL = 'blog:index'
LOGOUT_REDIRECT_URL = 'blog:index'
AUTH_USER_MODEL = 'blog.CustomUser'