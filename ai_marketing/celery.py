import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_marketing.settings.production')

app = Celery('ai_marketing')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure Celery Beat
app.conf.beat_schedule = {
    'system-health-check': {
        'task': 'ai_marketing.tasks.system_health_check',
        'schedule': 300.0,  # Every 5 minutes
    },
    'cleanup-old-logs': {
        'task': 'ai_marketing.tasks.cleanup_old_logs', 
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'database-cleanup': {
        'task': 'ai_marketing.tasks.database_cleanup',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Weekly on Sunday at 3 AM
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    return 'Debug task completed successfully!'
    