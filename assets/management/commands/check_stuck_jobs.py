from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from assets.models import AssetProcessingJob
import datetime

class Command(BaseCommand):
    help = 'Checks for stuck asset processing jobs and marks them as failed'

    def handle(self, *args, **options):
        # Get the threshold time
        threshold = timezone.now() - datetime.timedelta(seconds=settings.STUCK_JOB_THRESHOLD_SECONDS)
        
        # Find jobs that are in progress but haven't had a heartbeat recently
        stuck_jobs = AssetProcessingJob.objects.filter(
            status='in_progress',
            last_heartbeat__lt=threshold
        )
        
        count = stuck_jobs.count()
        if count > 0:
            self.stdout.write(f'Found {count} stuck jobs')
            
            # Update the stuck jobs
            for job in stuck_jobs:
                job.status = 'failed'
                job.error_message = 'Job is stuck - no heartbeat received recently'
                job.attempts += 1
                
                # Check if max attempts exceeded
                if job.attempts >= settings.MAX_JOB_ATTEMPTS:
                    job.status = 'max_attempts_exceeded'
                    
                job.save()
                self.stdout.write(f'Updated job {job.id} to {job.status}')
        else:
            self.stdout.write('No stuck jobs found')
            