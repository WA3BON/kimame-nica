# shop/urls.py
from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    CartView,
    AddToCartView,
    UpdateCartItemView,
    RemoveFromCartView,
    CheckoutView,
    CheckoutSuccessView,
    CheckoutCancelView,
    StripeWebhookView,
    OrderHistoryView,
    OrderDetailView,
    OrderPayView,
    OrderShippingUpdateView,
)

app_name = 'shop'

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/add/<int:pk>/', AddToCartView.as_view(), name='cart_add'),
    path('cart/update/<int:pk>/', UpdateCartItemView.as_view(), name='cart_update'),
    path('cart/remove/<int:pk>/', RemoveFromCartView.as_view(), name='cart_remove'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('checkout/success/', CheckoutSuccessView.as_view(), name='checkout_success'),
    path('checkout/cancel/', CheckoutCancelView.as_view(), name='checkout_cancel'),
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe_webhook'),
    path('orders/', OrderHistoryView.as_view(), name='order_history'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/pay/', OrderPayView.as_view(), name='order_pay'),
    path('orders/<int:pk>/shipping/', OrderShippingUpdateView.as_view(), name='order_shipping_update'),
]
