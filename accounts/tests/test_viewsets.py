from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User


class RegisterViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "strongpass123!",
            "password_confirm": "strongpass123!",
        }
        resp = self.client.post("/antisocial/v1/register/", data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", resp.data)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_password_mismatch(self):
        data = {
            "username": "newuser",
            "password": "strongpass123!",
            "password_confirm": "wrongpass123!",
        }
        resp = self.client.post("/antisocial/v1/register/", data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        data = {
            "username": "newuser",
            "password": "12345678",
            "password_confirm": "12345678",
        }
        resp = self.client.post("/antisocial/v1/register/", data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        User.objects.create_user(username="existing", password="testpass123!")
        data = {
            "username": "existing",
            "password": "strongpass123!",
            "password_confirm": "strongpass123!",
        }
        resp = self.client.post("/antisocial/v1/register/", data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )

    def test_login_success(self):
        data = {"username": "testuser", "password": "testpass123!"}
        resp = self.client.post("/antisocial/v1/login/", data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("token", resp.data)

    def test_login_invalid_credentials(self):
        data = {"username": "testuser", "password": "wrongpass"}
        resp = self.client.post("/antisocial/v1/login/", data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class JWTAuthViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="jwtuser", password="testpass123!"
        )

    def test_jwt_token_obtain_pair_success(self):
        data = {"username": "jwtuser", "password": "testpass123!"}
        resp = self.client.post("/antisocial/v1/auth/jwt/token/", data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_jwt_refresh_success(self):
        obtain_resp = self.client.post(
            "/antisocial/v1/auth/jwt/token/",
            {"username": "jwtuser", "password": "testpass123!"},
        )
        refresh_resp = self.client.post(
            "/antisocial/v1/auth/jwt/refresh/",
            {"refresh": obtain_resp.data["refresh"]},
        )
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_resp.data)


class HealthcheckViewTest(TestCase):
    def test_healthcheck(self):
        resp = self.client.get("/health/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("status"), "ok")
        self.assertEqual(resp.json().get("database"), "ok")
        self.assertIn("X-Request-ID", resp)


class ProfileViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123!"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_profiles(self):
        resp = self.client.get("/antisocial/v1/profile/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_profile(self):
        resp = self.client.get(f"/antisocial/v1/profile/{self.user.username}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "testuser")

    def test_retrieve_own_profile_via_me(self):
        resp = self.client.get("/antisocial/v1/profile/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "testuser")

    def test_me_endpoint_returns_correct_counts(self):
        other = User.objects.create_user(username="other", password="testpass123!")
        from accounts.models import Follow
        Follow.objects.create(follower=other, following=self.user)
        Follow.objects.create(follower=self.user, following=other)
        resp = self.client.get("/antisocial/v1/profile/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["followers_count"], 1)
        self.assertEqual(resp.data["following_count"], 1)

    def test_update_own_profile(self):
        resp = self.client.patch(
            "/antisocial/v1/profile/me/",
            {"display_name": "New Name", "bio": "New bio"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.display_name, "New Name")

    def test_cannot_update_other_profile(self):
        other = User.objects.create_user(username="other", password="testpass123!")
        resp = self.client.patch(
            f"/antisocial/v1/profile/{other.username}/",
            {"display_name": "Hacked"},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class FollowViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username="user1", password="testpass123!"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="testpass123!"
        )
        self.client.force_authenticate(user=self.user1)

    def test_follow_toggle(self):
        resp = self.client.post("/antisocial/v1/follow/toggle/user2/")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "followed")

    def test_unfollow_toggle(self):
        self.client.post("/antisocial/v1/follow/toggle/user2/")
        resp = self.client.post("/antisocial/v1/follow/toggle/user2/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "unfollowed")

    def test_cannot_follow_self(self):
        resp = self.client.post("/antisocial/v1/follow/toggle/user1/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_followers_list(self):
        self.client.post("/antisocial/v1/follow/toggle/user2/")
        resp = self.client.get("/antisocial/v1/follow/followers/user2/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)

    def test_following_list(self):
        self.client.post("/antisocial/v1/follow/toggle/user2/")
        resp = self.client.get("/antisocial/v1/follow/following/user1/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)


class UserSearchViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="searchme", password="testpass123!"
        )
        self.client.force_authenticate(user=self.user)

    def test_search_users(self):
        resp = self.client.get("/antisocial/v1/users/?q=search")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data["results"]), 1)

    def test_search_unauthenticated(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/antisocial/v1/users/?q=search")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
