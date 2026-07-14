from django.contrib import admin
from .models import Article, Tag, Comment, CustomUser

# Настройка главного заголовка панели управления в браузере
admin.site.site_header = "Панель управления кулинарным блогом"
admin.site.index_title = "Каталог рецептов и модерация"


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):

    list_display = ('title', 'author', 'created_at', 'is_published')

    list_editable = ('is_published',)

    search_fields = ('title', 'content', 'author__username')

    list_filter = ('created_at', 'is_published')

    actions = ['approve_recipes']

    @admin.action(description="🔥 Одобрить и опубликовать выбранные рецепты")
    def approve_recipes(self, request, queryset):
        updated_count = queryset.update(is_published=True)
        self.message_user(request, f"Успешно одобрено и отправлено на сайт рецептов: {updated_count}.")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'article', 'created_at')
    search_fields = ('content', 'author__username')
    list_filter = ('created_at',)
# Принудительная русификация названий таблиц в интерфейсе
Article._meta.verbose_name = "Рецепт"
Article._meta.verbose_name_plural = "Рецепты"
Comment._meta.verbose_name = "Комментарий"
Comment._meta.verbose_name_plural = "Комментарии"
Tag._meta.verbose_name = "Категория рецепта"
Tag._meta.verbose_name_plural = "Категории рецептов"

from django.contrib.auth.admin import UserAdmin

# Профессиональная регистрация кастомного пользователя для диплома
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Добавляем отображение наших полей "О себе" и "Аватарка" в админку
    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительно для профиля", {"fields": ("bio", "avatar")}),
    )

