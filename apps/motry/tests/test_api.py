"""
API 端點測試

測試所有 AJAX API 端點的回應格式、狀態碼、權限控制。
"""

import json

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from apps.motry.models import (
    Vehicle,
    Post,
    Comment,
    UserVehicle,
    FavoriteVehicle,
    Rating,
)

User = get_user_model()


class VehicleListAPITests(TestCase):
    """車輛列表 API 測試"""

    def setUp(self):
        self.client = Client()
        # 創建測試車輛
        Vehicle.objects.create(brand="Toyota", model="Camry")
        Vehicle.objects.create(brand="Honda", model="Accord")
        Vehicle.objects.create(brand="Yamaha", model="R1")

    def test_vehicle_list_api_success(self):
        """測試車輛列表 API 回應"""
        response = self.client.get(reverse("api_vehicle_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("vehicles", data["data"])
        self.assertEqual(len(data["data"]["vehicles"]), 3)

    def test_vehicle_list_api_structure(self):
        """測試車輛列表 API 資料結構"""
        response = self.client.get(reverse("api_vehicle_list"))
        data = json.loads(response.content)

        vehicle = data["data"]["vehicles"][0]
        expected_fields = [
            "id",
            "brand",
            "model",
            "displacement_cc",
            "horsepower_ps",
            "cylinders",
        ]
        for field in expected_fields:
            self.assertIn(field, vehicle)


class GarageAPITests(TestCase):
    """車庫 API 測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="garageuser",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            
            brand="BMW",
            model="M3",
        )

    def test_garage_add_requires_login(self):
        """測試加入車庫需要登入"""
        response = self.client.post(
            reverse("api_garage_add", kwargs={"vehicle_id": self.vehicle.id})
        )
        # 未登入應該重定向到登入頁
        self.assertEqual(response.status_code, 302)

    def test_garage_add_success(self):
        """測試加入車庫成功"""
        self.client.login(username="garageuser", password="testpass123")
        response = self.client.post(
            reverse("api_garage_add", kwargs={"vehicle_id": self.vehicle.id})
        )
        self.assertEqual(response.status_code, 201)

        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertTrue(data["in_garage"])
        self.assertIn("user_vehicle_id", data)

        # 確認資料庫
        self.assertTrue(
            UserVehicle.objects.filter(user=self.user, vehicle=self.vehicle).exists()
        )

    def test_garage_add_duplicate(self):
        """測試重複加入車庫"""
        self.client.login(username="garageuser", password="testpass123")
        UserVehicle.objects.create(user=self.user, vehicle=self.vehicle)

        response = self.client.post(
            reverse("api_garage_add", kwargs={"vehicle_id": self.vehicle.id})
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertTrue(data["in_garage"])

    def test_garage_remove_success(self):
        """測試從車庫移除成功"""
        self.client.login(username="garageuser", password="testpass123")
        UserVehicle.objects.create(user=self.user, vehicle=self.vehicle)

        response = self.client.post(
            reverse("api_garage_remove", kwargs={"vehicle_id": self.vehicle.id})
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertFalse(data["in_garage"])

        # 確認資料庫
        self.assertFalse(
            UserVehicle.objects.filter(user=self.user, vehicle=self.vehicle).exists()
        )

    def test_garage_remove_not_found(self):
        """測試移除不存在的車庫項目"""
        self.client.login(username="garageuser", password="testpass123")

        response = self.client.post(
            reverse("api_garage_remove", kwargs={"vehicle_id": self.vehicle.id})
        )
        self.assertEqual(response.status_code, 404)

        data = json.loads(response.content)
        self.assertFalse(data["success"])


class FavoriteAPITests(TestCase):
    """最愛 API 測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="favuser",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            
            brand="Ducati",
            model="Monster",
        )

    def test_favorite_add_requires_login(self):
        """測試加入最愛需要登入"""
        response = self.client.post(
            reverse("api_favorite_add", kwargs={"vehicle_id": self.vehicle.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_favorite_add_success(self):
        """測試加入最愛成功"""
        self.client.login(username="favuser", password="testpass123")
        response = self.client.post(
            reverse("api_favorite_add", kwargs={"vehicle_id": self.vehicle.id})
        )
        self.assertEqual(response.status_code, 201)

        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertTrue(data["favorite"])
        self.assertIn("favorite_id", data)

    def test_favorite_add_duplicate(self):
        """測試重複加入最愛"""
        self.client.login(username="favuser", password="testpass123")
        FavoriteVehicle.objects.create(user=self.user, vehicle=self.vehicle)

        response = self.client.post(
            reverse("api_favorite_add", kwargs={"vehicle_id": self.vehicle.id})
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertFalse(data["success"])

    def test_favorite_remove_success(self):
        """測試從最愛移除成功"""
        self.client.login(username="favuser", password="testpass123")
        FavoriteVehicle.objects.create(user=self.user, vehicle=self.vehicle)

        response = self.client.post(
            reverse("api_favorite_remove", kwargs={"vehicle_id": self.vehicle.id})
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertFalse(data["favorite"])

    def test_favorite_remove_not_found(self):
        """測試移除不存在的最愛項目"""
        self.client.login(username="favuser", password="testpass123")

        response = self.client.post(
            reverse("api_favorite_remove", kwargs={"vehicle_id": self.vehicle.id})
        )
        self.assertEqual(response.status_code, 404)


class RatingAjaxAPITests(TestCase):
    """評分 AJAX API 測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="ajaxrater",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            
            brand="Porsche",
            model="Cayman",
        )

    def test_rating_ajax_requires_login(self):
        """測試 AJAX 評分需要登入"""
        response = self.client.post(
            reverse("rate_vehicle_ajax", kwargs={"id": self.vehicle.id}),
            {"score": "5"},
        )
        self.assertEqual(response.status_code, 302)

    def test_rating_ajax_success(self):
        """測試 AJAX 評分成功"""
        self.client.login(username="ajaxrater", password="testpass123")
        response = self.client.post(
            reverse("rate_vehicle_ajax", kwargs={"id": self.vehicle.id}),
            {"score": "5"},
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertTrue(data["created"])
        self.assertEqual(data["score"], 5)
        self.assertIn("avg_rating", data)
        self.assertIn("rating_count", data)

    def test_rating_ajax_update(self):
        """測試 AJAX 更新評分"""
        self.client.login(username="ajaxrater", password="testpass123")
        Rating.objects.create(vehicle=self.vehicle, user=self.user, score=3)

        response = self.client.post(
            reverse("rate_vehicle_ajax", kwargs={"id": self.vehicle.id}),
            {"score": "5"},
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertFalse(data["created"])  # 是更新，不是新建
        self.assertEqual(data["score"], 5)

    def test_rating_ajax_invalid_score(self):
        """測試 AJAX 無效評分"""
        self.client.login(username="ajaxrater", password="testpass123")
        response = self.client.post(
            reverse("rate_vehicle_ajax", kwargs={"id": self.vehicle.id}),
            {"score": "10"},  # 超過範圍
        )
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.content)
        self.assertFalse(data["success"])


class CommentAjaxAPITests(TestCase):
    """留言 AJAX API 測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="ajaxcommenter",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            
            brand="Ferrari",
            model="488",
        )
        self.post = Post.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            body_text="測試貼文",
        )

    def test_comment_ajax_requires_login(self):
        """測試 AJAX 留言需要登入"""
        response = self.client.post(
            reverse("comment_create_ajax"),
            {"post": self.post.id, "body_text": "AJAX 留言"},
        )
        self.assertEqual(response.status_code, 302)

    def test_comment_ajax_success(self):
        """測試 AJAX 留言成功"""
        self.client.login(username="ajaxcommenter", password="testpass123")
        response = self.client.post(
            reverse("comment_create_ajax"),
            {"post": self.post.id, "body_text": "這是 AJAX 留言"},
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("comment_id", data)
        self.assertIn("comment_html", data)

    def test_comment_ajax_nested_reply(self):
        """測試 AJAX 巢狀回覆"""
        self.client.login(username="ajaxcommenter", password="testpass123")
        parent_comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            body_text="父留言",
        )

        response = self.client.post(
            reverse("comment_create_ajax"),
            {
                "post": self.post.id,
                "body_text": "子留言",
                "parent": parent_comment.id,
            },
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["parent_id"], parent_comment.id)

    def test_comment_ajax_max_depth(self):
        """測試 AJAX 留言最大深度限制"""
        self.client.login(username="ajaxcommenter", password="testpass123")

        # 建立三層留言
        level0 = Comment.objects.create(
            post=self.post, user=self.user, body_text="Level 0"
        )
        level1 = Comment.objects.create(
            post=self.post, user=self.user, parent=level0, body_text="Level 1"
        )
        level2 = Comment.objects.create(
            post=self.post, user=self.user, parent=level1, body_text="Level 2"
        )

        # 嘗試在第三層回覆（應該被拒絕）
        response = self.client.post(
            reverse("comment_create_ajax"),
            {
                "post": self.post.id,
                "body_text": "Level 3 - 應該失敗",
                "parent": level2.id,
            },
        )
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.content)
        self.assertFalse(data["success"])


class ExportAPITests(TestCase):
    """匯出 API 測試"""

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
        # 創建測試車輛
        Vehicle.objects.create(brand="Tesla", model="Model S")

    def test_export_requires_staff(self):
        """測試匯出需要管理員權限"""
        self.client.login(username="normaluser", password="testpass123")
        response = self.client.post(reverse("export_vehicles_csv"))
        # 非管理員應該被重定向
        self.assertNotEqual(response.status_code, 200)

    def test_export_staff_success(self):
        """測試管理員匯出成功"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.post(reverse("export_vehicles_csv"))
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("task_id", data)

    def test_export_status_requires_staff(self):
        """測試查詢匯出狀態需要管理員權限"""
        self.client.login(username="normaluser", password="testpass123")
        response = self.client.get(
            reverse("export_task_status", kwargs={"task_id": "fake-task-id"})
        )
        self.assertNotEqual(response.status_code, 200)

    def test_export_status_staff_access(self):
        """測試管理員可查詢匯出狀態"""
        self.client.login(username="staffuser", password="testpass123")
        response = self.client.get(
            reverse("export_task_status", kwargs={"task_id": "fake-task-id"})
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn("task_id", data)
        self.assertIn("status", data)
