from django.contrib import admin
# Импортируем наши модели из файла models.py текущей папки
from .models import Tag, Article, Comment

# Регистрируем каждую модель в админ-панели Django
admin.site.register(Tag)
admin.site.register(Article)
admin.site.register(Comment)
