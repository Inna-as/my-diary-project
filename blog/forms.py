from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Article, CustomUser, Ingredient


# ============ ФОРМА ДЛЯ СОЗДАНИЯ/РЕДАКТИРОВАНИЯ РЕЦЕПТА  ============
class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            'title', 'description', 'instructions', 'category',
            'image', 'cook_time', 'difficulty',
            'calories', 'protein', 'fat', 'carbs',
            'video_url',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control rounded-pill px-3',
                'placeholder': 'Название рецепта'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control rounded-3 p-3',
                'rows': 3,
                'placeholder': 'Краткое описание блюда (можно оставить пустым)'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control rounded-3 p-3',
                'rows': 8,
                'placeholder': 'Подробное описание приготовления...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select rounded-3'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'cook_time': forms.NumberInput(attrs={
                'class': 'form-control rounded-pill px-3',
                'placeholder': 'Время в минутах',
                'min': 1,
            }),
            'difficulty': forms.Select(attrs={
                'class': 'form-select rounded-3'
            }),
            'calories': forms.NumberInput(attrs={
                'class': 'form-control rounded-pill px-3',
                'placeholder': 'ккал',
                'min': 0,
            }),
            'protein': forms.NumberInput(attrs={
                'class': 'form-control rounded-pill px-3',
                'placeholder': 'г',
                'min': 0,
            }),
            'fat': forms.NumberInput(attrs={
                'class': 'form-control rounded-pill px-3',
                'placeholder': 'г',
                'min': 0,
            }),
            'carbs': forms.NumberInput(attrs={
                'class': 'form-control rounded-pill px-3',
                'placeholder': 'г',
                'min': 0,
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control rounded-pill px-3',
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
        }


# ============ ФОРМА ДЛЯ ПРОФИЛЯ ============
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'bio', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'bio': forms.Textarea(attrs={'class': 'form-control rounded-3 p-3', 'rows': 4}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }


# ============ ФОРМА ДЛЯ РЕГИСТРАЦИИ ============
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email')


# ============ ФОРМА ДЛЯ ХОЛОДИЛЬНИКА ============
class FridgeForm(forms.Form):
    ingredients = forms.ModelMultipleChoiceField(
        queryset=Ingredient.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Выберите продукты, которые у вас есть'
    )


# ============ КАЛЬКУЛЯТОР ПОРЦИЙ ============
class PortionsForm(forms.Form):
    portions = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 10,
            'value': 1
        }),
        label='Количество порций'
    )


# ============ ФОРМА ДОБАВЛЕНИЯ ИНГРЕДИЕНТА В РЕЦЕПТ ============
class RecipeIngredientForm(forms.Form):
    ingredient = forms.ModelChoiceField(
        queryset=Ingredient.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Ингредиент'
    )
    amount = forms.DecimalField(
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Количество',
            'step': 0.01
        }),
        label='Количество'
    )
    unit = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Единица измерения (г, шт, мл и т.д.)'
        }),
        label='Единица измерения'
    )


# ============ ПОИСК РЕЦЕПТОВ ============
class RecipeSearchForm(forms.Form):
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-pill px-3',
            'placeholder': 'Поиск по названию...'
        }),
        label='Поиск'
    )