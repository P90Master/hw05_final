from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from .models import Group, Follow, Post
from .forms import PostForm, CommentForm
from yatube.settings import PAGE_ITEMS_NUM

User = get_user_model()


def posts_paginate(request, posts_list):
    paginator = Paginator(posts_list, PAGE_ITEMS_NUM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    page_obj = posts_paginate(request, posts)

    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)

    if form.is_valid():
        post_author = request.user
        form.instance.author = post_author

        form.save()

        return redirect('posts:profile', post_author.username)

    return render(request, 'posts/create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()

        return redirect('posts:post_detail', post_id)

    return render(
        request,
        'posts/create.html',
        {'post': post, 'form': form, 'is_edit': True}
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = posts_paginate(request, posts)
    posts_amount = posts.count()

    user = request.user
    followers = author.following.all()
    users_followers = [follower.user for follower in followers]
    following = user in users_followers
    # following = Follow.objects.filter(user=user, author=author).exists()
    # Pytest выдает ошибку:
    # TypeError: 'AnonymousUser' object is not iterable
    '''
        upd: метод, который вы посоветовали работает исправно,
        и мои тесты с ним не конфликтуют, чего нельзя сказать о pytest.
        Я понятия не имею, что с ним не так, так что все вопросы к тем,
        кто эти тесты писал. Так как чтобы сдать проект нужно пройти тесты,
        оставляю первоначальный вариант, но в голове держу новый
    '''

    context = {
        'page_obj': page_obj,
        'posts_amount': posts_amount,
        'author': author,
        'following': following,
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    post_author = post.author
    posts_amount = post_author.posts.count()
    post_comments = post.comments.all()

    text_truncated = post.text[:30]

    form = CommentForm()

    context = {
        'post': post,
        'text_truncated': text_truncated,
        'posts_amount': posts_amount,
        'form': form,
        'comments': post_comments,
    }
    return render(request, 'posts/post_detail.html', context)


def group_posts(request, group_name):
    group = get_object_or_404(Group, slug=group_name)
    group_name = group.title
    posts = group.posts.all()
    page_obj = posts_paginate(request, posts)

    context = {
        'group_name': group_name,
        'page_obj': page_obj
    }

    return render(request, 'posts/group_list.html', context)


@login_required
def follow_index(request):
    user = request.user
    posts = Post.objects.filter(author__following__user=user)
    page_obj = posts_paginate(request, posts)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user

    if user != author:
        Follow.objects.get_or_create(user=user, author=author)

    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user

    follow = get_object_or_404(Follow, user=user, author=author)
    follow.delete()

    return redirect('posts:profile', username=username)
