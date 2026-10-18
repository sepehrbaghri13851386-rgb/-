from django.contrib import messages  # noqa: F401  (kept for future use)
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.views.decorators.http import require_POST

from ghaza_app.cart import cart_details

from .models import DetailCategory, DetailComment, DetailItem, DetailReply

TEMPLATE = 'restaurant-details.html'


def _cart_context(request):
    items, totals = cart_details(request.session)
    return {'cart_items': items, 'cart_totals': totals}


def _avatar_url(user):
    profile = getattr(user, 'profile', None)
    if profile and getattr(profile, 'avatar', None):
        try:
            return profile.avatar.url
        except ValueError:
            pass
    return staticfiles_storage.url('assets/images/images (7).jpg')


def _flash(request, kind, text):
    request.session['goz_flash'] = {'kind': kind, 'text': text}


def details_list(request, category_id=None):
    """همهٔ موردها یا فقط موردهای یک دسته‌بندی (مثلاً پیتزاها)."""
    approved = Q(comments__is_approved=True)
    items = (DetailItem.objects.filter(is_available=True)
             .select_related('category')
             .annotate(comment_count=Count('comments', filter=approved),
                       avg=Avg('comments__rating', filter=approved)))
    selected = None
    if category_id:
        selected = get_object_or_404(DetailCategory, pk=category_id)
    items = list(items)
    for it in items:
        it.pct = round((it.avg or 0) * 20)
        it.avg_r = round(it.avg or 0, 1)
    ctx = {
        'categories': DetailCategory.objects.all(),
        'selected_category': selected,
        'gz_items': items,
        'gz_item': None,
    }
    ctx.update(_cart_context(request))
    return render(request, TEMPLATE, ctx)


def details_item(request, pk):
    item = get_object_or_404(DetailItem.objects.select_related('category'),
                             pk=pk, is_available=True)
    comments = list(item.comments.filter(is_approved=True)
                    .select_related('user', 'reply'))
    for c in comments:
        c.avatar = _avatar_url(c.user)
        c.pct = c.rating * 20
        c.reply_obj = getattr(c, 'reply', None)
    avg = item.comments.filter(is_approved=True).aggregate(a=Avg('rating'))['a'] or 0
    images = [item.image.url] + [g.image.url for g in item.gallery.all()]
    ctx = {
        'categories': DetailCategory.objects.all(),
        'selected_category': item.category,
        'gz_item': item,
        'gz_images': images,
        'gz_comments': comments,
        'gz_avg': round(avg, 1),
        'gz_avg_round': round(avg),
        'gz_avg_pct': round(avg * 20),
        'gz_flash': request.session.pop('goz_flash', None),
    }
    ctx.update(_cart_context(request))
    return render(request, TEMPLATE, ctx)


@require_POST
def comment_add(request, pk):
    item = get_object_or_404(DetailItem, pk=pk, is_available=True)
    back = reverse('details_item', args=[item.pk])
    if not request.user.is_authenticated:
        return redirect(f"{reverse('sign_in')}?next={back}")
    text = request.POST.get('text', '').strip()
    try:
        rating = int(request.POST.get('rating', '5'))
    except ValueError:
        rating = 0
    if not 3 <= len(text) <= 500:
        _flash(request, 'err', 'متن نظر باید بین ۳ تا ۵۰۰ حرف باشد.')
    elif not 1 <= rating <= 5:
        _flash(request, 'err', 'لطفاً امتیاز ۱ تا ۵ را انتخاب کنید.')
    else:
        DetailComment.objects.create(item=item, user=request.user,
                                     rating=rating, text=text)
        _flash(request, 'ok', 'نظر شما ثبت شد. ممنون از همراهی‌تان!')
    return redirect(back + '#gz-comments')


@require_POST
def reply_add(request, comment_id):
    """فقط ادمین/استاف می‌تواند به نظر پاسخ بدهد."""
    if not (request.user.is_authenticated and request.user.is_staff):
        raise PermissionDenied
    comment = get_object_or_404(DetailComment, pk=comment_id)
    text = request.POST.get('text', '').strip()
    if text:
        DetailReply.objects.update_or_create(
            comment=comment,
            defaults={'author': request.user,
                      'author_name': request.user.get_full_name() or request.user.get_username(),
                      'text': text[:500]})
        _flash(request, 'ok', 'پاسخ شما ثبت شد.')
    else:
        _flash(request, 'err', 'متن پاسخ خالی است.')
    return redirect(reverse('details_item', args=[comment.item_id]) + '#gz-comments')