from pathlib import Path
import os
from django.urls import reverse_lazy
import environ
from celery.schedules import crontab

# Initialize environment variables
env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Read the .env file
env.read_env(os.path.join(BASE_DIR, '.env'))

# SECRET_KEY
SECRET_KEY = env('SECRET_KEY')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'subscriptions.apps.SubscriptionsConfig',
    # Third-party apps
    'widget_tweaks',
    'django_celery_results',
    'django_celery_beat',
    'tinymce',
    
    # Local apps
    'accounts',
    'projects',
    'content_templates',
    'prompts',
    'assets',
    'api',
    'blog',
    'core',
    'docs',
    'content_generation',
    'seo_optimization',
    'prompt_generator',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'ai_marketing.middleware.AuthRequiredMiddleware', 
]

# Authentication settings
# LOGIN_URL = '/accounts/login/'
# LOGIN_REDIRECT_URL = '/dashboard/'
# LOGOUT_REDIRECT_URL = '/accounts/login/'
ADMIN_URL = 'admin/'

# Constants for the application
MAX_TOKENS_ASSETS = 100000
MAX_TOKENS_PROMPT = 20000

ROOT_URLCONF = 'ai_marketing.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'subscriptions.context_processors.subscription_status',
            ],
        },
    },
]

WSGI_APPLICATION = 'ai_marketing.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Media and Static files (CSS, JavaScript, Images)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Stripe settings
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='pk_test_placeholder')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='sk_test_placeholder')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='whsec_placeholder')
STRIPE_PRICE_ID_MONTHLY = env('STRIPE_PRICE_ID_MONTHLY', default='price_1RHL24BSytWSX0dbjJFz6BQO')
STRIPE_PRICE_ID_QUARTERLY = env('STRIPE_PRICE_ID_QUARTERLY', default='price_1RHL4KBSytWSX0db7cIwLiDc')
STRIPE_PRICE_ID_YEARLY = env('STRIPE_PRICE_ID_YEARLY', default='price_1RHL63BSytWSX0dbfT6OzPq4')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# OpenAI API settings
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
OPENAI_DEFAULT_MODEL = 'gpt-4o'
OPENAI_FALLBACK_MODEL = 'gpt-3.5-turbo'

# Cache settings (base configuration)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Default site URL (will be overridden in local/production)
SITE_URL = env('SITE_URL', default='https://aimarketingplatform.app')