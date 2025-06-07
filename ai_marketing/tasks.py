import os
import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings
from django.core.management import call_command

logger = logging.getLogger(__name__)


@shared_task
def system_health_check():
    """Basic system health check task - only logs failures"""
    try:
        # Check Redis connection
        from django.core.cache import cache

        cache.set("health_check", "ok", 30)
        redis_status = cache.get("health_check") == "ok"

        # Check database connection
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = True

        # Only log if there are failures
        if not redis_status or not db_status:
            logger.error(
                f"Health Check FAILED - Redis: {redis_status}, Database: {db_status}"
            )

        # Optional: Log a daily summary at midnight (hour 0)
        current_hour = datetime.now().hour
        if current_hour == 0:
            logger.info(
                f"Daily Health Check Summary - Redis: {redis_status}, Database: {db_status}"
            )

        return {
            "timestamp": datetime.now().isoformat(),
            "redis": redis_status,
            "database": db_status,
            "status": "healthy" if redis_status and db_status else "unhealthy",
        }
    except Exception as e:
        logger.error(f"Health check failed with exception: {str(e)}")
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": str(e),
        }


@shared_task
def cleanup_old_logs():
    """Clean up old log files"""
    try:
        logs_dir = os.path.join(settings.BASE_DIR, "logs")
        cleaned_files = 0

        if os.path.exists(logs_dir):
            # Remove log files older than 30 days
            cutoff_date = datetime.now() - timedelta(days=30)

            for filename in os.listdir(logs_dir):
                filepath = os.path.join(logs_dir, filename)
                if os.path.isfile(filepath):
                    file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_modified < cutoff_date:
                        os.remove(filepath)
                        cleaned_files += 1

        logger.info(f"Cleaned up {cleaned_files} old log files")
        return f"Cleaned {cleaned_files} files"

    except Exception as e:
        logger.error(f"Log cleanup failed: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def database_cleanup():
    """Clean up old database records"""
    try:
        # Clean up old sessions
        call_command("clearsessions")

        # Clean up old content generation jobs (keep last 100)
        from content_generation.models import ContentGenerationJob

        old_jobs = ContentGenerationJob.objects.order_by("-started_at")[100:]
        deleted_count = len(old_jobs)
        for job in old_jobs:
            job.delete()

        logger.info(f"Database cleanup completed - removed {deleted_count} old jobs")
        return f"Cleaned {deleted_count} old records"

    except Exception as e:
        logger.error(f"Database cleanup failed: {str(e)}")
        return f"Error: {str(e)}"
