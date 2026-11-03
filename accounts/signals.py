import logging

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
                # User.username allows 150 chars but Profile.display_name only
                # 100; truncate so long usernames still get a profile.
                max_len = Profile._meta.get_field("display_name").max_length
                Profile.objects.create(
                    user=instance, display_name=instance.username[:max_len]
                )
        except Exception:
            logger.exception("Failed to create profile for user %s", instance.username)
