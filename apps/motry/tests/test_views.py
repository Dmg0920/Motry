"""
View 單元測試

測試所有 View 的回應狀態、權限控制、重定向行為。
"""

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from allauth.socialaccount.models import SocialApp

from apps.motry.models import (
    Vehicle,
    Post,
    Comment,
    UserVehicle,
    FavoriteVehicle,
    Rating,
    Like,
)

User = get_user_model()


def setup_social_app():
    """設置 allauth 社交登入所需的 SocialApp"""
    site = Site.objects.get_current()
    app, _ = SocialApp.objects.get_or_create(
        provider="google",
        defaults={
            "name": "Google",
            "client_id": "test-client-id",
            "secret": "test-secret",
        },
    )
    if not app.sites.filter(pk=site.pk).exists():
        app.sites.add(site)


class PublicViewTests(TestCase):
    """公開頁面測試（無需登入）"""

    def setUp(self):
        self.client = Client()
        self.vehicle = Vehicle.objects.create(
            
            brand="Toyota",
            model="GR86",
            displacement_cc=2387,
            horsepower_ps=235,
        )
        setup_social_app()

    def test_search_page_accessible(self):
        """測試搜尋頁面可訪問"""
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "motry/search_results.html")

    def test_search_with_query(self):
        """測試搜尋功能"""
        response = self.client.get(reverse("search"), {"query": "Toyota"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Toyota")

    def test_search_with_filters(self):
        """測試搜尋篩選"""
        response = self.client.get(
            reverse("search"),
            {
                "type": "car",
                "brand": "Toyota",
                "displacement_min": "2000",
                "hp_min": "200",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_vehicle_detail_accessible(self):
        """測試車輛詳情頁可訪問"""
        response = self.client.get(
            reverse("vehicle_detail", kwargs={"id": self.vehicle.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "motry/vehicle_detail.html")
        self.assertContains(response, "Toyota")
        self.assertContains(response, "GR86")

    def test_vehicle_detail_not_found(self):
        """測試車輛詳情頁 404"""
        response = self.client.get(reverse("vehicle_detail", kwargs={"id": 99999}))
        self.assertEqual(response.status_code, 404)

    def test_register_page_accessible(self):
        """測試註冊頁面可訪問"""
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "motry/auth/register.html")

    def test_login_page_accessible(self):
        """測試登入頁面可訪問"""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)


class AuthenticationTests(TestCase):
    """認證相關測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        setup_social_app()

    def test_login_success(self):
        """測試登入成功"""
        response = self.client.post(
            reverse("login"),
            {"username": "testuser", "password": "testpass123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_login_failure(self):
        """測試登入失敗（錯誤密碼）"""
        response = self.client.post(
            reverse("login"),
            {"username": "testuser", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse("_auth_user_id" in self.client.session)

    def test_logout(self):
        """測試登出"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse("_auth_user_id" in self.client.session)

    def test_register_success(self):
        """測試註冊成功"""
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_password_mismatch(self):
        """測試註冊失敗（密碼不匹配）"""
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "ComplexPass123!",
                "password2": "DifferentPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())


class ProtectedViewTests(TestCase):
    """需要登入的頁面測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            
            brand="Honda",
            model="Civic",
        )
        setup_social_app()

    def test_garage_requires_login(self):
        """測試車庫頁面需要登入"""
        response = self.client.get(reverse("user_garage"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('user_garage')}",
            fetch_redirect_response=False,
        )

    def test_garage_accessible_when_logged_in(self):
        """測試登入後可訪問車庫"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("user_garage"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "motry/garage.html")

    def test_favorites_requires_login(self):
        """測試最愛頁面需要登入"""
        response = self.client.get(reverse("user_favorites"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('user_favorites')}",
            fetch_redirect_response=False,
        )

    def test_favorites_accessible_when_logged_in(self):
        """測試登入後可訪問最愛"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("user_favorites"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "motry/favorites.html")

    def test_post_create_requires_login(self):
        """測試發表心得需要登入"""
        response = self.client.get(reverse("post_create"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('post_create')}",
            fetch_redirect_response=False,
        )

    def test_post_create_accessible_when_logged_in(self):
        """測試登入後可訪問發表心得頁面"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("post_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "motry/post_form.html")

    def test_vehicle_create_requires_login(self):
        """測試新增車輛需要登入"""
        response = self.client.get(reverse("vehicle_create"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('vehicle_create')}",
            fetch_redirect_response=False,
        )


class PostViewTests(TestCase):
    """貼文相關 View 測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="poster",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            
            brand="Subaru",
            model="BRZ",
        )
        self.post = Post.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            body_text="測試貼文內容",
        )
        setup_social_app()

    def test_post_delete_own_post(self):
        """測試刪除自己的貼文"""
        self.client.login(username="poster", password="testpass123")
        response = self.client.post(
            reverse("post_delete", kwargs={"post_id": self.post.id}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_deleted)

    def test_post_delete_others_post_forbidden(self):
        """測試無法刪除他人貼文"""
        self.client.login(username="other", password="testpass123")
        response = self.client.post(
            reverse("post_delete", kwargs={"post_id": self.post.id}),
            follow=True,
        )
        self.post.refresh_from_db()
        self.assertFalse(self.post.is_deleted)


class CommentViewTests(TestCase):
    """留言相關 View 測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="commenter",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            
            brand="Kawasaki",
            model="Ninja 400",
        )
        self.post = Post.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            body_text="測試貼文",
        )
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            body_text="測試留言",
        )
        setup_social_app()

    def test_comment_create_requires_login(self):
        """測試留言需要登入"""
        response = self.client.post(
            reverse("comment_create"),
            {"post": self.post.id, "body_text": "新留言"},
        )
        # 應該重定向到登入頁或返回錯誤
        self.assertNotEqual(response.status_code, 201)

    def test_comment_delete_own_comment(self):
        """測試刪除自己的留言"""
        self.client.login(username="commenter", password="testpass123")
        response = self.client.post(
            reverse("comment_delete", kwargs={"comment_id": self.comment.id}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_deleted)

    def test_comment_delete_others_comment_forbidden(self):
        """測試無法刪除他人留言"""
        self.client.login(username="other", password="testpass123")
        response = self.client.post(
            reverse("comment_delete", kwargs={"comment_id": self.comment.id}),
            follow=True,
        )
        self.comment.refresh_from_db()
        self.assertFalse(self.comment.is_deleted)


class RatingViewTests(TestCase):
    """評分相關 View 測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="rater",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            
            brand="Mercedes-Benz",
            model="C-Class",
        )
        setup_social_app()

    def test_rate_vehicle_requires_login(self):
        """測試評分需要登入"""
        response = self.client.post(
            reverse("rate_vehicle", kwargs={"id": self.vehicle.id}),
            {"score": "5"},
        )
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('rate_vehicle', kwargs={'id': self.vehicle.id})}",
            fetch_redirect_response=False,
        )

    def test_rate_vehicle_success(self):
        """測試評分成功"""
        self.client.login(username="rater", password="testpass123")
        response = self.client.post(
            reverse("rate_vehicle", kwargs={"id": self.vehicle.id}),
            {"score": "5"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Rating.objects.filter(vehicle=self.vehicle, user=self.user).exists()
        )

    def test_rate_vehicle_update(self):
        """測試更新評分"""
        self.client.login(username="rater", password="testpass123")
        # 第一次評分
        self.client.post(
            reverse("rate_vehicle", kwargs={"id": self.vehicle.id}),
            {"score": "3"},
        )
        # 更新評分
        self.client.post(
            reverse("rate_vehicle", kwargs={"id": self.vehicle.id}),
            {"score": "5"},
        )
        rating = Rating.objects.get(vehicle=self.vehicle, user=self.user)
        self.assertEqual(rating.score, 5)


class LikeViewTests(TestCase):
    """按讚相關 View 測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="liker",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            
            brand="Audi",
            model="RS6",
        )
        self.post = Post.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            body_text="測試貼文",
        )
        setup_social_app()

    def test_like_toggle_requires_login(self):
        """測試按讚需要登入"""
        response = self.client.get(
            reverse("like_toggle", kwargs={"post_id": self.post.id})
        )
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('like_toggle', kwargs={'post_id': self.post.id})}",
            fetch_redirect_response=False,
        )

    def test_like_toggle_add(self):
        """測試按讚"""
        self.client.login(username="liker", password="testpass123")
        response = self.client.get(
            reverse("like_toggle", kwargs={"post_id": self.post.id}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Like.objects.filter(post=self.post, user=self.user).exists())

    def test_like_toggle_remove(self):
        """測試取消按讚"""
        self.client.login(username="liker", password="testpass123")
        Like.objects.create(post=self.post, user=self.user)
        response = self.client.get(
            reverse("like_toggle", kwargs={"post_id": self.post.id}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Like.objects.filter(post=self.post, user=self.user).exists())


class StaffViewTests(TestCase):
    """管理員專用 View 測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="normaluser",
            password="testpass123",
        )
        self.staff = User.objects.create_user(
            username="staffuser",
            password="testpass123",
            is_staff=True,
        )

    def test_export_csv_requires_staff(self):
        """測試匯出 CSV 需要管理員權限"""
        self.client.login(username="normaluser", password="testpass123")
        response = self.client.post(reverse("export_vehicles_csv"))
        # 非管理員應該被重定向到管理員登入頁
        self.assertNotEqual(response.status_code, 200)

    def test_export_csv_staff_access(self):
        """測試管理員可以匯出 CSV"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.post(reverse("export_vehicles_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
