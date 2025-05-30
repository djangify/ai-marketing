# myproject/wsgi.py
import os
import sys
import signal
import threading
from django.core.wsgi import get_wsgi_application

# Define your cleanup function
def graceful_shutdown(signum, frame):
    print("SIGTERM received, cleaning up…")
    # If you have open files or DB connections you could close them here
    sys.exit(0)

# Only register signal handlers if in main thread
if threading.current_thread() is threading.main_thread():
    # Register signal handlers
    signal.signal(signal.SIGTERM, graceful_shutdown)  # Standard termination signal
    signal.signal(signal.SIGINT, graceful_shutdown)   # Keyboard interrupt (Ctrl+C)
    signal.signal(signal.SIGUSR1, graceful_shutdown)  # User-defined signal

# Continue bootstrapping Django as usual
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_marketing.settings.production')
application = get_wsgi_application()