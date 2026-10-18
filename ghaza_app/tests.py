"""تست‌های جستجوی بخش‌محور سایت (ویو restoran_asli.views.search)."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ghaza_app.models import Category, Food, Profile
from GOZIYAT_APP.models import DetailCategory, DetailItem


class SiteSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pizza = Category.objects.create(name='پیتزا', slug='pizza', order=1)
        cls.meat = Category.objects.create(name='گوشت و استیک', slug='meat', order=2)
        cls.dessert = DetailCategory.objects.create(name='دسرها', order=1)

        # دستهٔ پیتزا سه غذا دارد؛ فقط یکی‌شان «پیتزا» در نامش است
        cls.pizza_pepperoni = Food.objects.create(
            category=cls.pizza, name='پیتزا پپرونی', price=180000,
            description='با پنیر موزارلا', image='foods/1.jpg')
        cls.pizza_veg = Food.objects.create(
            category=cls.pizza, name='پیتزا سبزیجات', price=150000,
            description='تازه و گیاهی', image='foods/2.jpg')
        cls.pizza_margh = Food.objects.create(
            category=cls.pizza, name='مارگاریتا', price=160000,
            description='گوجه و ریحان', image='foods/3.jpg')
        cls.steak = Food.objects.create(
            category=cls.meat, name='استیک گریل', price=420000,
            description='با سس قارچ', image='foods/4.jpg')

        cls.cake = DetailItem.objects.create(
            category=cls.dessert, title='کیک شکلاتی', price=90000,
            description='دسر خانگی', image='goziyat/items/1.jpg')
        cls.tiramisu = DetailItem.objects.create(
            category=cls.dessert, title='تیرامیسو', price=120000,
            description='با قهوه', image='goziyat/items/2.jpg')

    def search(self, **params):
        return self.client.get(reverse('search'), params)

    def group_names(self, response, key):
        """نام دسته‌بندی‌های گروه‌های نتیجه، به ترتیب نمایش."""
        return [g['category'].name for g in response.context[key]]

    def group_items(self, response, key, index=0):
        return response.context[key][index]['items']

    # ------------------------------------------------------------------ scope
    def test_food_scope_searches_only_home_page_foods(self):
        res = self.search(q='استیک', scope='food')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.group_items(res, 'food_groups'), [self.steak])
        self.assertEqual(res.context['item_groups'], [])
        self.assertEqual(res.context['item_total'], 0)

    def test_item_scope_searches_only_restaurant_menu(self):
        res = self.search(q='تیرامیسو', scope='item')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.group_items(res, 'item_groups'), [self.tiramisu])
        self.assertEqual(res.context['food_groups'], [])
        self.assertEqual(res.context['food_total'], 0)

    def test_all_scope_searches_every_section(self):
        res = self.search(q='پیتزا', scope='all')
        self.assertTrue(res.context['food_groups'])
        self.assertEqual(res.context['item_groups'], [])

    def test_unknown_scope_falls_back_to_all(self):
        res = self.search(q='استیک', scope='whatever')
        self.assertEqual(res.context['scope'], 'all')
        self.assertEqual(res.context['food_total'], 1)

    # ------------------------------------------------- دسته‌بندی = کل دسته
    def test_category_name_query_returns_the_entire_category(self):
        """جستجوی نام دسته، همهٔ غذاهای آن دسته را برمی‌گرداند — نه فقط هم‌نام‌ها."""
        res = self.search(q='پیتزا', scope='food')
        self.assertEqual(len(res.context['food_groups']), 1)
        group = res.context['food_groups'][0]
        self.assertTrue(group['match'])
        self.assertCountEqual(
            group['items'], [self.pizza_pepperoni, self.pizza_veg, self.pizza_margh])
        # «استیک» که در دستهٔ دیگری است نباید بیاید
        self.assertNotIn(self.steak, group['items'])

    def test_whole_category_comes_before_partial_matches(self):
        res = self.search(q='استیک', scope='food')
        self.assertEqual(self.group_names(res, 'food_groups'),
                         ['گوشت و استیک'])

    def test_cat_param_returns_the_entire_category_without_query(self):
        res = self.search(cat=self.pizza.pk, scope='food')
        self.assertEqual(self.group_items(res, 'food_groups'),
                         [self.pizza_pepperoni, self.pizza_veg, self.pizza_margh])
        self.assertEqual(res.context['cat_name'], 'پیتزا')
        self.assertTrue(res.context['searched'])

    def test_cat_param_expands_whole_menu_category(self):
        res = self.search(cat=self.dessert.pk, scope='item')
        self.assertCountEqual(self.group_items(res, 'item_groups'),
                              [self.cake, self.tiramisu])
        self.assertEqual(res.context['food_groups'], [])

    def test_category_slug_is_searchable(self):
        res = self.search(q='meat', scope='food')
        self.assertEqual(self.group_names(res, 'food_groups'), ['گوشت و استیک'])

    # ------------------------------------------------------------ نوشتار فارسی
    def test_persian_letter_variants_match(self):
        """جستجو با «ي/ك» عربی هم باید متن «ی/ک» فارسی را پیدا کند."""
        res = self.search(q='پيتزا', scope='food')   # ی عربی
        self.assertEqual(len(res.context['food_groups']), 1)
        res = self.search(q='شکلاتي', scope='item')  # ی عربی در توضیح/عنوان
        self.assertEqual(self.group_items(res, 'item_groups'), [self.cake])

    def test_description_is_searchable(self):
        res = self.search(q='موزارلا', scope='food')
        self.assertEqual(self.group_items(res, 'food_groups'), [self.pizza_pepperoni])

    # --------------------------------------------------------------- خالی/خطا
    def test_no_query_shows_nothing_and_hints(self):
        res = self.search(scope='all')
        self.assertEqual(res.context['result_total'], 0)
        self.assertFalse(res.context['searched'])
        self.assertContains(res, 'عبارت مورد نظرتان را بنویسید')

    def test_no_match_shows_empty_state(self):
        res = self.search(q='ززززز', scope='all')
        self.assertEqual(res.context['result_total'], 0)
        self.assertTrue(res.context['searched'])
        self.assertContains(res, 'چیزی پیدا نشد')

    def test_long_query_is_trimmed(self):
        res = self.search(q='ا' * 500, scope='all')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['q']), 80)

    # ------------------------------------------------------------- فرم‌های سایت
    def test_every_page_search_form_targets_the_search_view(self):
        wired = ['index', 'about', 'cart', 'checkout', 'checkout_step2',
                 'checkout_step3', 'contact', 'faqs', 'blog1', 'blog2',
                 'blog_single', 'sign_in', 'sign_up', 'testimonials',
                 'restaurant_details', 'restaurants', 'not_found']
        for name in wired:
            with self.subTest(page=name):
                res = self.client.get(reverse(name))
                self.assertEqual(res.status_code, 200)
                self.assertContains(res, 'action="/search/"')
                self.assertContains(res, 'name="q"')

    def test_profile_search_form_targets_the_search_view(self):
        """صفحهٔ پروفایل فقط برای کاربر واردشده باز می‌شود."""
        User.objects.create_user(username='sara', password='pass-12345')
        self.client.login(username='sara', password='pass-12345')
        res = self.client.get(reverse('profile'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'action="/search/"')
        self.assertContains(res, 'name="q"')

    def test_home_page_search_is_scoped_to_foods(self):
        res = self.client.get(reverse('index'))
        self.assertContains(res, '<input type="hidden" name="scope" value="food">')

    def test_restaurant_details_search_is_scoped_to_menu(self):
        res = self.client.get(reverse('restaurant_details'))
        self.assertContains(res, '<input type="hidden" name="scope" value="item">')

    def test_categories_are_offered_as_chips(self):
        res = self.search(scope='all')
        self.assertContains(res, f'?cat={self.pizza.pk}&amp;scope=food')
        self.assertContains(res, f'?cat={self.dessert.pk}&amp;scope=item')

class ProfilePageTests(TestCase):
    """صفحهٔ پروفایل: ویرایش اطلاعات، بارگذاری آواتار و تغییر رمز عبور."""

    def setUp(self):
        import tempfile
        from django.test import override_settings

        # فایل آواتار تستی در یک پوشهٔ موقت می‌رود تا media/ واقعی کثیف نشود
        self._media = tempfile.TemporaryDirectory()
        self._override = override_settings(MEDIA_ROOT=self._media.name)
        self._override.enable()
        self.addCleanup(self._override.disable)
        self.addCleanup(self._media.cleanup)

        # کاربر قدیمی که سیگنال برایش سطر Profile نساخته است (مثل sepi در دیتابیس واقعی)
        self.user = User.objects.create_user(username='sepideh', password='old-pass-123')
        Profile.objects.filter(user=self.user).delete()
        self.client.force_login(self.user)

    def _png(self):
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image

        buf = BytesIO()
        Image.new('RGB', (32, 32), (200, 120, 40)).save(buf, format='PNG')
        return SimpleUploadedFile('a.png', buf.getvalue(), content_type='image/png')

    def test_user_without_profile_saves_avatar_without_error(self):
        """ثبت‌نام‌های قدیمی باید بتوانند عکس پروفایل بگذارند (قبلاً IntegrityError می‌داد)."""
        res = self.client.post(reverse('profile'), {'save_avatar': '1', 'avatar': self._png()})
        self.assertEqual(res.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile.avatar.name)

    def test_edit_info_updates_user_and_phone(self):
        res = self.client.post(reverse('profile'), {
            'first_name': 'نیلوفر', 'last_name': 'احمدی',
            'email': 'n@example.com', 'phone': '09120000000'})
        self.assertEqual(res.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'نیلوفر')
        self.assertEqual(self.user.profile.phone, '09120000000')

    def test_change_password_requires_correct_current_password(self):
        bad = self.client.post(reverse('profile'), {
            'change_password': '1', 'old_password': 'WRONG',
            'new_password1': 'new-pass-123', 'new_password2': 'new-pass-123'})
        self.assertEqual(bad.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('old-pass-123'))

        ok = self.client.post(reverse('profile'), {
            'change_password': '1', 'old_password': 'old-pass-123',
            'new_password1': 'new-pass-123', 'new_password2': 'new-pass-123'})
        self.assertEqual(ok.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new-pass-123'))
