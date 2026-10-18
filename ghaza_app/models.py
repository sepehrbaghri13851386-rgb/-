from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.timesince import timesince


class Category(models.Model):
    name = models.CharField("نام دسته‌بندی", max_length=100)
    slug = models.SlugField("شناسه (انگلیسی)", unique=True,
                            help_text="مثلاً: pizza, meat, sushi, fastfood, vegitarian")
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        return self.name


class Food(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 related_name='foods', verbose_name="دسته‌بندی")
    name = models.CharField("نام غذا", max_length=200)
    description = models.TextField("توضیحات", blank=True)
    price = models.PositiveIntegerField("قیمت (تومان)")
    discount_percent = models.PositiveSmallIntegerField(
        "درصد تخفیف", null=True, blank=True,
        validators=[MaxValueValidator(99)],
        help_text="اختیاری. مثلاً 20 یعنی ۲۰٪ تخفیف. اگه خالی یا 0 باشه، تخفیفی نمایش داده نمیشه.")
    image = models.ImageField("عکس", upload_to='foods/')
    is_available = models.BooleanField("موجود است", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "غذا"
        verbose_name_plural = "غذاها"

    def __str__(self):
        return self.name

    @property
    def has_discount(self):
        return bool(self.discount_percent)

    @property
    def final_price(self):
        if self.has_discount:
            return round(self.price * (100 - self.discount_percent) / 100)
        return self.price


class Profile(models.Model):
    """Extra per-user info (phone, avatar). Created automatically for every user."""

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='profile', verbose_name="کاربر")
    phone = models.CharField("شماره تماس", max_length=15, blank=True)
    avatar = models.ImageField("عکس پروفایل", upload_to='avatars/',
                               blank=True, null=True)

    class Meta:
        verbose_name = "پروفایل"
        verbose_name_plural = "پروفایل‌ها"

    def __str__(self):
        return f"پروفایل {self.user.username}"


def create_user_profile(sender, instance, created, **kwargs):
    """Make sure every User always has a Profile row."""
    if created:
        Profile.objects.create(user=instance)


models.signals.post_save.connect(create_user_profile, sender=User)


class Comment(models.Model):
    food = models.ForeignKey(Food, on_delete=models.CASCADE,
                             related_name='comments', verbose_name="غذا")
    name = models.CharField("نام", max_length=60)
    text = models.TextField("متن نظر", max_length=500)
    rating = models.PositiveSmallIntegerField(
        "امتیاز", default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)])
    is_approved = models.BooleanField(
        "نمایش داده شود", default=True,
        help_text="برای مخفی کردن نظرهای نامناسب، این تیک را بردارید.")
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "نظر"
        verbose_name_plural = "نظرها"

    def __str__(self):
        return f"{self.name} ← {self.food.name}"

    @property
    def time_ago(self):
        if (timezone.now() - self.created_at).total_seconds() < 60:
            return "همین حالا"
        first = timesince(self.created_at).split(',')[0].split('،')[0]
        return f"{first.strip()} پیش"


class ContactMessage(models.Model):
    """Message a logged-in customer sent from the «تماس با ما» page.
    Approved messages are shown in the «مشتریان راضی چه می‌گویند» section."""

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='contact_messages', verbose_name="کاربر")
    text = models.TextField("متن پیام", max_length=500)
    is_approved = models.BooleanField(
        "نمایش داده شود", default=True,
        help_text="پیام‌های تأییدشده در صفحه «نظرات مشتریان» نمایش داده می‌شوند.")
    created_at = models.DateTimeField("تاریخ ارسال", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"

    def __str__(self):
        return f"پیام {self.user.username}"

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def time_ago(self):
        if (timezone.now() - self.created_at).total_seconds() < 60:
            return "همین حالا"
        first = timesince(self.created_at).split(',')[0].split('،')[0]
        return f"{first.strip()} پیش"


class CommentReply(models.Model):
    """Owner / superuser answer to a customer comment."""

    comment = models.OneToOneField(Comment, on_delete=models.CASCADE,
                                   related_name='reply', verbose_name="نظر")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                               related_name='comment_replies', verbose_name="پاسخ‌دهنده")
    author_name = models.CharField("نام نمایشی", max_length=80, default="مدیر رستوران")
    text = models.TextField("متن پاسخ", max_length=500)
    created_at = models.DateTimeField("تاریخ پاسخ", auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "پاسخ نظر"
        verbose_name_plural = "پاسخ‌های نظرها"

    def __str__(self):
        return f"پاسخ به {self.comment}"


class Order(models.Model):
    """سفارش ثبت‌شدهٔ کاربر (از سبد خرید در مرحلهٔ پرداخت).

    وضعیت را ادمین از پنل مدیریت تغییر می‌دهد.
    """

    STATUS_DOING = 'doing'
    STATUS_DONE = 'done'
    STATUS_CHOICES = [
        (STATUS_DOING, 'در حال انجام'),
        (STATUS_DONE, 'انجام شد'),
    ]
    PAYMENT_CHOICES = [
        ('card_to_card', 'کارت به کارت'),
        ('gateway', 'کارت بانکی (درگاه)'),
        ('cash', 'پرداخت در محل'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='orders', verbose_name='کاربر')
    recipient = models.CharField('نام گیرنده', max_length=120, blank=True)
    phone = models.CharField('تلفن تماس', max_length=15)
    city = models.CharField('شهر', max_length=80)
    address = models.TextField('آدرس تحویل')
    when = models.CharField('زمان تحویل', max_length=80, blank=True)
    note = models.TextField('یادداشت سفارش', blank=True)
    payment = models.CharField('روش پرداخت', max_length=20,
                               choices=PAYMENT_CHOICES, default='gateway')
    subtotal = models.PositiveIntegerField('جمع جزء')
    delivery_fee = models.PositiveIntegerField('هزینه ارسال', default=0)
    total = models.PositiveIntegerField('مبلغ نهایی')
    status = models.CharField('وضعیت', max_length=20,
                              choices=STATUS_CHOICES, default=STATUS_DOING)
    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)

    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارش‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return f'سفارش #{self.pk} — {self.user.username}'

    @property
    def date_fa(self):
        """تاریخ ثبت به شمسی، برای نمایش در پروفایل («۲ خرداد ۱۳۹۹»)."""
        from django.utils import timezone as tz
        from .jalali import jalali_date_str
        try:
            d = tz.localtime(self.created_at)
        except Exception:
            d = self.created_at
        return jalali_date_str(d.year, d.month, d.day)

    @property
    def address_line(self):
        return f'{self.city}، {self.address}'


class OrderItem(models.Model):
    """یک ردیف از سفارش؛ نام و قیمت لحظهٔ ثبت ذخیره می‌شود."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              related_name='items', verbose_name='سفارش')
    name = models.CharField('نام غذا', max_length=200)
    qty = models.PositiveIntegerField('تعداد', default=1)
    unit_price = models.PositiveIntegerField('قیمت واحد')

    class Meta:
        verbose_name = 'ردیف سفارش'
        verbose_name_plural = 'ردیف‌های سفارش'
        ordering = ['pk']

    def __str__(self):
        return f'{self.name} × {self.qty}'

    @property
    def line_total(self):
        return self.qty * self.unit_price