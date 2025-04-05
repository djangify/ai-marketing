from django.contrib import admin
from .models import StripeCustomer, Subscription, Profile

@admin.register(StripeCustomer)
class StripeCustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'stripe_customer_id', 'created_at')
    search_fields = ('user__username', 'user__email', 'stripe_customer_id')
    readonly_fields = ('id', 'created_at')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'stripe_subscription_id', 'created_at')
    search_fields = ('user__username', 'user__email', 'stripe_subscription_id')
    readonly_fields = ('id', 'created_at')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
