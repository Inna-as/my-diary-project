from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# 1. Таблица для тегов
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название тега")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"


# 2. Таблица для рецептов (статей блога)
class Article(models.Model):
    # Заголовок статьи — короткая строка
    title = models.CharField(max_length=200, verbose_name="Заголовок статьи")
    # Основной текст статьи
    content = models.TextField(verbose_name="Текст статьи")
    # Связь "один ко многим" (автор)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Автор")
    # Связь "многие ко многим" с тегами
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Теги")
    # Время создания
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    # Статус публикации
    is_published = models.BooleanField("Одобрено админом", default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ['-created_at']


# 3. Таблица комментариев
class Comment(models.Model):
    # Связь с рецептом/статьей
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments', verbose_name="Статья")
    # Связь с автором комментария
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Автор")
    # Текст комментария
    content = models.TextField(verbose_name="Текст комментария")
    # Время написания
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата написания")
    # Вложенные комментарии (цепочка)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies', verbose_name="Родительский комментарий")

    def __str__(self):
        return f"Комментарий от {self.author.username} к статье {self.article.title}"

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['created_at']


# Пользовательская модель
class CustomUser(AbstractUser):
    # Биография
    bio = models.TextField("О себе", blank=True)
    # Аватарка профиля
    avatar = models.ImageField("Фотография профиля", upload_to="avatars/", blank=True, null=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"