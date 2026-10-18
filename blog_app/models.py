from django.conf import settings
from django.db import models
from django.urls import reverse


class BlogPost(models.Model):
    title = models.CharField('نام / عنوان', max_length=200)
    image = models.ImageField('عکس', upload_to='blog/')
    description = models.TextField('توضیحات')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='نویسنده',
        null=True, blank=True, on_delete=models.SET_NULL, related_name='blog_posts',
    )
    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'بلاگ'
        verbose_name_plural = 'بلاگ‌ها'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog_detail', args=[self.pk])


class BlogComment(models.Model):
    post = models.ForeignKey(BlogPost, verbose_name='بلاگ', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='کاربر',
        null=True, blank=True, on_delete=models.SET_NULL, related_name='blog_comments',
    )
    text = models.TextField('متن نظر', max_length=1000)
    created_at = models.DateTimeField('تاریخ', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'نظر بلاگ'
        verbose_name_plural = 'نظرات بلاگ'

    def __str__(self):
        return f'{self.display_name}: {self.text[:30]}'

    @property
    def display_name(self):
        if not self.user:
            return 'کاربر حذف‌شده'
        return self.user.get_full_name() or self.user.get_username()


class BlogReply(models.Model):
    comment = models.ForeignKey(BlogComment, verbose_name='نظر', on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='پاسخ‌دهنده',
        null=True, blank=True, on_delete=models.SET_NULL, related_name='blog_replies',
    )
    text = models.TextField('متن پاسخ', max_length=1000)
    created_at = models.DateTimeField('تاریخ', auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'پاسخ'
        verbose_name_plural = 'پاسخ‌ها'

    def __str__(self):
        return self.text[:40]