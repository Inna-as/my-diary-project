from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from .models import Article, Tag
from .forms import CommentForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import ArticleForm
from django.core.cache import cache





def index_view(request):
    # Получаем текст, который пользователь ввёл в строку поиска (если он есть)
    query = request.GET.get('q', '')

    if query:
        # Если поисковый запрос есть, фильтруем статьи.
        articles_list = Article.objects.filter(
            title__icontains=query
        ) | Article.objects.filter(
            content__icontains=query
        )
    else:
        # Если поиска нет, берем вообще все статьи из базы.
        articles_list = Article.objects.all().order_by('-created_at')


    # Передаем пагинатору список статей и говорим: "Выводи по 3 статьи на страницу"
    paginator = Paginator(articles_list, 3)

    # Смотрим, на какой странице сейчас находится пользователь
    page_number = request.GET.get('page')

    # Получаем объект текущей страницы со статьями для этой страницы
    page_obj = paginator.get_page(page_number)

    popular_tags = Tag.objects.all()


    # Собираем все данные в один словарь
    context = {
        'page_obj': page_obj,  # Здесь лежат статьи для текущей страницы
        'popular_tags': popular_tags,  # Здесь лежат теги
        'query': query,  # Возвращаем текст поиска обратно в инпут
    }

    # Функция render склеивает наш HTML-шаблон с данными из словаря context
    return render(request, 'blog/index.html', context)


from django.shortcuts import get_object_or_404


# (Остальные импорты у вас уже есть сверху файла)

def article_detail_view(request, pk):

    article = get_object_or_404(Article, pk=pk)

    # ИСПРАВЛЕНО: Берем только ГЛАВНЫЕ комментарии, у которых нет родителя (parent=None)
    comments = article.comments.filter(parent=None)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user

            # Проверяем, нажал ли пользователь кнопку «Ответить».
            # Если да, скрытое поле parent_id передаст ID главного комментария.
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent_id = int(parent_id)  # Привязываем ответ к родителю

            comment.save()
            return redirect('blog:article_detail', pk=article.pk)
    else:
        form = CommentForm()

    context = {
        'article': article,
        'comments': comments,  # Передаем только корневые комментарии
        'form': form,
    }
    return render(request, 'blog/article_detail.html', context)


def register_view(request):
    """
    Страница регистрации новых пользователей.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Создаем пользователя в базе данных
            login(request, user)  # Сразу автоматически авторизуем его на сайте
            return redirect('blog:index')  # Уводим на главную страницу
    else:
        form = UserCreationForm()  # Если просто зашли — показываем пустую форму

    return render(request, 'blog/register.html', {'form': form})


@login_required  # Перенаправит гостя на вход, если он попытается зайти по ссылке
def article_create_view(request):

    #Страница создания новой статьи.

    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user  # Автоматически ставим автором того, кто сейчас залогинен
            article.save()  # Сохраняем статью
            form.save_m2m() # Сохраняем теги
            cache.delete('sidebar_tags')
            return redirect('blog:index')  # Уводим на главную страницу
    else:
        form = ArticleForm()  # Если просто зашли — показываем пустую форму

    return render(request, 'blog/article_form.html', {'form': form})


@login_required
def article_update_view(request, pk):

    # Редактирование статьи (доступно только автору).

    # Находим статью по ID
    article = get_object_or_404(Article, pk=pk)

    # ПРОВЕРКА ПРАВ :если текущий пользователь не автор,
    # мы  возвращаем его на главную страницу и не даем ничего менять.
    if article.author != request.user:
        return redirect('blog:index')

    if request.method == 'POST':
        # Передаем в форму то, что ввел юзер, и привязываем к нашей старой статье
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            return redirect('blog:article_detail', pk=article.pk)  # Возвращаем в статью
    else:
        # Если просто зашли — показываем форму, уже заполненную старым текстом статьи
        form = ArticleForm(instance=article)

    return render(request, 'blog/article_form.html', {'form': form})


@login_required
def article_delete_view(request, pk):

    # Удаление статьи (доступно только автору).

    article = get_object_or_404(Article, pk=pk)

    # Проверка прав доступа
    if article.author != request.user:
        return redirect('blog:index')

    if request.method == 'POST':
        article.delete()  # Физически удаляем статью из базы данных
        return redirect('blog:index')  # Уводим на главную страницу

    # Если метод GET — показываем страницу с вопросом "Вы уверены?"
    return render(request, 'blog/article_confirm_delete.html', {'article': article})
