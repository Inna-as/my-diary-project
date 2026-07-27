from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# ============ ПОЛЬЗОВАТЕЛЬСКАЯ МОДЕЛЬ ============
class CustomUser(AbstractUser):
    bio = models.TextField("О себе", blank=True)
    avatar = models.ImageField("Фотография профиля", upload_to="avatars/", blank=True, null=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


# ============ НОВАЯ АРХИТЕКТУРА "УМНЫЙ ХОЛОДИЛЬНИК" ============

# 1. Категории продуктов (Мясо, Овощи, Молочка и т.д.)
class FoodCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название категории")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория продуктов"
        verbose_name_plural = "Категории продуктов"
        ordering = ['name']


# 2. Справочник ингредиентов (Курица, Томаты, Сметана)
class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название ингредиента")
    category = models.ForeignKey(
        FoodCategory,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name="Категория"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ['name']


# 3. Модель рецепта
class Article(models.Model):
    # ВАЖНО: Добавили категории блюд
    DISH_CATEGORY_CHOICES = [
        ('dessert', 'Десерт'),
        ('appetizer', 'Закуска'),
        ('first', 'Первые блюда'),
        ('second', 'Вторые блюда'),
        ('snack', 'Перекус'),
        ('drink', 'Напиток'),
        ('salad', 'Салат'),
        ('soup', 'Суп'),
        ('main', 'Основное блюдо'),
        ('baking', 'Выпечка'),
    ]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='article_set',
        verbose_name="Автор"
    )
    title = models.CharField(max_length=200, verbose_name="Название блюда")
    instructions = models.TextField(verbose_name="Пошаговые инструкции")
    is_published = models.BooleanField("Одобрено админом", default=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    # Новые поля
    category = models.CharField(
        max_length=20,
        choices=DISH_CATEGORY_CHOICES,
        default='main',
        verbose_name="Категория блюда"
    )
    description = models.TextField(verbose_name="Описание", blank=True, null=True)
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name="Изображение",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ['-created_at']


# 4. Связь рецепта и ингредиентов + количество порции
class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name="Рецепт"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент"
    )
    amount = models.FloatField(verbose_name="Количество на 1 порцию")
    unit = models.CharField(max_length=50, verbose_name="Единица измерения")

    def __str__(self):
        return f"{self.ingredient.name} для {self.recipe.title}"

    class Meta:
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецептов"


# 5. Умные замены продуктов
class IngredientSubstitution(models.Model):
    source = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='substitutions_from',
        verbose_name="Исходный продукт"
    )
    replacement = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='substitutions_to',
        verbose_name="Продукт-аналог"
    )

    def __str__(self):
        return f"{self.source.name} → {self.replacement.name}"

    class Meta:
        verbose_name = "Замена ингредиента"
        verbose_name_plural = "Замены ингредиентов"


# 6. Личная кулинарная книга (Избранное)
class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='favored_by',
        verbose_name="Рецепт"
    )

    class Meta:
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} → {self.recipe.title}"


class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'{self.author.username}: {self.text[:50]}'