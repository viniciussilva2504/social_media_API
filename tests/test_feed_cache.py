from django.core.cache import cache
from django.test import TestCase
from django.contrib.auth.models import User

from accounts.models import Follow
from posts.services.feed_cache import (
    get_feed_version,
    build_feed_response_cache_key,
    bump_feed_version,
    invalidate_feed_for_users,
    invalidate_feed_for_author_and_followers,
    invalidate_feed_for_follow_change,
)


class FeedVersionTest(TestCase):
    def setUp(self):
        cache.clear()

    def test_initial_version_is_1(self):
        self.assertEqual(get_feed_version(999), 1)

    def test_bump_increments_version(self):
        get_feed_version(1)  # initialise
        bump_feed_version(1)
        self.assertEqual(get_feed_version(1), 2)

    def test_bump_when_no_initial_key(self):
        bump_feed_version(42)
        self.assertEqual(get_feed_version(42), 2)

    def test_build_cache_key_includes_version(self):
        key = build_feed_response_cache_key(1, "page=2")
        self.assertIn("v1", key)
        self.assertIn("page=2", key)

    def test_build_cache_key_default_query(self):
        key = build_feed_response_cache_key(1, "")
        self.assertIn("default", key)


class InvalidationTest(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("author", password="str0ngP@ss!")
        self.follower = User.objects.create_user("follower", password="str0ngP@ss!")
        Follow.objects.create(follower=self.follower, following=self.user)

    def test_invalidate_feed_for_users(self):
        v_before = get_feed_version(self.user.id)
        invalidate_feed_for_users([self.user.id])
        v_after = get_feed_version(self.user.id)
        self.assertGreater(v_after, v_before)

    def test_invalidate_feed_for_author_and_followers(self):
        v_author = get_feed_version(self.user.id)
        v_follower = get_feed_version(self.follower.id)
        invalidate_feed_for_author_and_followers(self.user.id)
        self.assertGreater(get_feed_version(self.user.id), v_author)
        self.assertGreater(get_feed_version(self.follower.id), v_follower)

    def test_invalidate_feed_for_follow_change(self):
        v1 = get_feed_version(self.follower.id)
        v2 = get_feed_version(self.user.id)
        invalidate_feed_for_follow_change(self.follower.id, self.user.id)
        self.assertGreater(get_feed_version(self.follower.id), v1)
        self.assertGreater(get_feed_version(self.user.id), v2)

    def test_invalidate_skips_none_ids(self):
        # Should not raise
        invalidate_feed_for_users([None, 0])
