from django.contrib import admin
from .models import (Category, Comment, CommentReply, ContactMessage, Food,
                     Profile, Order, OrderItem)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'discount_percent', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name',)
    list_editable = ('discount_percent', 'is_available')


class CommentReplyInline(admin.StackedInline):
    model = CommentReply
    extra = 0
    max_num = 1
    fields = ('author_name', 'text')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'food', 'rating', 'short_text', 'is_approved', 'has_reply', 'created_at')
    list_filter = ('is_approved', 'rating', 'food__category')
    search_fields = ('name', 'text', 'food__name')
    list_editable = ('is_approved',)
    date_hierarchy = 'created_at'
    inlines = [CommentReplyInline]
    actions = ['approve', 'hide']

    @admin.display(description="متن نظر")
    def short_text(self, obj):
        return obj.text[:50] + ('…' if len(obj.text) > 50 else '')

    @admin.display(description="پاسخ داده شد؟", boolean=True)
    def has_reply(self, obj):
        return hasattr(obj, 'reply')

    @admin.action(description="نمایش نظرهای انتخاب‌شده")
    def approve(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="مخفی کردن نظرهای انتخاب‌شده")
    def hide(self, request, queryset):
        queryset.update(is_approved=False)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'has_avatar')
    search_fields = ('user__username', 'user__email', 'phone')

    @admin.display(description="عکس دارد؟", boolean=True)
    def has_avatar(self, obj):
        return bool(obj.avatar)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'short_text', 'is_approved', 'created_at')
    list_filter = ('is_approved',)
    search_fields = ('user__username', 'user__first_name', 'user__email', 'text')
    list_editable = ('is_approved',)
    date_hierarchy = 'created_at'
    actions = ['approve', 'hide']

    @admin.display(description="متن پیام")
    def short_text(self, obj):
        return obj.text[:60] + ('…' if len(obj.text) > 60 else '')

    @admin.action(description="نمایش پیام‌های انتخاب‌شده")
    def approve(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="مخفی کردن پیام‌های انتخاب‌شده")
    def hide(self, request, queryset):
        queryset.update(is_approved=False)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ('name', 'qty', 'unit_price', 'line_total')
    readonly_fields = ('name', 'qty', 'unit_price', 'line_total')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """مدیریت سفارش‌ها؛ وضعیت را ادمین از همان لیست عوض می‌کند."""

    list_display = ('pk', 'user', 'short_address', 'total_toman',
                    'status', 'payment', 'created_at')
    list_editable = ('status',)
    list_display_links = ('pk', 'user')
    list_filter = ('status', 'payment', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name',
                     'phone', 'address', 'recipient')
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    readonly_fields = ('created_at',)

    @admin.display(description='آدرس')
    def short_address(self, obj):
        return obj.address_line

    @admin.display(description='مبلغ نهایی')
    def total_toman(self, obj):
        return f'{obj.total:,} تومان'