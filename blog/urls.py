from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'blog'

urlpatterns = [
    # Главная страница
    path('', views.index_view, name='index'),

    # Страница статьи/рецепта
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

    # ==================== УМНЫЙ ХОЛОДИЛЬНИК ====================

    # Главная страница "Умный Холодильник"
    path('fridge/', views.fridge_view, name='fridge'),

    # Результаты поиска (сессия)
    path('fridge/results/', views.fridge_results_view, name='fridge_results'),

    # Поиск рецептов (JSON - AJAX)
    path('fridge/search/', views.fridge_search_view, name='fridge_search'),

    # ==================== ИЗБРАННОЕ ====================

    # Добавление/удаление рецепта из избранного (JSON - AJAX)
    path('favorite/<int:recipe_id>/', views.favorite_view, name='favorite'),

    # Список всех избранных рецептов пользователя
    path('favorites/', views.favorites_view, name='favorites'),
    # AJAX - сохранить выбранные ингредиенты
    path('fridge/save/', views.fridge_save_view, name='fridge_save'),
]

# Обслуживание медиафайлов в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)