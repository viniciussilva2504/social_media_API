from django.test import TestCase
from django.contrib.auth.models import User

from accounts.models import Profile, Follow


class ProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )

    def test_profile_created_on_user_creation(self):
        self.assertTrue(hasattr(self.user, "profile"))
        self.assertEqual(self.user.profile.display_name, "testuser")

    def test_profile_str(self):
        self.assertEqual(str(self.user.profile), "@testuser")

    def test_followers_count_property(self):
        self.assertEqual(self.user.profile.followers_count, 0)

    def test_following_count_property(self):
        self.assertEqual(self.user.profile.following_count, 0)


class FollowModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", password="testpass123!"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="testpass123!"
        )

    def test_follow_creation(self):
        follow = Follow.objects.create(follower=self.user1, following=self.user2)
        self.assertEqual(str(follow), "user1 -> user2")

    def test_follow_unique_constraint(self):
        Follow.objects.create(follower=self.user1, following=self.user2)
        with self.assertRaises(Exception):
            Follow.objects.create(follower=self.user1, following=self.user2)

    def test_followers_count_updates(self):
        Follow.objects.create(follower=self.user1, following=self.user2)
        self.assertEqual(self.user2.profile.followers_count, 1)
        self.assertEqual(self.user1.profile.following_count, 1)
