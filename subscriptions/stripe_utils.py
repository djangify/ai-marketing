# subscriptions/stripe_utils.py
import stripe
from django.conf import settings
from django.urls import reverse
from .models import Subscription

# Configure Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_customer(user):
    """Create a Stripe customer for the given user"""
    customer = stripe.Customer.create(
        email=user.email,
        name=f"{user.first_name} {user.last_name}",
        metadata={
            'user_id': user.id
        }
    )
    return customer.id

def create_checkout_session(request, subscription_type):
    """Create a Stripe Checkout Session for subscription purchase"""
    if subscription_type == 'monthly':
        price_id = settings.STRIPE_PRICE_ID_MONTHLY
    elif subscription_type == 'quarterly':
        price_id = settings.STRIPE_PRICE_ID_QUARTERLY
    elif subscription_type == 'yearly':
        price_id = settings.STRIPE_PRICE_ID_YEARLY
    else:
        raise ValueError("Invalid subscription type")
    
    user = request.user
    
    # Get or create Stripe customer
    if hasattr(user, 'subscription') and user.subscription.stripe_customer_id:
        customer_id = user.subscription.stripe_customer_id
    else:
        customer_id = create_stripe_customer(user)
        # Create or update subscription record with customer ID
        Subscription.objects.update_or_create(
            user=user,
            defaults={'stripe_customer_id': customer_id}
        )
    
    # Create Stripe Checkout session
    success_url = request.build_absolute_uri(
        reverse('subscriptions:checkout_success')
    )
    cancel_url = request.build_absolute_uri(
        reverse('subscriptions:checkout_cancel')
    )
    
    checkout_session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=['card'],
        line_items=[
            {
                'price': price_id,
                'quantity': 1,
            },
        ],
        mode='subscription',
        success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=cancel_url,
        metadata={
            'user_id': user.id,
            'subscription_type': subscription_type
        }
    )
    
    return checkout_session


def create_portal_session(request):
    """Create a Stripe Customer Portal session for managing subscriptions"""
    user = request.user
    
    if not hasattr(user, 'stripe_subscription') or not user.stripe_subscription.stripe_customer_id:  # Changed from subscription to stripe_subscription
        raise ValueError("User has no Stripe customer ID")
    
    return_url = request.build_absolute_uri(
        reverse('subscriptions:subscription_detail')
    )
    
    portal_session = stripe.billing_portal.Session.create(
        customer=user.stripe_subscription.stripe_customer_id,  # Changed from subscription to stripe_subscription
        return_url=return_url,
    )
    
    return portal_session