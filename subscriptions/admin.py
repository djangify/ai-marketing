# subscriptions/admin.py
from django.contrib import admin
from .models import Subscription, UserProfile

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_type', 'payment_status', 'start_date', 'end_date')
    search_fields = ('user__username', 'user__email')
    list_filter = ('subscription_type', 'payment_status')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'signup_date')
    search_fields = ('user__username', 'user__email')