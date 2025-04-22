from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone


class StripeCustomer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stripe_customer')
    stripe_customer_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Stripe Customer ({self.stripe_customer_id})"

class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    stripe_subscription_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Subscription ({self.stripe_subscription_id})"
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True, help_text="Tell us a little about yourself")
    # Add additional fields as needed
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# Add to accounts/models.py after the Profile model
class TokenUsage(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='token_usage')
    prompt_tokens_used = models.IntegerField(default=0)
    asset_tokens_used = models.IntegerField(default=0)
    last_reset_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Token Usage"
    
    def reset_usage(self):
        """Reset token usage counters on subscription renewal"""
        self.prompt_tokens_used = 0
        self.asset_tokens_used = 0
        self.last_reset_date = timezone.now()
        self.save()

class MemberResource(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    file = models.FileField(upload_to='member_resources/')
    thumbnail = models.ImageField(upload_to='member_resources/thumbnails/')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
