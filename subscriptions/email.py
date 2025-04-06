# subscriptions/email.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_trial_welcome_email(user):
    """Send welcome email on day 1 of trial"""
    subject = 'Welcome to Your Trial!'
    context = {
        'user': user,
        'days_remaining': user.profile.get_trial_days_remaining(),
        'trial_end_date': user.profile.get_trial_end_date(),
    }
    html_message = render_to_string('subscriptions/emails/trial_welcome.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )

def send_trial_reminder_email(user, days_remaining):
    """Send reminder email during trial"""
    subject = f'Your Trial Ends in {days_remaining} {"Day" if days_remaining == 1 else "Days"}'
    context = {
        'user': user,
        'days_remaining': days_remaining,
        'trial_end_date': user.profile.get_trial_end_date(),
    }
    html_message = render_to_string('subscriptions/emails/trial_reminder.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )

def send_trial_ended_email(user):
    """Send email when trial has ended"""
    subject = 'Your Trial Has Ended'
    context = {
        'user': user,
    }
    html_message = render_to_string('subscriptions/emails/trial_ended.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )
    