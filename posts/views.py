from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Comment, Follow


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
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()
    return redirect('post', post.author, post_id)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    all_posts = author.posts.all()
    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        followed_authors = User.objects.filter\
            (following__user=request.user).exists()
        following = author in followed_authors
    return render(request, 'profile.html',
                  {'page': page, 'author': author, 'paginator': paginator,
                   'following': following})


def post_view(request, post_id, username):
    author = get_object_or_404(User, username=username)
    all_posts = author.posts.all().count()
    post = get_object_or_404(Post, author__username=username, id=post_id)
    comments = post.comments.all()
    form = CommentForm()
    interests = author.follower.all().count()
    followers = author.following.all().count()
    following = False
    context = {'author': author,
               'post_list': all_posts,
               'post': post,
               'comments': comments,
               'form': form,
               'following': following,
               'interests': interests,
               'followers': followers,
               'show_comment': True, }
    return render(request, 'post.html', context)


@login_required
def post_edit(request, username: str, post_id: int):
    """This view edits the post by its id and saves changes in database."""
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
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'includes/follow.html',
                  {'paginator': paginator, 'page': page, 'follow': True})


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=username)
    if user.following.exists():
        return redirect('profile', username=username)
    if request.user != user:
        Follow.objects.create(user=request.user,
                              author=User.objects.get(username=username))
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username)
