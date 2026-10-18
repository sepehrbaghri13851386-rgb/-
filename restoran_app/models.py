from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Restaurant(models.Model):
    """رستوران / کافه‌ای که ادمین (سوپریوزر) اضافه می‌کند و در /restaurants/ نمایش داده می‌شود."""

    KIND_CHOICES = [
        ('restaurant', 'رستوران'),
        ('cafe', 'کافه'),
        ('pub', 'پاب'),
        ('fastfood', 'فست‌فود'),
        ('asian', 'غذای آسیایی'),
    ]

    name = models.CharField("نام", max_length=150)
    kind = models.CharField("نوع", max_length=20, choices=KIND_CHOICES,
                            default='restaurant')
    description = models.TextField("توضیحات", blank=True)
    address = models.TextField("آدرس", blank=True)
    image = models.ImageField("عکس اصلی", upload_to='restaurants/',
                              blank=True, null=True)
    logo = models.ImageField("لوگو (اختیاری)", upload_to='restaurants/logos/',
                             blank=True, null=True,
                             help_text="اگر خالی باشد، از عکس اصلی استفاده می‌شود.")
    # منوی رستوران = دسته‌بندی‌هایی که دارد (همان دسته‌های اپ غذا)
    categories = models.ManyToManyField('ghaza_app.Category', blank=True,
                                        related_name='restaurants',
                                        verbose_name="دسته‌بندی‌های منو")
    # غذاهایی که برای همین رستوران ثبت می‌کنیم (در صفحه‌ی جزئیات نمایش داده می‌شوند)
    foods = models.ManyToManyField('ghaza_app.Food', blank=True,
                                   related_name='restaurants',
                                   verbose_name="غذاهای این رستوران")
    rating = models.PositiveSmallIntegerField(
        "امتیاز (۱ تا ۵)", default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)])
    is_open = models.BooleanField("الان باز است", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "رستوران"
        verbose_name_plural = "رستوران‌ها"

    def __str__(self):
        return self.name

    @property
    def stars(self):
        return range(self.rating)