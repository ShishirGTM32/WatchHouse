from django.urls import path
from . import views
from django.contrib.auth.views import PasswordResetDoneView
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='LogIn'),
    path('register/', views.RegisterPage.as_view(), name='Register'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('password_reset_done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('logout/', views.CustomLogoutView.as_view(), name='LogOut'),
    path('password-reset-confirm/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Homepage and static pages
    path('', views.Home.as_view(), name='Home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('account/', views.AccountView.as_view(), name='account'),
    path('orders/', views.ViewOrdersView.as_view(), name='view_orders'),

    # Shop and Cart
    path('shop/', views.ShopView.as_view(), name='shop'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:watch_id>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/clear/', views.ClearCartView.as_view(), name='clear_cart'),
    path('cart/update/<int:watch_id>/<str:action>/', views.UpdateQuantityView.as_view(), name='update_quantity'),
    path('cart/remove/<int:watch_id>/', views.RemoveItemView.as_view(), name='remove_item'),


    path('shipping-details/', views.ShippingDetailsView.as_view(), name='checkout'),
    path('success/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('cancelled/', views.PaymentCancelledView.as_view(), name='payment_cancelled'),
    path('stripe/webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
