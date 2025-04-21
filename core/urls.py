# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
     path('quick_start/', views.quick_start, name='quick_start'),
    path('policy/privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('policy/cookies-policy/', views.cookies_policy, name='cookies_policy'),
    path('policy/terms-policy/', views.terms_policy, name='terms_policy'),
    path('policy/refund-policy/', views.refund_policy, name='refund_policy'),
    path('policy/support-policy/', views.support_policy, name='support_policy'),
    path('policy/advertising-policy/', views.advertising_policy, name='advertising_policy'),
    path('policy/policies/', views.policies_index, name='policies_index'),
    
]