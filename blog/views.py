from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from .models import Article, Tag
from .forms import CommentForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import ArticleForm
from django.core.cache import cache
from django.db.models import Count, Q
from .models import CustomUser







def index_view(request):
    # Получаем параметры поиска, тега и сортировки из адресной строки
    query = request.GET.get('q', '').strip()
    tag_id = request.GET.get('tag', '')
    sort_by = request.GET.get('sort', 'new')

    # Базовый QuerySet: агрегируем количество комментариев к каждой статье через Count
    articles_list = Article.objects.annotate(comments_count=Count('comments'))

    #  Логика переключения сортировки
    if sort_by == 'old':
        articles_list = articles_list.order_by('created_at')  # От старых к новым
    elif sort_by == 'popular':
        articles_list = articles_list.order_by('-comments_count', '-created_at')  # Самые обсуждаемые
    else:
        articles_list = articles_list.order_by('-created_at')  # Сначала новые (по умолчанию)

    # Если передан поисковый запрос (Исправлено для диплома)
    if query:
        words = query.split()
        search_filter = Q()
        for word in words:
            # Слово должно быть И в первом наборе условий, И во втором, но внутри набора ищем через ИЛИ
            word_filter = (
                    Q(title__icontains=word) |
                    Q(content__icontains=word) |
                    Q(author__username__icontains=word)
            )
            search_filter &= word_filter
        articles_list = articles_list.filter(search_filter)

    # Если пользователь кликнул на тег, фильтруем статьи по этому тегу
    selected_tag = None
    if tag_id:
        articles_list = articles_list.filter(tags__id=tag_id)
        selected_tag = get_object_or_404(Tag, id=tag_id)

    # Пагинация
    paginator = Paginator(articles_list, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    popular_tags = Tag.objects.all()

    context = {
        'page_obj': page_obj,
        'popular_tags': popular_tags,
        'query': query,
        'selected_tag': selected_tag,
        'sort_by': sort_by,  # Передаем текущую сортировку обратно в HTML
    }
    return render(request, 'blog/index.html', context)


from django.shortcuts import get_object_or_404




def article_detail_view(request, pk):

    article = get_object_or_404(Article, pk=pk)

    #  Берем только главные комментарии, у которых нет родителя
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

 #Страница профиля автора со списком его статей и статистикой.
def author_profile_view(request, username):

    # Находим автора по его имени, если такого нет — выдаем чистую ошибку 404
    author = get_object_or_404(CustomUser, username=username)

    # Считаем статистику автора через его связи
    total_articles = author.article_set.count()
    total_comments = author.comment_set.count()

    # Забираем все статьи этого автора, сортируя от новых к старым
    author_articles = author.article_set.all().order_by('-created_at')

    # Считаем комментарии к карточкам статей на этой странице
    author_articles = author_articles.annotate(comments_count=Count('comments'))

    context = {
        'author': author,
        'total_articles': total_articles,
        'total_comments': total_comments,
        'author_articles': author_articles,
    }
    return render(request, 'blog/author_profile.html', context)


from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm


@login_required
def profile_view(request):
    if request.method == 'POST':
        # request.FILES обязательно нужен, чтобы поймать файл аватарки!
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'blog/profile.html', {'form': form})



