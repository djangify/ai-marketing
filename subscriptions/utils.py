# subscriptions/utils.py
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from functools import wraps

def has_access(user):
    """
    Check if a user has access based on trial period, active subscription, or superuser status
    """
    if not user.is_authenticated:
        return False
    
    # Superusers always have access
    if user.is_superuser:
        return True
    
    # Check if user is in trial period
    try:
        if hasattr(user, 'subscription_profile') and user.subscription_profile.is_in_trial_period():
            return True
    except Exception as e:
        print(f"Error checking trial period: {e}")
        pass
    
    # Check if user has active subscription
    try:
        if hasattr(user, 'stripe_subscription') and user.stripe_subscription.is_active():
            return True
    except Exception as e:
        print(f"Error checking subscription: {e}")
        pass
    
    return False

def subscription_required(view_func):
    """
    Decorator to restrict access to views based on subscription status
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if has_access(request.user):
            return view_func(request, *args, **kwargs)
        else:
            # Redirect to subscription page if no access
            return redirect('subscriptions:subscription_required')
    return _wrapped_view
