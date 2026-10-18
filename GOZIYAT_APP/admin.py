from django.contrib import admin

from .models import (DetailCategory, DetailComment, DetailImage, DetailItem,
                     DetailReply)


@admin.register(DetailCategory)
class DetailCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'item_count')
    list_editable = ('order',)

    @admin.display(description='تعداد موردها')
    def item_count(self, obj):
        return obj.items.count()


class DetailImageInline(admin.TabularInline):
    model = DetailImage
    extra = 2


@admin.register(DetailItem)
class DetailItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'is_available', 'created_at')
    list_filter = ('category', 'is_available')
    list_editable = ('is_available',)
    search_fields = ('title', 'description')
    inlines = [DetailImageInline]


class DetailReplyInline(admin.StackedInline):
    model = DetailReply
    extra = 1
    max_num = 1
    can_delete = True
    verbose_name = 'پاسخ ادمین'
    verbose_name_plural = 'پاسخ ادمین'


@admin.register(DetailComment)
class DetailCommentAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'item', 'rating', 'short_text', 'has_reply',
                    'is_approved', 'created_at')
    list_filter = ('is_approved', 'item__category', 'rating')
    list_editable = ('is_approved',)
    search_fields = ('text', 'user__username', 'item__title')
    readonly_fields = ('item', 'user', 'rating', 'text', 'created_at')
    inlines = [DetailReplyInline]

    @admin.display(description='متن')
    def short_text(self, obj):
        return obj.text[:50]

    @admin.display(description='پاسخ داده شده', boolean=True)
    def has_reply(self, obj):
        return hasattr(obj, 'reply')

    def has_add_permission(self, request):
        return False  # نظرها فقط از سایت ثبت می‌شوند

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for obj in instances:
            if isinstance(obj, DetailReply):
                obj.author = request.user
                obj.author_name = request.user.get_full_name() or request.user.get_username()
            obj.save()
        formset.save_m2m()