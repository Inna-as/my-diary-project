from django import forms
from .models import Comment

# Форма для ввода комментариев
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']  # Пользователь будет заполнять только поле текста

from .models import Article

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content', 'tags'] # Поля, которые пользователь заполняет сам

from .models import CustomUser

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        # Поля, которые пользователь сможет редактировать прямо на сайте
        fields = ['first_name', 'last_name', 'bio', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control rounded-pill px-3'}),
            'bio': forms.Textarea(attrs={'class': 'form-control rounded-3 p-3', 'rows': 4}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
