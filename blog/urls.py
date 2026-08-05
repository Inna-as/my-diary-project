from django.urls import path
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

    # Регистрация и профиль
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),

    # ==================== УМНЫЙ ХОЛОДИЛЬНИК ====================
    path('fridge/', views.fridge_view, name='fridge'),
    path('fridge/results/', views.fridge_results_view, name='fridge_results'),
    path('fridge/search/', views.fridge_search_view, name='fridge_search'),
    path('fridge/save/', views.fridge_save_view, name='fridge_save'),

    # ==================== ИЗБРАННОЕ ====================
    path('favorite/<int:recipe_id>/', views.favorite_view, name='favorite'),
    path('favorites/', views.favorites_view, name='favorites'),

    # ==================== МОДЕРАЦИЯ КОММЕНТАРИЕВ ====================
    path('moderate/', views.moderate_view, name='moderate'),
    path('moderate/approve/<int:comment_id>/', views.moderate_approve_view, name='moderate_approve'),
    path('moderate/<int:comment_id>/delete/', views.moderate_delete_view, name='moderate_delete'),
    path('moderate/count/', views.moderate_count_view, name='moderate_count'),
    path('comment/<int:comment_id>/report/', views.comment_report_view, name='comment_report'),
    path('moderate/approve-all/', views.moderate_approve_all_view, name='moderate_approve_all'),
    path('reports/<int:report_id>/dismiss/', views.report_dismiss_view, name='report_dismiss'),
]

# Обслуживание медиафайлов в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)