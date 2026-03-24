"""
ASGI config for social_media project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "social_media.settings")

application = get_asgi_application()
