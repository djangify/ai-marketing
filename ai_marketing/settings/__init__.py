"""
Settings package for AI Marketing Platform

This module automatically loads the appropriate settings based on the
DJANGO_SETTINGS_MODULE environment variable or defaults to local settings.
"""

import os

# Default to local settings if not specified
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'ai_marketing.settings.local')

# Extract the settings file name from the module path
if '.' in settings_module:
    settings_file = settings_module.split('.')[-1]
else:
    settings_file = 'local'

# Import the appropriate settings
if settings_file == 'production':
    from .production import *
elif settings_file == 'local':
    from .local import *
else:
    # Fallback to local for any other case
    from .local import *