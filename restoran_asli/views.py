from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from ghaza_app.cart import add_to_cart, cart_details, clear_cart, remove_from_cart, set_qty
from ghaza_app.forms import (AvatarForm, PasswordChangeSimpleForm, ProfileEditForm,
                             SignInForm, SignUpForm)
from ghaza_app.models import (Category, Comment, CommentReply, ContactMessage, Food,
                              Order, OrderItem, Profile)
from GOZIYAT_APP.models import DetailCategory, DetailItem
from nazerat_app.models import ContactReply


# ---------------------------------------------------------------------------
#  جستجو: ابزارهای مشترک
# ---------------------------------------------------------------------------

# یکدست‌سازی متن فارسی: ی/ي، ک/ك، آ/أ/إ/ا، ۀ/ة/ه و اعداد فارسی/عربی
_FA_ALIASES = str.maketrans({
    'ی': 'ي', 'ک': 'ك', 'آ': 'ا', 'أ': 'ا', 'إ': 'ا', 'ۀ': 'ه', 'ة': 'ه',
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5', '۶': '6',
    '۷': '7', '۸': '8', '۹': '9',
    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4', '٥': '5', '٦': '6',
    '٧': '7', '٨': '8', '٩': '9',
})

# برای وقتی که متن دیتابیس با حروف فارسی («ی» و «ک») ذخیره شده باشد
_FA_BACK = str.maketrans({'ي': 'ی', 'ك': 'ک'})

SEARCH_SCOPES = ('food', 'item', 'all')


def _canon(text):
    """متن را برای مقایسه یکدست می‌کند (ی/ك عربی، ا/آ، اعداد فارسی، فاصلهٔ اضافه)."""
    return ' '.join((text or '').translate(_FA_ALIASES).lower().split())


def _variants(query):
    """حالت‌های نوشتاری مختلف یک عبارت، برای جستجوی دیتابیسی."""
    query = (query or '').strip()
    if not query:
        return []
    canon = _canon(query)
    out = []
    for variant in (canon, canon.translate(_FA_BACK), query.lower()):
        if variant and variant not in out:
            out.append(variant)
    return out


def _or_icontains(fields, query):
    """Q(...) برای جستجوی «شامل» روی چند فیلد، با در نظر گرفتن حالت‌های نوشتاری."""
    condition = Q()
    for field in fields:
        for variant in _variants(query):
            condition |= Q(**{f'{field}__icontains': variant})
    return condition


def _matches(query, *texts):
    """آیا عبارت جستجو در یکی از متن‌ها هست؟ (بدون حساسیت به ی/ك و اعداد)"""
    needle = _canon(query)
    return bool(needle) and any(needle in _canon(text) for text in texts)


def _matched_categories(queryset, query, cat_id, fields=('name', 'slug')):
    """دسته‌هایی که یا با ?cat= انتخاب شده‌اند یا نام‌شان با عبارت جستجو می‌خواند.

    fields فقط شامل فیلدهای واقعی مدل باشد (DetailCategory فیلد slug ندارد).
    """
    found, seen = [], set()
    if cat_id.isdigit():
        for category in queryset.filter(pk=int(cat_id)):
            found.append(category)
            seen.add(category.pk)
    if query:
        for category in queryset.filter(_or_icontains(list(fields), query)):
            if category.pk not in seen:
                found.append(category)
                seen.add(category.pk)
    return found


def _group_by_category(queryset, matched_ids=()):
    """آیتم‌ها را بر اساس دسته‌بندی گروه می‌کند؛ ترتیب حضور اولیه حفظ می‌شود.

    اگر دسته‌ای با نامش پیدا شده باشد، کل آیتم‌های آن دسته داخل همین گروه
    برمی‌گردد (خواستهٔ «دسته را که بزنی، کل دسته بیاید»)."""
    groups, index = [], {}
    for item in queryset:
        group = index.get(item.category_id)
        if group is None:
            group = {'category': item.category, 'items': [],
                     'match': item.category_id in matched_ids}
            index[item.category_id] = group
            groups.append(group)
        group['items'].append(item)
    # گروه‌هایی که نام دسته‌شان با جستجو خوانده، اول نمایش داده می‌شوند
    groups.sort(key=lambda g: (not g['match'], getattr(g['category'], 'order', 0),
                               g['category'].pk))
    return groups


def search(request):
    """جستجوی بخش‌محور در سراسر سایت.

    ?q=      عبارت جستجو (نام غذا، توضیحات یا نام دسته)
    ?scope=  food → فقط غذاهای صفحهٔ اصلی | item → فقط منوی رستوران | all → هر دو
    ?cat=    شناسهٔ دسته‌بندی → همهٔ آیتم‌های آن دسته برمی‌گردد

    اگر عبارت جستجو (یا ?cat=) با نام یک دسته‌بندی بخواند، تمام آیتم‌های آن
    دسته — نه فقط آن‌هایی که اسمشان با عبارت می‌خواند — نمایش داده می‌شوند.
    """
    query = (request.GET.get('q') or request.GET.get('search') or '').strip()[:80]
    scope = request.GET.get('scope') or 'all'
    if scope not in SEARCH_SCOPES:
        scope = 'all'
    cat_id = (request.GET.get('cat') or '').strip()

    want_food = scope in ('food', 'all')
    want_item = scope in ('item', 'all')
    approved = Q(comments__is_approved=True)

    food_groups, food_categories, matched_food_ids = [], [], set()
    if want_food:
        food_categories = list(Category.objects.all())
        matched = _matched_categories(Category.objects.all(), query, cat_id)
        matched_food_ids = {c.pk for c in matched}
        foods = (Food.objects.filter(is_available=True)
                 .select_related('category')
                 .annotate(comment_count=Count('comments', filter=approved),
                           avg_rating=Avg('comments__rating', filter=approved)))
        condition = Q(category__in=matched) if matched else Q()
        if query:
            condition |= _or_icontains(['name', 'description'], query)
        foods = foods.filter(condition) if condition else foods.none()
        food_groups = _group_by_category(foods, matched_food_ids)

    item_groups, item_categories, matched_item_ids = [], [], set()
    if want_item:
        item_categories = list(DetailCategory.objects.all())
        matched = _matched_categories(DetailCategory.objects.all(), query, cat_id,
                                      fields=('name',))
        matched_item_ids = {c.pk for c in matched}
        items = (DetailItem.objects.filter(is_available=True)
                 .select_related('category')
                 .annotate(comment_count=Count('comments', filter=approved),
                           avg=Avg('comments__rating', filter=approved)))
        condition = Q(category__in=matched) if matched else Q()
        if query:
            condition |= _or_icontains(['title', 'description'], query)
        items = items.filter(condition) if condition else items.none()
        for it in items:
            it.avg_r = round(it.avg or 0, 1)
        item_groups = _group_by_category(items, matched_item_ids)

    food_total = sum(len(g['items']) for g in food_groups)
    item_total = sum(len(g['items']) for g in item_groups)

    # نام دسته‌ای که کاربر روی آن کلیک کرده (برای عنوان «کل دستهٔ …»)
    cat_name = ''
    if cat_id.isdigit():
        picked = (Category.objects.filter(pk=int(cat_id)).first()
                  or DetailCategory.objects.filter(pk=int(cat_id)).first())
        cat_name = picked.name if picked else ''

    context = {
        'q': query,
        'scope': scope,
        'cat_id': cat_id,
        'cat_name': cat_name,
        'food_groups': food_groups,
        'item_groups': item_groups,
        'food_categories': food_categories,
        'item_categories': item_categories,
        'food_total': food_total,
        'item_total': item_total,
        'result_total': food_total + item_total,
        'matched_food_ids': matched_food_ids,
        'matched_item_ids': matched_item_ids,
        'searched': bool(query or cat_id),
    }
    context.update(_cart_context(request))
    return render(request, 'search.html', context)


def _cart_context(request):
    items, totals = cart_details(request.session)
    return {'cart_items': items, 'cart_totals': totals}


def _safe_next(request):
    """A local redirect target from ?next= (guarded against open redirects)."""
    candidate = request.POST.get('next') or request.GET.get('next')
    if candidate and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return candidate
    return ''


def _avatar_url(user):
    """Profile picture of the user, or the default avatar (images (7).jpg)."""
    profile = getattr(user, 'profile', None)
    if profile and profile.avatar:
        try:
            return profile.avatar.url
        except ValueError:
            pass
    return staticfiles_storage.url('assets/images/images (7).jpg')


def _contact_entries(qs, with_reply=False):
    """Serialize approved contact messages for the testimonial sections."""
    entries = []
    for m in qs:
        entry = {
            'id': m.pk,
            'name': m.display_name,
            'text': m.text,
            'avatar': _avatar_url(m.user),
            'date': m.time_ago,
        }
        if with_reply:
            r = getattr(m, 'owner_reply', None)
            entry['reply'] = ({
                'name': r.author_name,
                'text': r.text,
                'avatar': _avatar_url(r.author),
            } if r else None)
        entries.append(entry)
    return entries


def _is_owner(user):
    """فقط سوپریوزر (صاحب سایت) می‌تواند پاسخ بدهد."""
    return user.is_authenticated and user.is_superuser


def _back_to(anchor):
    return redirect(f"{reverse('testimonials')}#{anchor}")


def index(request):
    categories = Category.objects.all()
    approved = Q(comments__is_approved=True)
    foods = (
        Food.objects.filter(is_available=True)
        .select_related('category')
        .annotate(
            comment_count=Count('comments', filter=approved),
            avg_rating=Avg('comments__rating', filter=approved),
        )
    )
    latest_comments = (
        Comment.objects.filter(is_approved=True, food__is_available=True)
        .select_related('food', 'food__category')[:3]
    )
    happy_customers = _contact_entries(
        ContactMessage.objects.filter(is_approved=True)
        .select_related('user', 'user__profile')[:6]
    )
    context = {
        'categories': categories,
        'foods': foods,
        'latest_comments': latest_comments,
        'happy_customers': happy_customers,
    }
    context.update(_cart_context(request))
    return render(request, 'index.html', context)


def about(request):
    return render(request, 'about.html', _cart_context(request))


def restaurants(request):
    return render(request, 'restaurants.html', _cart_context(request))


def restaurant_details(request):
    return render(request, 'restaurant-details.html', _cart_context(request))


def cart(request):
    return render(request, 'cart.html', _cart_context(request))


# ---------------------------------------------------------------------------
#  تسویهٔ خرید: ثبت سفارش (مرحلهٔ ۱ اطلاعات ← ۲ پرداخت ← ۳ تأیید)
# ---------------------------------------------------------------------------

def _checkout_login_required(request):
    """سفارش فقط برای کاربر واردشده؛ او را به ورود با next می‌فرستیم."""
    if request.user.is_authenticated:
        return None
    return redirect(f"{reverse('sign_in')}?next={reverse('checkout')}")


def _place_order(request, payment):
    """سفارش را از سبد خرید + اطلاعات ارسالِ ذخیره‌شده در session می‌سازد
    و سبد را خالی می‌کند. در صورت خطا None برمی‌گرداند."""
    items, totals = cart_details(request.session)
    data = request.session.get('checkout_data') or {}
    if not items:
        messages.error(request, 'سبد خرید شما خالی است؛ ابتدا غذایی اضافه کنید.')
        return None
    if not (data.get('phone') and data.get('city') and data.get('address')):
        messages.error(request, 'اطلاعات ارسال تکمیل نیست؛ لطفاً دوباره تلاش کنید.')
        return None
    order = Order.objects.create(
        user=request.user,
        recipient=(data.get('recipient') or request.user.get_full_name()
                   or request.user.username),
        phone=data['phone'],
        city=data['city'],
        address=data['address'],
        when=data.get('when', ''),
        note=data.get('note', ''),
        payment=payment,
        subtotal=totals['subtotal'],
        delivery_fee=totals['delivery_fee'],
        total=totals['grand_total'],
    )
    OrderItem.objects.bulk_create([
        OrderItem(order=order, name=it['food'].name, qty=it['qty'],
                  unit_price=it['food'].final_price)
        for it in items
    ])
    clear_cart(request.session)
    request.session.pop('checkout_data', None)
    request.session['last_order_id'] = order.pk
    return order


def checkout(request):
    """مرحلهٔ ۱: اطلاعات ارسال. در POST ذخیره می‌شود و بسته به روش پرداخت،
    یا به درگاه (مرحلهٔ ۲) می‌رود یا سفارش مستقیماً ثبت می‌شود."""
    gate = _checkout_login_required(request)
    if gate:
        return gate

    items, totals = cart_details(request.session)
    data = request.session.get('checkout_data') or {}
    profile_obj = getattr(request.user, 'profile', None)

    if request.method == 'POST':
        values = {
            'name': (request.POST.get('name') or '').strip(),
            'phone': (request.POST.get('phone') or '').strip().replace(' ', ''),
            'city': (request.POST.get('city') or '').strip(),
            'address': (request.POST.get('address') or '').strip(),
            'when': (request.POST.get('when') or '').strip(),
            'note': (request.POST.get('note') or '').strip(),
        }
        payment = (request.POST.get('payment') or 'gateway').strip()
        if payment not in {c[0] for c in Order.PAYMENT_CHOICES}:
            payment = 'gateway'

        errors = {}
        if not items:
            messages.error(request, 'سبد خرید شما خالی است؛ ابتدا غذایی اضافه کنید.')
            return redirect('cart')
        if not values['phone'] or not values['phone'].isdigit() or len(values['phone']) < 10:
            errors['phone'] = 'شمارهٔ تماس معتبر نیست (مثلاً ۰۹۱۲۱۲۳۴۵۶۷).'
        if not values['city']:
            errors['city'] = 'شهر را وارد کنید.'
        if not values['address']:
            errors['address'] = 'آدرس تحویل را وارد کنید.'

        if errors:
            context = _cart_context(request)
            context.update({'form_errors': errors, 'form_values': values})
            return render(request, 'checkout.html', context)

        values['payment'] = payment
        request.session['checkout_data'] = values
        if payment == 'gateway':
            return redirect('checkout_step2')
        order = _place_order(request, payment)
        if order is not None:
            messages.success(request, f'سفارش شما ثبت شد؛ کد پیگیری #{order.pk}')
            return redirect('checkout_step3')
        return redirect('cart')

    # GET: پیش‌پرکردن فیلدها از اطلاعات قبلی / پروفایل کاربر
    values = {
        'name': (data.get('recipient') or request.user.get_full_name()
                 or request.user.username),
        'phone': data.get('phone') or (profile_obj.phone if profile_obj else ''),
        'city': data.get('city', ''),
        'address': data.get('address', ''),
        'when': data.get('when', ''),
        'note': data.get('note', ''),
    }
    context = _cart_context(request)
    context.update({'form_values': values, 'form_errors': {}})
    return render(request, 'checkout.html', context)


def checkout_step2(request):
    """مرحلهٔ ۲: صفحهٔ پرداخت (درگاه). «تأیید نهایی» سفارش را ثبت می‌کند."""
    gate = _checkout_login_required(request)
    if gate:
        return gate
    if request.method == 'POST':
        data = request.session.get('checkout_data') or {}
        order = _place_order(request, data.get('payment') or 'gateway')
        if order is not None:
            messages.success(request, f'سفارش شما ثبت شد؛ کد پیگیری #{order.pk}')
            return redirect('checkout_step3')
        return redirect('cart')
    return render(request, 'checkout-step2.html', _cart_context(request))


def checkout_step3(request):
    """مرحلهٔ ۳: سفارش ثبت‌شده؛ اگر چیزی ثبت نشده باشد، خلاصهٔ سبد نمایش داده می‌شود."""
    context = _cart_context(request)
    order = None
    if request.user.is_authenticated:
        order = (Order.objects
                 .filter(pk=request.session.get('last_order_id'), user=request.user)
                 .prefetch_related('items').first())
    if order is not None:
        context['order'] = order
    return render(request, 'checkout-step3.html', context)


def contact(request):
    return render(request, 'contact.html', _cart_context(request))


def faqs(request):
    return render(request, 'faqs.html', _cart_context(request))


def profile(request):
    return render(request, 'profile.html', _cart_context(request))


def blog1(request):
    return render(request, 'blog1.html', _cart_context(request))


def blog2(request):
    return render(request, 'blog2.html', _cart_context(request))


def blog_single(request):
    return render(request, 'blog-single.html', _cart_context(request))


def sign_in(request):
    """Login page (backend wired: username OR e-mail + password)."""
    next_url = _safe_next(request)
    if request.user.is_authenticated:
        return redirect(next_url or 'profile')
    form = SignInForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        auth_login(request, user)
        messages.success(request, f"خوش آمدید، {user.first_name or user.username}!")
        return redirect(next_url or 'profile')
    context = {'form': form, 'next': next_url or ''}
    context.update(_cart_context(request))
    return render(request, 'sign-in.html', context)


def sign_up(request):
    """Registration page (backend wired: creates User + Profile and logs in)."""
    next_url = _safe_next(request)
    if request.user.is_authenticated:
        return redirect(next_url or 'profile')
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        auth_login(request, user)
        messages.success(request, "ثبت‌نام با موفقیت انجام شد. خوش آمدید!")
        return redirect(next_url or 'profile')
    context = {'form': form, 'next': next_url}
    context.update(_cart_context(request))
    return render(request, 'sign-up.html', context)


def sign_out(request):
    """Log the user out and send them back home."""
    auth_logout(request)
    messages.info(request, "از حساب خود خارج شدید.")
    return redirect('index')


@login_required
def profile_edit(request):
    """Profile page: edit name / e-mail / phone / avatar, and change password."""
    # کاربرهای قدیمی (قبل از سیگنال ساخت Profile) ممکن است سطر پروفایل نداشته باشند؛
    # بدون این، ذخیرهٔ آواتار با IntegrityError (NOT NULL user_id) می‌شکست.
    profile_obj = Profile.objects.get_or_create(user=request.user)[0]
    if request.method == 'POST':
        if 'change_password' in request.POST:
            pw_form = PasswordChangeSimpleForm(request.user, request.POST)
            edit_form = ProfileEditForm(instance=request.user)
            avatar_form = AvatarForm(instance=profile_obj)
            if pw_form.is_valid():
                request.user.set_password(pw_form.cleaned_data['new_password1'])
                request.user.save()
                auth_login(request, request.user)  # keep the session after password change
                messages.success(request, "رمز عبور با موفقیت تغییر کرد.")
                return redirect('profile')
            messages.error(request, "تغییر رمز عبور انجام نشد؛ خطاها را ببینید.")
        elif 'save_avatar' in request.POST:
            edit_form = ProfileEditForm(instance=request.user)
            avatar_form = AvatarForm(request.POST, request.FILES, instance=profile_obj)
            pw_form = PasswordChangeSimpleForm(request.user)
            if avatar_form.is_valid():
                avatar_form.save()
                messages.success(request, "عکس پروفایل به‌روزرسانی شد.")
                return redirect('profile')
            messages.error(request, "بارگذاری عکس انجام نشد؛ فرمت یا حجم فایل را بررسی کنید.")
        else:
            edit_form = ProfileEditForm(request.POST, instance=request.user)
            avatar_form = AvatarForm(instance=profile_obj)
            pw_form = PasswordChangeSimpleForm(request.user)
            if edit_form.is_valid():
                edit_form.save()
                if profile_obj is not None:
                    profile_obj.phone = edit_form.cleaned_data.get('phone', '')
                    profile_obj.save()
                messages.success(request, "اطلاعات پروفایل به‌روزرسانی شد.")
                return redirect('profile')
    else:
        initial = {'phone': profile_obj.phone if profile_obj else ''}
        edit_form = ProfileEditForm(instance=request.user, initial=initial)
        avatar_form = AvatarForm(instance=profile_obj)
        pw_form = PasswordChangeSimpleForm(request.user)
    context = {
        'edit_form': edit_form,
        'pw_form': pw_form,
        'avatar_form': avatar_form,
        'phone': profile_obj.phone if profile_obj else '',
        'avatar_url': _avatar_url(request.user),
        'orders': request.user.orders.prefetch_related('items'),
    }
    context.update(_cart_context(request))
    return render(request, 'profile.html', context)


def testimonials(request):
    """Customer wall: messages sent from the contact page + food comments
    (with the owner's replies) are shown here."""
    contact_testimonials = _contact_entries(
        ContactMessage.objects.filter(is_approved=True)
        .select_related('user', 'user__profile', 'owner_reply', 'owner_reply__author'),
        with_reply=True,
    )
    comments = (
        Comment.objects.filter(is_approved=True, food__is_available=True)
        .select_related('food', 'food__category', 'reply', 'reply__author')
    )
    comment_entries = [
        {
            'id': c.pk,
            'name': c.name,
            'initial': c.name[:1],
            'food': c.food.name,
            'text': c.text,
            'rating': c.rating,
            'date': c.time_ago,
            'reply': ({
                'name': c.reply.author_name,
                'text': c.reply.text,
                'avatar': _avatar_url(c.reply.author),
            } if hasattr(c, 'reply') else None),
        }
        for c in comments
    ]
    context = {
        'contact_testimonials': contact_testimonials,
        'comment_entries': comment_entries,
    }
    context.update(_cart_context(request))
    return render(request, 'testimonials.html', context)


@require_POST
def reply_add(request, comment_id):
    """فقط سوپریوزر می‌تواند به نظر یک غذا پاسخ بدهد (ثبت یا ویرایش)."""
    if not _is_owner(request.user):
        raise PermissionDenied
    comment = get_object_or_404(Comment, pk=comment_id)
    text = request.POST.get('text', '').strip()
    if not text:
        messages.error(request, "متن پاسخ خالی است.")
        return _back_to(f'comment-{comment.pk}')
    reply, created = CommentReply.objects.update_or_create(
        comment=comment,
        defaults={
            'author': request.user,
            'author_name': request.user.get_full_name() or request.user.username,
            'text': text[:500],
        })
    messages.success(request, "پاسخ شما ثبت شد." if created else "پاسخ به‌روزرسانی شد.")
    return _back_to(f'comment-{comment.pk}')


@require_POST
def reply_delete(request, comment_id):
    """حذف پاسخ صاحب سایت از زیر نظر یک غذا (فقط سوپریوزر)."""
    if not _is_owner(request.user):
        raise PermissionDenied
    CommentReply.objects.filter(comment_id=comment_id).delete()
    messages.success(request, "پاسخ حذف شد.")
    return _back_to(f'comment-{comment_id}')


@require_POST
def contact_reply_add(request, message_id):
    """فقط سوپریوزر می‌تواند به پیام «تماس با ما» پاسخ بدهد (ثبت یا ویرایش)."""
    if not _is_owner(request.user):
        raise PermissionDenied
    message = get_object_or_404(ContactMessage, pk=message_id)
    text = request.POST.get('text', '').strip()
    if not text:
        messages.error(request, "متن پاسخ خالی است.")
        return _back_to(f'contact-{message.pk}')
    _, created = ContactReply.objects.update_or_create(
        message=message,
        defaults={
            'author': request.user,
            'author_name': request.user.get_full_name() or request.user.username,
            'text': text[:500],
        })
    messages.success(request, "پاسخ شما ثبت شد." if created else "پاسخ به‌روزرسانی شد.")
    return _back_to(f'contact-{message.pk}')


@require_POST
def contact_reply_delete(request, message_id):
    """حذف پاسخ صاحب سایت از زیر پیام «تماس با ما» (فقط سوپریوزر)."""
    if not _is_owner(request.user):
        raise PermissionDenied
    ContactReply.objects.filter(message_id=message_id).delete()
    messages.success(request, "پاسخ حذف شد.")
    return _back_to(f'contact-{message_id}')


@require_POST
def contact_message_delete(request, message_id):
    """حذف کامل یک پیام «تماس با ما» از صفحهٔ نظرات (فقط سوپریوزر)."""
    if not _is_owner(request.user):
        raise PermissionDenied
    ContactMessage.objects.filter(pk=message_id).delete()
    messages.success(request, "پیام حذف شد.")
    return redirect('testimonials')


@require_POST
def comment_delete(request, comment_id):
    """حذف کامل نظر یک غذا از صفحهٔ نظرات (فقط سوپریوزر)."""
    if not _is_owner(request.user):
        raise PermissionDenied
    Comment.objects.filter(pk=comment_id).delete()
    messages.success(request, "نظر حذف شد.")
    return redirect('testimonials')


def not_found(request):
    return render(request, '404.html', _cart_context(request))


@require_POST
def contact_send(request):
    """Receives the contact form (AJAX). Only logged-in customers can send a
    message; it is saved and shown in «مشتریان راضی چه می‌گویند»."""
    if not request.user.is_authenticated:
        return HttpResponse(
            '<div class="failed">برای ارسال پیام ابتدا باید '
            '<a href="/sign-in/?next=/contact/">وارد شوید</a> یا '
            '<a href="/sign-up/?next=/contact/">ثبت‌نام کنید</a>.</div>',
            status=401)
    # honeypot: ربات‌ها معمولاً این فیلد مخفی را پر می‌کنند
    if request.POST.get('website'):
        return HttpResponse('<div class="success">پیام شما ارسال شد.</div>')
    text = request.POST.get('message', '').strip()
    if not 3 <= len(text) <= 500:
        return HttpResponse(
            '<div class="failed">متن پیام باید بین ۳ تا ۵۰۰ حرف باشد.</div>',
            status=400)
    ContactMessage.objects.create(user=request.user, text=text[:500])
    return HttpResponse(format_html(
        '<div class="success">ممنون، {}! پیام شما با موفقیت ارسال شد و '
        'در بخش «مشتریان راضی چه می‌گویند» نمایش داده می‌شود.</div>',
        request.user.get_full_name() or request.user.username))


@require_POST
def cart_add(request, food_id):
    """Add a food to the cart, then go to the cart page."""
    try:
        Food.objects.get(pk=food_id, is_available=True)
    except Food.DoesNotExist:
        return redirect('cart')
    add_to_cart(request.session, food_id)
    return redirect('cart')


@require_POST
def cart_update(request, food_id):
    """Change quantity (+ / − buttons on the cart page) and re-render the page."""
    try:
        qty = int(request.POST.get('qty', '1'))
    except ValueError:
        qty = 1
    set_qty(request.session, food_id, qty)
    return redirect('cart')


@require_POST
def cart_remove(request, food_id):
    """Remove one line from the cart."""
    remove_from_cart(request.session, food_id)
    return redirect('cart')


def custom_404(request, exception):
    """Shown for unknown URLs when DEBUG = False."""
    return render(request, '404.html', _cart_context(request), status=404)