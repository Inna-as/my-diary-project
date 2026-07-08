from django.db import models
# Импортируем готовую таблицу пользователей Django (User).
from django.contrib.auth.models import User


# 1. ТАБЛИЦА ДЛЯ ТЕГОВ
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название тега")

    def __str__(self):
        return self.name


# 2. ТАБЛИЦА ДЛЯ СТАТЕЙ БЛОГА
class Article(models.Model):
    # Заголовок статьи — короткая строка
    title = models.CharField(max_length=200, verbose_name="Заголовок статьи")
    # Текстовое поле для огромных текстов
    content = models.TextField(verbose_name="Текст статьи")

    # Связь "Один ко многим".
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор", related_name='articles')


    # Связь "Многие ко многим".
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Теги")

    # Само сохраняет точную дату и время создания статьи
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")

    def __str__(self):
        return self.title


# 3. Таблица коминтариев
class Comment(models.Model):
    # Привязываем комментарий к определенной статье
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments', verbose_name="Статья")
    # Привязываем к пользователю, который пишет этот комментарий
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')

    content = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата написания")

    # Древовидность-позволяет комментарию ссылаться на другой комментарий в этой же таблице,
    # за счет чего и создается цепочка «вопрос — ответ» любой вложенности.

    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies',
                               verbose_name="Родительский комментарий")

    def __str__(self):
        return f"Комментарий от {self.author.username} к статье {self.article.title}"
