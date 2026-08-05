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


# 2. Справочник ингредиентов
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

    DIFFICULTY_CHOICES = [
        ('easy', 'Легко'),
        ('medium', 'Средне'),
        ('hard', 'Сложно'),
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
    likes_count = models.PositiveIntegerField(default=0, verbose_name='Количество лайков')

    # ═══════ НОВЫЕ ПОЛЯ: время, сложность, KBJU ═══════
    cook_time = models.PositiveIntegerField(
        "Время приготовления (мин)",
        null=True,
        blank=True,
        help_text="Укажите время в минутах"
    )
    difficulty = models.CharField(
        "Сложность",
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='easy'
    )
    calories = models.PositiveIntegerField("Калорийность (ккал)", null=True, blank=True)
    protein = models.PositiveIntegerField("Белки (г)", null=True, blank=True)
    fat = models.PositiveIntegerField("Жиры (г)", null=True, blank=True)
    carbs = models.PositiveIntegerField("Углеводы (г)", null=True, blank=True)

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

    # Древовидные комментарии - поле parent для ответов
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='Ответ на'
    )

    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    # Лайки на комментарии
    likes = models.ManyToManyField(
        CustomUser,
        related_name='comment_likes',
        blank=True,
        verbose_name='Лайки'
    )

    likes_count = models.PositiveIntegerField(default=0, verbose_name='Количество лайков')
    is_approved = models.BooleanField(
        'Одобрен',
        default=False,
        help_text='Показывать комментарий на сайте'
    )
    is_spam = models.BooleanField(
        'Спам',
        default=False,
        help_text='Автофильтр пометил как спам'
    )
    report_count = models.PositiveIntegerField(
        'Жалоб',
        default=0
    )
    auto_approved = models.BooleanField(
        'Автоодобрен',
        default=False,
        help_text='Пропущен автоматически (доверенный пользователь)'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'{self.author.username}: {self.text[:50]}'

    @property
    def is_reply(self):
        return self.parent is not None

    @property
    def depth(self):
        depth = 0
        parent = self.parent
        while parent:
            depth += 1
            parent = parent.parent
        return depth


# ═══════ ОТДЕЛЬНАЯ МОДЕЛЬ (НЕ внутри Comment!) ═══════
class CommentReport(models.Model):
    """Жалоба пользователя на комментарий."""
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Комментарий'
    )
    reporter = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Пожаловался'
    )
    reason = models.CharField(
        'Причина',
        max_length=50,
        choices=[
            ('spam', 'Спам'),
            ('abuse', 'Оскорбление'),
            ('offtopic', 'Не по теме'),
        ]
    )
    created_at = models.DateTimeField('Дата жалобы', auto_now_add=True)

    class Meta:
        verbose_name = 'Жалоба на комментарий'
        verbose_name_plural = 'Жалобы на комментарии'
        unique_together = ('comment', 'reporter')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.reporter.username} → {self.comment.text[:30]}'