from django.urls import path
# Импортируем готовые окна авторизации из самого Django
from django.contrib.auth.views import LoginView, LogoutView
from . import views

app_name = 'blog'

urlpatterns = [
    # Главная страница
    path('', views.index_view, name='index'),

    # Страница статьи
    path('article/<int:pk>/', views.article_detail_view, name='article_detail'),
    #  Путь для создания статьи
    path('article/new/', views.article_create_view, name='article_create'),
#  Ссылки на редактирование и удаление
    path('article/<int:pk>/edit/', views.article_update_view, name='article_update'),
    path('article/<int:pk>/delete/', views.article_delete_view, name='article_delete'),
    #  Ссылка на профиль автора (принимает имя пользователя)
    path('author/<str:username>/', views.author_profile_view, name='author_profile'),

    #   адреса для входа и выхода на сайт
    path('login/', LoginView.as_view(template_name='blog/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),
]
