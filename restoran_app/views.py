from functools import wraps

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from ghaza_app.cart import cart_details
from ghaza_app.models import Category

from .forms import RestaurantForm
from .models import Restaurant

PAGE_SIZE = 8


def _cart_context(request):
    items, totals = cart_details(request.session)
    return {'cart_items': items, 'cart_totals': totals}


def superuser_required(view):
    """فقط سوپریوزر (ادمین سایت) اجازه دارد."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('sign_in')}?next={request.path}")
        if not request.user.is_superuser:
            messages.error(request, 'فقط ادمین سایت می‌تواند رستوران‌ها را مدیریت کند.')
            return redirect('restaurants')
        return view(request, *args, **kwargs)
    return wrapper


def _back(request):
    """برگشت به همان صفحه (با فیلترها) بعد از تغییر باز/بسته."""
    nxt = request.POST.get('next', '')
    if nxt and url_has_allowed_host_and_scheme(
            nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(nxt)
    return redirect('restaurants')


def restaurant_list(request):
    """لیست رستوران‌ها + فیلتر چندتایی: ?cat=1&cat=2 -> رستورانی که هر دو دسته را دارد."""
    selected_ids = []
    for value in request.GET.getlist('cat'):
        if value.isdigit() and int(value) not in selected_ids:
            selected_ids.append(int(value))

    qs = Restaurant.objects.prefetch_related('categories')
    for cid in selected_ids:              # هر filter یک شرط AND جدا می‌سازد
        qs = qs.filter(categories__pk=cid)

    page_obj = Paginator(qs, PAGE_SIZE).get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'selected_ids': selected_ids,
        'qs': ''.join(f'cat={i}&' for i in selected_ids),   # برای لینک‌های صفحه‌بندی
        'is_owner': request.user.is_authenticated and request.user.is_superuser,
    }
    context.update(_cart_context(request))
    return render(request, 'restaurants.html', context)


def restaurant_detail(request, pk):
    """صفحه‌ی جزئیات رستوران: عکس، توضیحات، آدرس و غذاهای ثبت‌شده برای آن."""
    restaurant = get_object_or_404(
        Restaurant.objects.prefetch_related('categories'), pk=pk)
    foods = (restaurant.foods.filter(is_available=True)
             .select_related('category'))
    context = {
        'restaurant': restaurant,
        'foods': foods,
        'is_owner': request.user.is_authenticated and request.user.is_superuser,
    }
    context.update(_cart_context(request))
    return render(request, 'restaurant_detail.html', context)


@superuser_required
def restaurant_create(request):
    form = RestaurantForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'رستوران اضافه شد.')
        return redirect('restaurants')
    context = {'form': form, 'is_edit': False}
    context.update(_cart_context(request))
    return render(request, 'restaurant_form.html', context)


@superuser_required
def restaurant_edit(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    form = RestaurantForm(request.POST or None, request.FILES or None, instance=restaurant)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'تغییرات ذخیره شد.')
        return redirect('restaurants')
    context = {'form': form, 'is_edit': True, 'restaurant': restaurant}
    context.update(_cart_context(request))
    return render(request, 'restaurant_form.html', context)


@superuser_required
@require_POST
def restaurant_toggle(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    restaurant.is_open = not restaurant.is_open
    restaurant.save(update_fields=['is_open'])
    state = 'باز' if restaurant.is_open else 'بسته'
    messages.success(request, f'«{restaurant.name}» اکنون {state} است.')
    return _back(request)


@superuser_required
@require_POST
def restaurant_delete(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    name = restaurant.name
    restaurant.delete()
    messages.success(request, f'«{name}» حذف شد.')
    return _back(request)