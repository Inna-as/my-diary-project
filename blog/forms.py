from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Article, CustomUser


# ============ ФОРМА ДЛЯ СОЗДАНИЯ/РЕДАКТИРОВАНИЯ РЕЦЕПТА  ============
class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'description', 'instructions', 'category', 'image']
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




# Форма для выбора ингредиентов в холодильнике
class FridgeForm(forms.Form):
    ingredients = forms.ModelMultipleChoiceField(
        queryset=None,  # Заполняется в view
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Выберите продукты, которые у вас есть'
    )


# Форма для калькулятора порций
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


# Форма для добавления ингредиента в рецепт
class RecipeIngredientForm(forms.Form):
    ingredient = forms.ModelChoiceField(
        queryset=None,  # Заполняется в view
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


# Форма для поиска рецептов по ингредиентам
class RecipeSearchForm(forms.Form):
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-pill px-3',
            'placeholder': 'Поиск по названию...'
        }),
        label='Поиск'
    )