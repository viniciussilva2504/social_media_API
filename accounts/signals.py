import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from accounts.models.profile import Profile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            with transaction.atomic():
                Profile.objects.create(user=instance, display_name=instance.username)
        except Exception:
            logger.exception("Failed to create profile for user %s", instance.username)

        if instance.email:
            try:
                send_mail(
                    subject="welcome to ant.social",
                    message=(
                        f"hey @{instance.username},\n\n"
                        "welcome to the anti-social network.\n\n"
                        "— ant.social"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.email],
                    fail_silently=True,
                )
            except Exception:
                logger.warning("Failed to send welcome email to %s", instance.username)
