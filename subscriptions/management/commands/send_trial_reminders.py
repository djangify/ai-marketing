# subscriptions/management/commands/send_trial_reminders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from subscriptions.models import UserProfile
from subscriptions.email import send_trial_reminder_email, send_trial_ended_email

class Command(BaseCommand):
    help = 'Send trial reminder emails to users'

    def handle(self, *args, **options):
        # Get all users with profiles
        profiles = UserProfile.objects.all()
        
        for profile in profiles:
            user = profile.user
            
            # Skip users who already have an active subscription
            if hasattr(user, 'subscription') and user.subscription.is_active():
                continue
            
            # Check trial status
            days_remaining = profile.get_trial_days_remaining()
            
            # Send appropriate emails
            if days_remaining == 2:  # Second day of trial
                send_trial_reminder_email(user, days_remaining)
                self.stdout.write(self.style.SUCCESS(f'Sent day 2 reminder to {user.email}'))
            
            elif days_remaining == 1:  # Last day of trial
                send_trial_reminder_email(user, days_remaining)
                self.stdout.write(self.style.SUCCESS(f'Sent last day reminder to {user.email}'))
            
            elif days_remaining == 0:  # Trial just ended
                trial_end_date = profile.get_trial_end_date()
                # Check if trial ended today
                if trial_end_date.date() == timezone.now().date():
                    send_trial_ended_email(user)
                    self.stdout.write(self.style.SUCCESS(f'Sent trial ended email to {user.email}'))
                    