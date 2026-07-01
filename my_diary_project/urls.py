from django.contrib import admin
from django.urls import path, include  # Импортируем include, чтобы подключить ссылки приложения

urlpatterns = [
    # Адрес для админки
    path('admin/', admin.site.urls),

    # Подключаем файл ссылок из нашего приложения "blog" ко всему сайту.
    path('', include('blog.urls')),
]
