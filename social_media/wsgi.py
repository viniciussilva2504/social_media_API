"""
WSGI config for social_media project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "social_media.settings")

application = get_wsgi_application()
