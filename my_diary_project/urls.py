from django.contrib import admin
from django.urls import path, include  # Импортируем include, чтобы подключить ссылки приложения
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Адрес для админки
    path('admin/', admin.site.urls),

    # Подключаем файл ссылок из нашего приложения "blog" ко всему сайту.
    path('', include('blog.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

