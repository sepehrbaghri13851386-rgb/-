from django.contrib import admin

from .models import Restaurant


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'rating', 'is_open', 'created_at')
    list_editable = ('is_open',)          # باز/بسته را مستقیم از لیست عوض کن
    list_filter = ('kind', 'is_open', 'categories')
    search_fields = ('name', 'description')
    filter_horizontal = ('categories', 'foods')