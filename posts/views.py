from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Comment, Follow, get_followed_authors
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.select_related('group')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page,
                                          'paginator': paginator})

def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {"group": group, "post_list": post_list,
         "page": page, "paginator": paginator}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request, "new.html", {'form': form})
    form = PostForm()
    return render(request, "new.html", {'form': form})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.author = request.user
            new_comment.post = post
            new_comment.save()
        return redirect('post', username, post_id)
    return render(request, 'post.html', {'form': form, 'post': post})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    all_posts = author.posts.all()
    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    interests = author.follower.all().count()
    followers = author.following.all().count()
    post_count = all_posts.count()
    if request.user.is_authenticated:
        if Follow.objects.filter(user=request.user, author=author):
            following = True
        else:
            following = False
        return render(request, 'profile.html', {
            'paginator': paginator,
            'author': author,
            'post_list': all_posts,
            'post_count': post_count,
            'page': page,
            'following': following,
            'interests': interests,
            'followers': followers,
        })
    else:
        return render(request, 'profile.html', {
            'paginator': paginator,
            'author': author,
            'post_list': all_posts,
            'post_count': post_count,
            'page': page,
            'interests': interests,
            'followers': followers,
        })


def post_view(request, post_id, username):
    author = get_object_or_404(User, username=username)
    all_posts = author.posts.all().count()
    post = author.posts.get(id=post_id)
    comments = Comment.objects.filter(post=post)
    form = CommentForm()
    interests = author.follower.all().count()
    followers = author.following.all().count()
    if request.user.is_authenticated:
        if Follow.objects.filter(user=request.user, author=author):
            following = True
        else:
            following = False
        return render(request, 'post.html', {
            'author': author,
            'post_list': all_posts,
            'post': post,
            'comments': comments,
            'form': form,
            'following': following,
            'interests': interests,
            'followers': followers})
    else:
        return render(request, "post.html", {
            'post': post,
            'author': post.author,
            'post_list': all_posts,
            'post_count': post_count,
            'comments': comments,
            'form': form,
            'interests': interests,
            'followers': followers})


@login_required
def post_edit(request, username: str, post_id: int):
    """This view edits the post by its id and saves changes in database."""
    # author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if post.author != request.user:
        return redirect('post', username, post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username, post_id)
    return render(request, 'new.html', {"form": form, 'post': post})


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    interests = request.user.follower.all()
    interest_authors = []
    for i in interests:
        interest_authors.append(i.author)
    posts = Post.objects.filter(author__in=interest_authors)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request,
                  "follow.html",
                  {"paginator": paginator, 'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        if Follow.objects.filter(user=request.user,
                                 author=author).exists() is not True:
            Follow.objects.create(
                user=request.user,
                author=author
            )
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username)
