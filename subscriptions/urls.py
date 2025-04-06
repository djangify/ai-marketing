# subscriptions/urls.py
from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('subscription-required/', views.subscription_required, name='subscription_required'),
    path('detail/', views.subscription_detail, name='subscription_detail'),
    path('checkout/<str:subscription_type>/', views.subscription_checkout, name='subscription_checkout'),
    path('checkout-success/', views.checkout_success, name='checkout_success'),
    path('checkout-cancel/', views.checkout_cancel, name='checkout_cancel'),
    path('portal/', views.subscription_portal, name='subscription_portal'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('dashboard-status/', views.dashboard_subscription_status, name='dashboard_status'),
]

