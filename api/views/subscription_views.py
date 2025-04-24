from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from subscriptions.models import Subscription
from ..serializers import SubscriptionSerializer
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone

# Configure Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    """
    Create a Stripe checkout session
    """
    try:
        user = request.user
        subscription_type = request.data.get('subscription_type', 'monthly')
        
        # Set price ID based on subscription type
        if subscription_type == 'monthly':
            price_id = settings.STRIPE_PRICE_ID_MONTHLY
        elif subscription_type == 'quarterly':
            price_id = settings.STRIPE_PRICE_ID_QUARTERLY
        elif subscription_type == 'yearly':
            price_id = settings.STRIPE_PRICE_ID_YEARLY
        else:
            return Response({"error": "Invalid subscription type"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create Stripe customer
        if hasattr(user, 'stripe_subscription') and user.stripe_subscription.stripe_customer_id:
            customer_id = user.stripe_subscription.stripe_customer_id
        else:
            # Create a new customer
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}".strip() or user.username,
                metadata={
                    'user_id': str(user.id)
                }
            )
            customer_id = customer.id
            
            # Save the customer ID to our database
            if hasattr(user, 'stripe_subscription'):
                user.stripe_subscription.stripe_customer_id = customer_id
                user.stripe_subscription.save()
            else:
                Subscription.objects.create(
                    user=user,
                    stripe_customer_id=customer_id
                )
        
        # Create checkout session
        base_url = request.build_absolute_uri('/').rstrip('/')
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
            success_url=f"{base_url}/subscriptions/checkout-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/subscriptions/checkout-cancel",
            metadata={
                'user_id': str(user.id),
                'subscription_type': subscription_type
            }
        )
        
        return Response({"url": checkout_session.url})
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_portal_session(request):
    """
    Create a Stripe customer portal session
    """
    try:
        user = request.user
        
        # Check if user has a Stripe customer ID
        if not hasattr(user, 'stripe_subscription') or not user.stripe_subscription.stripe_customer_id:
            return Response({"error": "No Stripe customer found for this user"}, status=status.HTTP_404_NOT_FOUND)
            
        # Create a portal session
        base_url = request.build_absolute_uri('/').rstrip('/')
        portal_session = stripe.billing_portal.Session.create(
            customer=user.stripe_subscription.stripe_customer_id,
            return_url=f"{base_url}/subscriptions/manage/",
        )
        
        return Response({"url": portal_session.url})
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@csrf_exempt
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    """
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