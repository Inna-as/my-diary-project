from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView, LoginView

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),

    # Вход и выход

    path('login/', LoginView.as_view(template_name='blog/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

    # Все URL приложения blog
    path('', include('blog.urls')),
]

# ==================== СТАТИЧЕСКИЕ И МЕДИА ФАЙЛЫ ====================

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)