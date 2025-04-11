# subscriptions/context_processors.py
from .utils import has_access

def subscription_status(request):
    """Make subscription status available in all templates"""
    context = {
        'has_access': has_access(request.user),
        'in_trial': False,
        'trial_days_remaining': 0,
        'trial_end_date': None,
        'subscription': None,
    }
    
    if request.user.is_authenticated:
        # Superusers are treated as having full access
        if request.user.is_superuser:
            context['has_access'] = True
            # Set as if they have an active subscription to hide trial messages
            context['subscription'] = {'is_active': True}
            return context
        
        # Add trial info if user has a profile
        if hasattr(request.user, 'subscription_profile'):  
            context['in_trial'] = request.user.subscription_profile.is_in_trial_period()
            context['trial_days_remaining'] = request.user.subscription_profile.get_trial_days_remaining()
            context['trial_end_date'] = request.user.subscription_profile.get_trial_end_date()
        
        # Add subscription if user has one
        if hasattr(request.user, 'stripe_subscription'):  
            context['subscription'] = request.user.stripe_subscription
    
    return context