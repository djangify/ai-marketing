# subscriptions/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Subscription(models.Model):
    SUBSCRIPTION_TYPES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    
    PAYMENT_STATUS = (
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('trialing', 'Trialing'),
        ('unpaid', 'Unpaid'),
    )
    
    # Change the related_name to 'stripe_subscription' to avoid conflict
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stripe_subscription')
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_type = models.CharField(max_length=10, choices=SUBSCRIPTION_TYPES, default='monthly')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='incomplete')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s subscription"
    
    def is_active(self):
        """Check if the subscription is active"""
        if self.payment_status in ['active', 'trialing']:
            if self.end_date and self.end_date < timezone.now():
                return False
            return True
        return False

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription_profile')
    signup_date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username}'s Subscription Profile"
    
    def is_in_trial_period(self):
        """Check if the user is within the 3-day trial period"""
        trial_period_days = 3
        trial_end_date = self.signup_date + timezone.timedelta(days=trial_period_days)
        return timezone.now() <= trial_end_date
    
    def get_trial_days_remaining(self):
        """Get the number of days remaining in the trial period"""
        trial_period_days = 3
        trial_end_date = self.signup_date + timezone.timedelta(days=trial_period_days)
        remaining = (trial_end_date - timezone.now()).days
        return max(0, remaining + 1)  # +1 to include the current day
    
    def get_trial_end_date(self):
        """Get the date when the trial ends"""
        trial_period_days = 3
        return self.signup_date + timezone.timedelta(days=trial_period_days)
    