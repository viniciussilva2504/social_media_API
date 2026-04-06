from django.test import TestCase, Client
from django.contrib.auth.models import User

from accounts.models import Follow


class HomeViewTest(TestCase):
    def test_home_unauthenticated(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "home.html")

    def test_home_authenticated_redirects(self):
        User.objects.create_user(username="user", password="testpass123!")
        self.client.login(username="user", password="testpass123!")
        resp = self.client.get("/")
        self.assertRedirects(resp, "/feed/")


class RegisterViewTest(TestCase):
    def test_register_get(self):
        resp = self.client.get("/register/")
        self.assertEqual(resp.status_code, 200)

    def test_register_success(self):
        resp = self.client.post("/register/", {
            "username": "newuser",
            "email": "new@example.com",
            "password": "strongpass123!",
            "password_confirm": "strongpass123!",
        })
        self.assertRedirects(resp, "/feed/")
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_password_mismatch(self):
        resp = self.client.post("/register/", {
            "username": "newuser",
            "password": "strongpass123!",
            "password_confirm": "wrongpass123!",
        })
        self.assertEqual(resp.status_code, 200)

    def test_register_weak_password(self):
        resp = self.client.post("/register/", {
            "username": "newuser",
            "password": "12345678",
            "password_confirm": "12345678",
        })
        self.assertEqual(resp.status_code, 200)

    def test_register_duplicate_username(self):
        User.objects.create_user(username="taken", password="testpass123!")
        resp = self.client.post("/register/", {
            "username": "taken",
            "password": "strongpass123!",
            "password_confirm": "strongpass123!",
        })
        self.assertEqual(resp.status_code, 200)


class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )

    def test_login_get(self):
        resp = self.client.get("/login/")
        self.assertEqual(resp.status_code, 200)

    def test_login_success(self):
        resp = self.client.post("/login/", {
            "username": "testuser",
            "password": "testpass123!",
        })
        self.assertRedirects(resp, "/feed/")

    def test_login_failure(self):
        resp = self.client.post("/login/", {
            "username": "testuser",
            "password": "wrongpass",
        })
        self.assertEqual(resp.status_code, 200)


class LogoutViewTest(TestCase):
    def test_logout(self):
        User.objects.create_user(username="user", password="testpass123!")
        self.client.login(username="user", password="testpass123!")
        resp = self.client.post("/logout/")
        self.assertRedirects(resp, "/")


class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.client.login(username="testuser", password="testpass123!")

    def test_profile_view(self):
        resp = self.client.get(f"/profile/{self.user.username}/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "profile.html")

    def test_profile_not_found(self):
        resp = self.client.get("/profile/nonexistent/")
        self.assertEqual(resp.status_code, 404)

    def test_profile_requires_login(self):
        self.client.logout()
        resp = self.client.get(f"/profile/{self.user.username}/")
        self.assertEqual(resp.status_code, 302)


class EditProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.client.login(username="testuser", password="testpass123!")

    def test_edit_own_profile(self):
        resp = self.client.post(f"/profile/{self.user.username}/edit/", {
            "display_name": "New Name",
            "bio": "New bio",
        })
        self.assertRedirects(resp, f"/profile/{self.user.username}/")
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.display_name, "New Name")

    def test_cannot_edit_other_profile(self):
        other = User.objects.create_user(username="other", password="testpass123!")
        resp = self.client.get(f"/profile/{other.username}/edit/")
        self.assertRedirects(resp, f"/profile/{other.username}/")


class FollowersFollowingViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", password="testpass123!"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="testpass123!"
        )
        Follow.objects.create(follower=self.user1, following=self.user2)
        self.client.login(username="user1", password="testpass123!")

    def test_followers_view(self):
        resp = self.client.get(f"/profile/{self.user2.username}/followers/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "follow_list.html")

    def test_following_view(self):
        resp = self.client.get(f"/profile/{self.user1.username}/following/")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "follow_list.html")


class SelfFollowConstraintTest(TestCase):
    def test_self_follow_prevented_at_db_level(self):
        user = User.objects.create_user(username="user", password="testpass123!")
        with self.assertRaises(Exception):
            Follow.objects.create(follower=user, following=user)
