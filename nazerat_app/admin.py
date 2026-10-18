# nazerat_app/admin.py  (اپ جدید)
from django.contrib import admin

from .models import ContactReply


@admin.register(ContactReply)
class ContactReplyAdmin(admin.ModelAdmin):
    list_display = ('message', 'author_name', 'short_text', 'updated_at')
    search_fields = ('text', 'author_name')
    autocomplete_fields = ()

    @admin.display(description='متن')
    def short_text(self, obj):
        return obj.text[:60]