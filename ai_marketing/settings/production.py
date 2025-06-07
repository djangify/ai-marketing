import os
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Database in base.py is already set up to use environment variables


ALLOWED_HOSTS = env.list(  # noqa: F405
    "ALLOWED_HOSTS",
    default=[
        "aimarketingplatform.app",
        "www.aimarketingplatform.app",
    ],
)

CSRF_TRUSTED_ORIGINS = env.list(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://aimarketingplatform.app",
        "https://www.aimarketingplatform.app",
    ],
)

# Redis Configuration
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_URL = f"redis://:{REDIS_PASSWORD}@127.0.0.1:6379/0"

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Email configuration for production
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL", default="noreply@aimarketingplatform.app"
)

# Static files for production
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# Site URL for production
SITE_URL = "https://aimarketingplatform.app"

# Security settings for production
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Additional security headers
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Session security
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True

# Create logs directory if it doesn't exist
logs_dir = os.path.join(BASE_DIR, "logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir, mode=0o755, exist_ok=True)

# Create celery log directories
# celery_logs_dir = "/var/log/celery"
# celery_run_dir = "/var/run/celery"
# for directory in [celery_logs_dir, celery_run_dir]:
#     if not os.path.exists(directory):
#         os.makedirs(directory, mode=0o755, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "django_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(logs_dir, "django.log"),
            "formatter": "verbose",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "mode": "a",
        },
        "celery_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(logs_dir, "celery.log"),
            "formatter": "verbose",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "mode": "a",
        },
        "celery_beat_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(logs_dir, "celery_beat.log"),
            "formatter": "simple",
            "maxBytes": 5242880,  # 5MB
            "backupCount": 3,
            "mode": "a",
        },
        "console": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["django_file", "console"],
            "level": "INFO",
            "propagate": True,
        },
        "ai_marketing": {
            "handlers": ["django_file", "console"],
            "level": "INFO",
            "propagate": True,
        },
        "celery": {
            "handlers": ["celery_file", "console"],
            "level": "INFO",
            "propagate": True,
        },
        "celery.beat": {
            "handlers": ["celery_beat_file"],
            "level": "INFO",
            "propagate": False,
        },
        "celery.task": {
            "handlers": ["celery_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Celery Beat Configuration (Database Scheduler)
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BEAT_SCHEDULE = {
    "system-health-check": {
        "task": "ai_marketing.tasks.system_health_check",
        "schedule": 3600.0,  # Every hour (changed from 300.0)
    },
    "cleanup-old-logs": {
        "task": "ai_marketing.tasks.cleanup_old_logs",
        "schedule": 86400.0,  # Daily
    },
}

# Production cache (Redis)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": 300,
    }
}
