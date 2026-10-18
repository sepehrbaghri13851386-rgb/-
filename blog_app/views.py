from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import BlogPostForm
from .models import BlogPost, BlogComment, BlogReply

superuser_required = user_passes_test(
    lambda u: u.is_authenticated and u.is_superuser, login_url='sign_in'
)


def blog_list(request):
    paginator = Paginator(BlogPost.objects.all(), 9)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog1.html', {'page': page})


def blog_detail(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    comments = post.comments.select_related('user').prefetch_related('replies__user')
    return render(request, 'blog_detail.html', {'post': post, 'comments': comments})


@superuser_required
def blog_create(request):
    form = BlogPostForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        messages.success(request, 'بلاگ با موفقیت اضافه شد.')
        return redirect(post)
    return render(request, 'blog_form.html', {'form': form, 'is_edit': False})


@superuser_required
def blog_edit(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    form = BlogPostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'بلاگ ویرایش شد.')
        return redirect(post)
    return render(request, 'blog_form.html', {'form': form, 'is_edit': True, 'post': post})


@superuser_required
@require_POST
def blog_delete(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    post.delete()
    messages.success(request, 'بلاگ حذف شد.')
    return redirect('blog1')


@login_required(login_url='sign_in')
@require_POST
def comment_add(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    text = request.POST.get('text', '').strip()
    if text:
        BlogComment.objects.create(post=post, user=request.user, text=text[:1000])
        messages.success(request, 'نظر شما ثبت شد.')
    return redirect(post.get_absolute_url() + '#comments')


@superuser_required
@require_POST
def reply_add(request, comment_id):
    comment = get_object_or_404(BlogComment, pk=comment_id)
    text = request.POST.get('text', '').strip()
    if text:
        BlogReply.objects.create(comment=comment, user=request.user, text=text[:1000])
        messages.success(request, 'پاسخ ثبت شد.')
    return redirect(comment.post.get_absolute_url() + f'#comment-{comment.pk}')


@superuser_required
@require_POST
def reply_delete(request, reply_id):
    reply = get_object_or_404(BlogReply, pk=reply_id)
    post = reply.comment.post
    reply.delete()
    return redirect(post.get_absolute_url() + '#comments')


@superuser_required
@require_POST
def comment_delete(request, comment_id):
    comment = get_object_or_404(BlogComment, pk=comment_id)
    post = comment.post
    comment.delete()
    return redirect(post.get_absolute_url() + '#comments')