"""
URL configuration for restoran_asli.

URL                     view                       name
/                       views.index                index
/about/                 views.about                about
/search/                views.search               search         (?q=&scope=&cat=)
/restaurants/           views.restaurants          restaurants
/restaurant-details/    views.restaurant_details   restaurant_details
/cart/                  views.cart                 cart
/cart/add/<id>/         views.cart_add             cart_add       (POST)
/cart/update/<id>/      views.cart_update          cart_update    (POST)
/cart/remove/<id>/      views.cart_remove          cart_remove    (POST)
/checkout/              views.checkout             checkout
/checkout-step2/        views.checkout_step2       checkout_step2
/checkout-step3/        views.checkout_step3       checkout_step3
/contact/               views.contact              contact
/contact/send/          views.contact_send         contact_send   (POST, AJAX)
/foods/<id>/comments/       comment_views.comment_list  comment_list  (GET, JSON)
/foods/<id>/comments/add/   comment_views.comment_add   comment_add   (POST, AJAX)
/faqs/                  views.faqs                 faqs
/profile/               views.profile              profile
/blog/                  views.blog1                blog1
/blog2/                 views.blog2                blog2
/blog-single/           views.blog_single          blog_single
/sign-in/               views.sign_in              sign_in
/sign-up/               views.sign_up              sign_up
/sign-out/              views.sign_out             sign_out       (POST link)
/profile/               views.profile_edit         profile        (login required)
/testimonials/<id>/reply/         views.reply_add            reply_add            (POST, superuser)
/testimonials/<id>/reply/delete/  views.reply_delete         reply_delete         (POST, superuser)
/testimonials/contact/<id>/reply/         views.contact_reply_add     contact_reply_add     (POST, superuser)
/testimonials/contact/<id>/reply/delete/  views.contact_reply_delete  contact_reply_delete  (POST, superuser)
/testimonials/contact/<id>/delete/        views.contact_message_delete  contact_message_delete (POST, superuser)
/testimonials/<id>/delete/                views.comment_delete        comment_delete        (POST, superuser)
/404/                   views.not_found            not_found
/admin/                 Django admin
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from ghaza_app import views as comment_views
from GOZIYAT_APP import views as goz
from blog_app import views as blog_views
from restoran_app import views as rest_views
handler404 = 'restoran_asli.views.custom_404'

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    # --- جستجوی بخش‌محور: scope=food | item | all و ?cat=<id> برای کل یک دسته ---
    path('search/', views.search, name='search'),
    # --- رستوران‌ها (restoran_app): لیست + فیلتر، و مدیریت فقط برای سوپریوزر ---
    path('restaurants/', rest_views.restaurant_list, name='restaurants'),
    path('restaurants/add/', rest_views.restaurant_create, name='restaurant_add'),
    path('restaurants/<int:pk>/', rest_views.restaurant_detail, name='restaurant_detail'),
    path('restaurants/<int:pk>/edit/', rest_views.restaurant_edit, name='restaurant_edit'),
    path('restaurants/<int:pk>/toggle/', rest_views.restaurant_toggle, name='restaurant_toggle'),
    path('restaurants/<int:pk>/delete/', rest_views.restaurant_delete, name='restaurant_delete'),
    # --- جزئیات (GOZIYAT_APP): لیست، دسته‌بندی، صفحهٔ مورد، نظر و پاسخ ---
    path('restaurant-details/', goz.details_list, name='restaurant_details'),
    path('restaurant-details/category/<int:category_id>/', goz.details_list, name='details_category'),
    path('restaurant-details/item/<int:pk>/', goz.details_item, name='details_item'),
    path('restaurant-details/item/<int:pk>/comment/', goz.comment_add, name='details_comment_add'),
    path('restaurant-details/comment/<int:comment_id>/reply/', goz.reply_add, name='details_reply_add'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:food_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:food_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:food_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout-step2/', views.checkout_step2, name='checkout_step2'),
    path('checkout-step3/', views.checkout_step3, name='checkout_step3'),
    path('contact/', views.contact, name='contact'),
    path('contact/send/', views.contact_send, name='contact_send'),
    path('foods/<int:food_id>/comments/', comment_views.comment_list, name='comment_list'),
    path('foods/<int:food_id>/comments/add/', comment_views.comment_add, name='comment_add'),
    path('faqs/', views.faqs, name='faqs'),
    path('profile/', views.profile_edit, name='profile'),
    path('blog/', blog_views.blog_list, name='blog1'),
    path('blog/add/', blog_views.blog_create, name='blog_create'),
    path('blog/<int:pk>/', blog_views.blog_detail, name='blog_detail'),
    path('blog/<int:pk>/edit/', blog_views.blog_edit, name='blog_edit'),
    path('blog/<int:pk>/delete/', blog_views.blog_delete, name='blog_delete'),
    path('blog/<int:pk>/comment/', blog_views.comment_add, name='blog_comment_add'),
    path('blog/comment/<int:comment_id>/reply/', blog_views.reply_add, name='blog_reply_add'),
    path('blog/comment/<int:comment_id>/delete/', blog_views.comment_delete, name='blog_comment_delete'),
    path('blog/reply/<int:reply_id>/delete/', blog_views.reply_delete, name='blog_reply_delete'),
    # لینک‌های قدیمی منو (برای جلوگیری از NoReverseMatch) -> همان صفحهٔ بلاگ جدید
    path('blog2/', blog_views.blog_list, name='blog2'),
    path('blog-single/', blog_views.blog_list, name='blog_single'),
    path('sign-in/', views.sign_in, name='sign_in'),
    path('sign-up/', views.sign_up, name='sign_up'),
    path('sign-out/', views.sign_out, name='sign_out'),
    path('testimonials/', views.testimonials, name='testimonials'),
    path('testimonials/<int:comment_id>/reply/', views.reply_add, name='reply_add'),
    path('testimonials/<int:comment_id>/reply/delete/', views.reply_delete, name='reply_delete'),
    path('testimonials/contact/<int:message_id>/reply/', views.contact_reply_add, name='contact_reply_add'),
    path('testimonials/contact/<int:message_id>/reply/delete/', views.contact_reply_delete, name='contact_reply_delete'),
    path('testimonials/contact/<int:message_id>/delete/', views.contact_message_delete, name='contact_message_delete'),
    path('testimonials/<int:comment_id>/delete/', views.comment_delete, name='comment_delete'),
    path('404/', views.not_found, name='not_found'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)