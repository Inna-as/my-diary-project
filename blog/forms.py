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
