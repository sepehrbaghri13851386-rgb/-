from django.conf import settings
from django.db import models
from django.utils import timezone

_FA_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
_UNITS = (('سال', 31536000), ('ماه', 2592000), ('هفته', 604800),
          ('روز', 86400), ('ساعت', 3600), ('دقیقه', 60))


def fa_time_ago(dt):
    """«۲ دقیقه پیش» / «۳ روز پیش» / «همین الان»"""
    secs = int((timezone.now() - dt).total_seconds())
    for label, size in _UNITS:
        if secs >= size:
            return f'{str(secs // size).translate(_FA_DIGITS)} {label} پیش'
    return 'همین الان'


class DetailCategory(models.Model):
    """دسته‌بندی؛ مثلاً «پیتزاها»، «ساندویچ‌ها»، «نوشیدنی‌ها»."""
    name = models.CharField('نام دسته‌بندی', max_length=80)
    order = models.PositiveIntegerField('ترتیب نمایش', default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'

    def __str__(self):
        return self.name


class DetailItem(models.Model):
    """یک مورد (مثلاً یک پیتزا) با عکس، توضیح و قیمت."""
    category = models.ForeignKey(DetailCategory, on_delete=models.PROTECT,
                                 related_name='items', verbose_name='دسته‌بندی')
    title = models.CharField('عنوان', max_length=150)
    description = models.TextField('توضیحات', blank=True)
    price = models.PositiveIntegerField('قیمت (تومان)', null=True, blank=True)
    image = models.ImageField('عکس اصلی', upload_to='goziyat/items/')
    is_available = models.BooleanField('نمایش در سایت', default=True)
    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'مورد'
        verbose_name_plural = 'موردها'

    def __str__(self):
        return self.title


class DetailImage(models.Model):
    """عکس‌های اضافهٔ گالری هر مورد."""
    item = models.ForeignKey(DetailItem, on_delete=models.CASCADE,
                             related_name='gallery', verbose_name='مورد')
    image = models.ImageField('عکس', upload_to='goziyat/gallery/')

    class Meta:
        verbose_name = 'عکس گالری'
        verbose_name_plural = 'عکس‌های گالری'

    def __str__(self):
        return f'{self.item.title} #{self.pk}'


class DetailComment(models.Model):
    """نظر کاربران واردشده دربارهٔ یک مورد."""
    item = models.ForeignKey(DetailItem, on_delete=models.CASCADE,
                             related_name='comments', verbose_name='مورد')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='goziyat_comments', verbose_name='کاربر')
    rating = models.PositiveSmallIntegerField('امتیاز (۱ تا ۵)', default=5)
    text = models.TextField('متن نظر', max_length=500)
    is_approved = models.BooleanField('تأیید شده (نمایش در سایت)', default=True)
    created_at = models.DateTimeField('تاریخ', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'نظر'
        verbose_name_plural = 'نظرها'

    def __str__(self):
        return f'{self.display_name} → {self.item.title}'

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.get_username()

    @property
    def time_ago(self):
        return fa_time_ago(self.created_at)


class DetailReply(models.Model):
    """پاسخ ادمین به یک نظر (برای هر نظر یک پاسخ)."""
    comment = models.OneToOneField(DetailComment, on_delete=models.CASCADE,
                                   related_name='reply', verbose_name='نظر')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                               on_delete=models.SET_NULL, editable=False)
    author_name = models.CharField('نام پاسخ‌دهنده', max_length=150, blank=True, editable=False)
    text = models.TextField('متن پاسخ', max_length=500)
    created_at = models.DateTimeField('تاریخ', auto_now_add=True)

    class Meta:
        verbose_name = 'پاسخ'
        verbose_name_plural = 'پاسخ‌ها'

    def __str__(self):
        return f'پاسخ به {self.comment}'

    @property
    def time_ago(self):
        return fa_time_ago(self.created_at)