# nazerat_app/models.py  (اپ جدید)
from django.conf import settings
from django.db import models


class ContactReply(models.Model):
    """پاسخ صاحب سایت (سوپریوزر) به یک پیام «تماس با ما» که در صفحهٔ نظرات نمایش داده می‌شود."""

    message = models.OneToOneField(
        'ghaza_app.ContactMessage', on_delete=models.CASCADE,
        related_name='owner_reply', verbose_name='پیام مشتری')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='contact_replies', verbose_name='پاسخ‌دهنده')
    author_name = models.CharField('نام پاسخ‌دهنده', max_length=150)
    text = models.TextField('متن پاسخ', max_length=500)
    created_at = models.DateTimeField('ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('ویرایش', auto_now=True)

    class Meta:
        verbose_name = 'پاسخ به پیام'
        verbose_name_plural = 'پاسخ به پیام‌ها'

    def __str__(self):
        return f'پاسخ به پیام #{self.message_id}'