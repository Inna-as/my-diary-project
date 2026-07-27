from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'blog'

urlpatterns = [
    # Главная страница
    path('', views.index_view, name='index'),

    # Страница статьи
    path('article/<int:pk>/', views.article_detail_view, name='article_detail'),

    # Создание новой статьи
    path('article/new/', views.article_create_view, name='article_create'),

    # Редактирование статьи
    path('article/<int:pk>/edit/', views.article_update_view, name='article_update'),

    # Удаление статьи
    path('article/<int:pk>/delete/', views.article_delete_view, name='article_delete'),

    # Страница профиля автора (по имени пользователя)
    path('author/<str:username>/', views.author_profile_view, name='author_profile'),

    # Войти и выйти из аккаунта
    path('login/', LoginView.as_view(template_name='blog/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Регистрация и профиль
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
]

# Обслуживание медиафайлов в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)