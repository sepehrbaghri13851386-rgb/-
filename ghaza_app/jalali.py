"""تبدیل تاریخ میلادی به شمسی (جلالی) برای نمایش فارسیِ تاریخ سفارش‌ها."""


def to_jalali(gy, gm, gd):
    """Gregorian (gy, gm, gd) → Jalali (jy, jm, jd)."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) \
        + ((gy2 + 399) // 400) - 80 + gd + g_d_m[gm - 1]
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
          'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']

_FA_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def fa_digits(text):
    """تبدیل ارقام انگلیسیِ یک رشته به فارسی."""
    return str(text).translate(_FA_DIGITS)


def jalali_date_str(gy, gm, gd):
    """«۲ خرداد ۱۳۹۹» — تاریخ شمسیِ فارسی بدون صفر ابتدایی."""
    jy, jm, jd = to_jalali(gy, gm, gd)
    return f'{fa_digits(jd)} {MONTHS[jm - 1]} {fa_digits(jy)}'
