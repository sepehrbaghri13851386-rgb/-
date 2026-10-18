from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from .models import Comment, Food


def _comment_json(c):
    return {
        'name': c.name,
        'initial': c.name[:1],
        'text': c.text,
        'rating': c.rating,
        'time': c.time_ago,
    }


def _summary(food):
    agg = food.comments.filter(is_approved=True).aggregate(
        count=Count('id'), avg=Avg('rating'))
    return {'count': agg['count'], 'avg': round(agg['avg'] or 0, 1)}


@require_GET
def comment_list(request, food_id):
    food = get_object_or_404(Food, pk=food_id)
    comments = food.comments.filter(is_approved=True)[:50]
    return JsonResponse({
        'food': food.name,
        'comments': [_comment_json(c) for c in comments],
        **_summary(food),
    })


@require_POST
def comment_add(request, food_id):
    food = get_object_or_404(Food, pk=food_id)

    # honeypot: ربات‌ها معمولاً این فیلد مخفی را پر می‌کنند
    if request.POST.get('website'):
        return JsonResponse({'ok': True, 'comment': None, **_summary(food)})

    name = request.POST.get('name', '').strip()
    text = request.POST.get('text', '').strip()
    try:
        rating = int(request.POST.get('rating', 5))
    except ValueError:
        rating = 0

    errors = {}
    if not 2 <= len(name) <= 60:
        errors['name'] = 'نام باید بین ۲ تا ۶۰ حرف باشد.'
    if not 3 <= len(text) <= 500:
        errors['text'] = 'متن نظر باید بین ۳ تا ۵۰۰ حرف باشد.'
    if not 1 <= rating <= 5:
        errors['rating'] = 'امتیاز باید بین ۱ تا ۵ باشد.'
    if errors:
        return JsonResponse({'ok': False, 'errors': errors}, status=400)

    comment = Comment.objects.create(food=food, name=name, text=text, rating=rating)
    return JsonResponse({'ok': True, 'comment': _comment_json(comment), **_summary(food)})