from django.contrib import admin
from django.utils.html import format_html

from .models import BlogPost, BlogComment, BlogReply


class BlogReplyInline(admin.TabularInline):
    model = BlogReply
    extra = 1
    fields = ('text', 'user', 'created_at')
    readonly_fields = ('created_at',)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if not obj.user_id:
                obj.user = request.user
            obj.save()
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'title', 'author', 'created_at')
    list_display_links = ('thumb', 'title')
    search_fields = ('title', 'description')
    readonly_fields = ('author', 'created_at')

    @admin.display(description='عکس')
    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:50px;border-radius:6px">', obj.image.url)
        return '-'

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'user', 'post', 'created_at', 'reply_count')
    list_filter = ('post',)
    search_fields = ('text',)
    inlines = [BlogReplyInline]

    @admin.display(description='نظر')
    def short_text(self, obj):
        return obj.text[:50]

    @admin.display(description='تعداد پاسخ')
    def reply_count(self, obj):
        return obj.replies.count()