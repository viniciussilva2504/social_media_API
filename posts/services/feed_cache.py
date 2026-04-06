from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache

from accounts.models.follow import Follow


def _version_key(user_id):
    return f"feed:version:{user_id}"


def get_feed_cache_timeout():
    return getattr(settings, "FEED_CACHE_TIMEOUT_SECONDS", 60)


def get_feed_version(user_id):
    key = _version_key(user_id)
    version = cache.get(key)
    if version is None:
        cache.set(key, 1, None)
        return 1
    return version


def build_feed_response_cache_key(user_id, query_string):
    version = get_feed_version(user_id)
    query = query_string or "default"
    return f"feed:response:{user_id}:v{version}:{query}"


def bump_feed_version(user_id):
    key = _version_key(user_id)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 2, None)


def invalidate_feed_for_users(user_ids):
    for user_id in {uid for uid in user_ids if uid}:
        bump_feed_version(user_id)


def invalidate_feed_for_author_and_followers(author_id):
    follower_ids = Follow.objects.filter(following_id=author_id).values_list(
        "follower_id", flat=True
    )
    invalidate_feed_for_users([author_id, *list(follower_ids)])


def invalidate_feed_for_follow_change(follower_id, following_id):
    invalidate_feed_for_users([follower_id, following_id])


def get_user_if_exists(user_id):
    return User.objects.filter(id=user_id).first()
