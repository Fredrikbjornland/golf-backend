"""
WSGI config for golfbackend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
import time
import traceback
import signal
import sys

from django.core.wsgi import get_wsgi_application
from django.conf import settings


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "golfbackend.settings")

if getattr(settings, "PROJECT_ROOT_DIR", None):
    sys.path.append(settings.PROJECT_ROOT_DIR)

if getattr(settings, "LIBRARY_ROOT_DIR", None):
    sys.path.append(settings.LIBRARY_ROOT_DIR)

try:
    application = get_wsgi_application()
except Exception:
    # Error loading applications
    if "mod_wsgi" in sys.modules:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGINT)
        time.sleep(2.5)
