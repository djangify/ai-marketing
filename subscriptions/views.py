# subscriptions/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Subscription, UserProfile
from .utils import has_access
import stripe
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.urls import reverse
from .stripe_utils import create_checkout_session, create_portal_session


@login_required
def subscription_required(request):
    """View shown when a user tries to access content without an active subscription"""
    context = {
        'has_subscription': hasattr(request.user, 'subscription') and request.user.subscription.is_active(),
        'in_trial': hasattr(request.user, 'profile') and request.user.profile.is_in_trial_period(),
    }
    return render(request, 'subscriptions/subscription_required.html', context)


@login_required
def subscription_detail(request):
    """View for displaying subscription details"""
    try:
        subscription = request.user.stripe_subscription  # Changed from subscription to stripe_subscription
        context = {
            'subscription': subscription,
            'in_trial': request.user.subscription_profile.is_in_trial_period() if hasattr(request.user, 'subscription_profile') else False,  # Changed from profile to subscription_profile
        }
        return render(request, 'subscriptions/subscription_detail.html', context)
    except:
        context = {
            'subscription': None,
            'in_trial': request.user.subscription_profile.is_in_trial_period() if hasattr(request.user, 'subscription_profile') else False,  # Changed from profile to subscription_profile
        }
        return render(request, 'subscriptions/subscription_detail.html', context)


@login_required
def subscription_checkout(request, subscription_type):
    """Create a checkout session for subscription purchase"""
    try:
        checkout_session = create_checkout_session(request, subscription_type)
        return redirect(checkout_session.url)
    except Exception as e:
        return render(request, 'subscriptions/error.html', {'error': str(e)})

@login_required
def checkout_success(request):
    """Handle successful checkout"""
    session_id = request.GET.get('session_id')
    if session_id:
        try:
            # Retrieve the session to get subscription info
            session = stripe.checkout.Session.retrieve(session_id)
            subscription_id = session.subscription
            
            # Update user's subscription in our database
            subscription, created = Subscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'stripe_subscription_id': subscription_id,
                    'payment_status': 'active',
                    'subscription_type': session.metadata.get('subscription_type', 'monthly'),
                    'start_date': timezone.now(),
                }
            )
            
            return render(request, 'subscriptions/checkout_success.html')
        except Exception as e:
            return render(request, 'subscriptions/error.html', {'error': str(e)})
    
    return redirect('subscriptions:subscription_detail')

@login_required
def checkout_cancel(request):
    """Handle canceled checkout"""
    return render(request, 'subscriptions/checkout_cancel.html')

@login_required
def subscription_portal(request):
    """Redirect to Stripe Customer Portal"""
    try:
        portal_session = create_portal_session(request)
        return redirect(portal_session.url)
    except Exception as e:
        return render(request, 'subscriptions/error.html', {'error': str(e)})

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'customer.subscription.created':
        handle_subscription_created(event)
    elif event['type'] == 'customer.subscription.updated':
        handle_subscription_updated(event)
    elif event['type'] == 'customer.subscription.deleted':
        handle_subscription_deleted(event)
    elif event['type'] == 'invoice.payment_succeeded':
        handle_payment_succeeded(event)
    elif event['type'] == 'invoice.payment_failed':
        handle_payment_failed(event)
    
    return HttpResponse(status=200)

def handle_subscription_created(event):
    """Handle subscription created webhook event"""
    subscription_data = event['data']['object']
    customer_id = subscription_data['customer']
    
    try:
        subscription = Subscription.objects.get(stripe_customer_id=customer_id)
        
        # Update subscription details
        subscription.stripe_subscription_id = subscription_data['id']
        subscription.payment_status = subscription_data['status']
        
        # Set end date if available
        if subscription_data['current_period_end']:
            end_timestamp = subscription_data['current_period_end']
            subscription.end_date = timezone.datetime.fromtimestamp(
                end_timestamp, tz=timezone.utc
            )
        
        subscription.save()
    except Subscription.DoesNotExist:
        # Subscription not found in our database
        pass

def handle_subscription_updated(event):
    """Handle subscription updated webhook event"""
    subscription_data = event['data']['object']
    subscription_id = subscription_data['id']
    
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
        
        # Update subscription status
        subscription.payment_status = subscription_data['status']
        
        # Update end date
        if subscription_data['current_period_end']:
            end_timestamp = subscription_data['current_period_end']
            subscription.end_date = timezone.datetime.fromtimestamp(
                end_timestamp, tz=timezone.utc
            )
        
        subscription.save()
    except Subscription.DoesNotExist:
        # Subscription not found in our database
        pass

def handle_subscription_deleted(event):
    """Handle subscription deleted webhook event"""
    subscription_data = event['data']['object']
    subscription_id = subscription_data['id']
    
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
        subscription.payment_status = 'canceled'
        subscription.save()
    except Subscription.DoesNotExist:
        # Subscription not found in our database
        pass

def handle_payment_succeeded(event):
    """Handle payment succeeded webhook event"""
    invoice_data = event['data']['object']
    subscription_id = invoice_data.get('subscription')
    
    if subscription_id:
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            subscription.payment_status = 'active'
            
            # Update end date based on the period end from the invoice
            if invoice_data.get('lines', {}).get('data'):
                for item in invoice_data['lines']['data']:
                    if item.get('period', {}).get('end'):
                        end_timestamp = item['period']['end']
                        subscription.end_date = timezone.datetime.fromtimestamp(
                            end_timestamp, tz=timezone.utc
                        )
                        break
            
            subscription.save()
        except Subscription.DoesNotExist:
            # Subscription not found in our database
            pass

def handle_payment_failed(event):
    """Handle payment failed webhook event"""
    invoice_data = event['data']['object']
    subscription_id = invoice_data.get('subscription')
    
    if subscription_id:
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            subscription.payment_status = 'past_due'
            subscription.save()
        except Subscription.DoesNotExist:
            # Subscription not found in our database
            pass

@login_required
def dashboard_subscription_status(request):
    """Dashboard component showing subscription status"""
    context = {
         'subscription': getattr(request.user, 'stripe_subscription', None),  
        'in_trial': request.user.subscription_profile.is_in_trial_period(),  
        'trial_days_remaining': request.user.subscription_profile.get_trial_days_remaining(),  
        'trial_end_date': request.user.subscription_profile.get_trial_end_date(),  
        'subscription_types': [
            {'type': 'monthly', 'name': 'Monthly', 'price': '£19.99/month', 'description': 'Perfect for individuals'},
            {'type': 'quarterly', 'name': 'Quarterly', 'price': '£50.97/quarter', 'description': 'Save 15% compared to monthly'},
            {'type': 'yearly', 'name': 'Yearly', 'price': '$179.91/year', 'description': 'Best value, save 25%'}
        ]
    }
    return render(request, 'subscriptions/dashboard_status.html', context)
  