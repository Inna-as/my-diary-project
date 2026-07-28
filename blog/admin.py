from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, FoodCategory, Ingredient, Article,
    RecipeIngredient, IngredientSubstitution, FavoriteRecipe, Comment
)

# Настройка главного заголовка панели управления в браузере
admin.site.site_header = "Панель управления - Умный Холодильник"
admin.site.index_title = "Кулинарная база данных"


# ============ РЕГИСТРАЦИЯ НОВЫХ МОДЕЛЕЙ ============

@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'instructions')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount', 'unit')
    list_filter = ('ingredient__category',)
    search_fields = ('recipe__title', 'ingredient__name')


@admin.register(IngredientSubstitution)
class IngredientSubstitutionAdmin(admin.ModelAdmin):
    list_display = ('source', 'replacement')
    search_fields = ('source__name', 'replacement__name')


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user__username', 'recipe__title')


# ============ АДМИНКА ДЛЯ КОММЕНТАРИЕВ ============
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'article', 'text_preview', 'parent', 'created_at', 'likes_count']
    list_filter = ['created_at', 'likes_count', 'article']
    search_fields = ['text', 'author__username', 'article__title']
    readonly_fields = ['created_at', 'likes_count']
    ordering = ['-created_at']

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    text_preview.short_description = 'Текст'


# ============ КАСТОМНЫЙ ПОЛЬЗОВАТЕЛЬ ============
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительно для профиля", {"fields": ("bio", "avatar")}),
    )


# ============ РУСИФИКАЦИЯ НАЗВАНИЙ ТАБЛИЦ ============
FoodCategory._meta.verbose_name = "Категория продуктов"
FoodCategory._meta.verbose_name_plural = "Категории продуктов"

Ingredient._meta.verbose_name = "Ингредиент"
Ingredient._meta.verbose_name_plural = "Ингредиенты"

Article._meta.verbose_name = "Рецепт"
Article._meta.verbose_name_plural = "Рецепты"

RecipeIngredient._meta.verbose_name = "Ингредиент рецепта"
RecipeIngredient._meta.verbose_name_plural = "Ингредиенты рецептов"

IngredientSubstitution._meta.verbose_name = "Замена ингредиента"
IngredientSubstitution._meta.verbose_name_plural = "Замены ингредиентов"

FavoriteRecipe._meta.verbose_name = "Избранный рецепт"
FavoriteRecipe._meta.verbose_name_plural = "Избранные рецепты"

Comment._meta.verbose_name = "Комментарий"
Comment._meta.verbose_name_plural = "Комментарии"