"""
Form 單元測試

測試所有表單的驗證邏輯、欄位約束。
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.motry.forms import (
    PostCreateForm,
    CommentCreateForm,
    VehicleCreateForm,
    UserVehicleForm,
    RatingForm,
    VehicleIntroForm,
    VehiclePhotoForm,
)
from apps.motry.models import Vehicle, Post, Comment, Tag, UserVehicle

User = get_user_model()


class PostCreateFormTests(TestCase):
    """PostCreateForm 測試"""

    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            type="car",
            brand="Toyota",
            model="Supra",
        )
        self.tag1 = Tag.objects.create(name="心得分享")
        self.tag2 = Tag.objects.create(name="開箱")
        self.tag3 = Tag.objects.create(name="改裝")
        self.tag4 = Tag.objects.create(name="維修")

    def test_valid_form(self):
        """測試有效表單"""
        form = PostCreateForm(
            data={
                "vehicle_id": self.vehicle.id,
                "body_text": "這是一篇測試心得",
                "tags": [self.tag1.id],
            }
        )
        self.assertTrue(form.is_valid())

    def test_body_text_required(self):
        """測試心得內容為必填"""
        form = PostCreateForm(
            data={
                "vehicle_id": self.vehicle.id,
                "body_text": "",
                "tags": [self.tag1.id],
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("body_text", form.errors)

    def test_tags_min_count(self):
        """測試標籤最少 1 個"""
        form = PostCreateForm(
            data={
                "vehicle_id": self.vehicle.id,
                "body_text": "測試內容",
                "tags": [],
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("tags", form.errors)

    def test_tags_max_count(self):
        """測試標籤最多 3 個"""
        form = PostCreateForm(
            data={
                "vehicle_id": self.vehicle.id,
                "body_text": "測試內容",
                "tags": [self.tag1.id, self.tag2.id, self.tag3.id, self.tag4.id],
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("tags", form.errors)

    def test_tags_valid_range(self):
        """測試標籤數量在有效範圍內"""
        form = PostCreateForm(
            data={
                "vehicle_id": self.vehicle.id,
                "body_text": "測試內容",
                "tags": [self.tag1.id, self.tag2.id, self.tag3.id],
            }
        )
        self.assertTrue(form.is_valid())

    def test_body_text_max_length(self):
        """測試心得內容最大長度"""
        form = PostCreateForm(
            data={
                "vehicle_id": self.vehicle.id,
                "body_text": "a" * 2001,  # 超過 2000 字
                "tags": [self.tag1.id],
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("body_text", form.errors)

    def test_user_vehicle_id_optional(self):
        """測試用戶車輛 ID 為選填"""
        form = PostCreateForm(
            data={
                "vehicle_id": self.vehicle.id,
                "body_text": "測試內容",
                "tags": [self.tag1.id],
                "user_vehicle_id": "",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["user_vehicle_id"])

    def test_images_method(self):
        """測試 images() 方法"""
        # 創建假圖片
        image = SimpleUploadedFile(
            "test.jpg",
            b"\x47\x49\x46\x38\x89\x61",  # GIF header
            content_type="image/jpeg",
        )
        form = PostCreateForm(
            data={
                "vehicle_id": self.vehicle.id,
                "body_text": "測試內容",
                "tags": [self.tag1.id],
            },
            files={"image_1": image},
        )
        if form.is_valid():
            images = form.images()
            self.assertEqual(len(images), 1)


class CommentCreateFormTests(TestCase):
    """CommentCreateForm 測試"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="commenter",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            type="car",
            brand="Honda",
            model="NSX",
        )
        self.post = Post.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            body_text="測試貼文",
        )

    def test_valid_form(self):
        """測試有效表單"""
        form = CommentCreateForm(
            data={
                "post": self.post.id,
                "body_text": "這是一則測試留言",
            }
        )
        self.assertTrue(form.is_valid())

    def test_body_text_required(self):
        """測試留言內容為必填"""
        form = CommentCreateForm(
            data={
                "post": self.post.id,
                "body_text": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("body_text", form.errors)

    def test_parent_belongs_to_post(self):
        """測試父留言必須屬於同一貼文"""
        other_post = Post.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            body_text="另一篇貼文",
        )
        other_comment = Comment.objects.create(
            post=other_post,
            user=self.user,
            body_text="其他貼文的留言",
        )

        form = CommentCreateForm(
            data={
                "post": self.post.id,
                "parent": other_comment.id,
                "body_text": "嘗試回覆其他貼文的留言",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("parent", form.errors)

    def test_valid_nested_reply(self):
        """測試有效的巢狀回覆"""
        parent_comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            body_text="父留言",
        )

        form = CommentCreateForm(
            data={
                "post": self.post.id,
                "parent": parent_comment.id,
                "body_text": "回覆留言",
            }
        )
        self.assertTrue(form.is_valid())


class VehicleCreateFormTests(TestCase):
    """VehicleCreateForm 測試"""

    def test_valid_car_form(self):
        """測試有效的汽車表單"""
        form = VehicleCreateForm(
            data={
                "type": "car",
                "brand": "BMW",
                "model": "M4",
                "generation": "G82",
                "years_from": 2021,
                "displacement_cc": 2993,
                "cylinders": 6,
                "horsepower_ps": 510,
            },
            selected_type="car",
        )
        self.assertTrue(form.is_valid())

    def test_valid_bike_form(self):
        """測試有效的機車表單"""
        form = VehicleCreateForm(
            data={
                "type": "bike",
                "brand": "Yamaha",
                "model": "YZF-R1",
                "years_from": 2020,
                "displacement_cc": 998,
                "cylinders": 4,
                "horsepower_ps": 200,
            },
            selected_type="bike",
        )
        self.assertTrue(form.is_valid())

    def test_model_required(self):
        """測試車型為必填"""
        form = VehicleCreateForm(
            data={
                "type": "car",
                "brand": "BMW",
                "model": "",
            },
            selected_type="car",
        )
        self.assertFalse(form.is_valid())
        self.assertIn("model", form.errors)

    def test_brand_choices_by_type(self):
        """測試品牌選項依類型變化"""
        car_form = VehicleCreateForm(selected_type="car")
        bike_form = VehicleCreateForm(selected_type="bike")

        car_brands = [choice[0] for choice in car_form.fields["brand"].choices]
        bike_brands = [choice[0] for choice in bike_form.fields["brand"].choices]

        self.assertIn("BMW", car_brands)
        self.assertIn("Yamaha", bike_brands)
        self.assertNotIn("Yamaha", car_brands)
        self.assertNotIn("BMW", bike_brands)


class UserVehicleFormTests(TestCase):
    """UserVehicleForm 測試"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            password="testpass123",
        )
        self.vehicle1 = Vehicle.objects.create(
            type="car",
            brand="Lexus",
            model="IS300",
        )
        self.vehicle2 = Vehicle.objects.create(
            type="car",
            brand="Lexus",
            model="RC350",
        )

    def test_valid_form(self):
        """測試有效表單"""
        form = UserVehicleForm(
            self.user,
            data={
                "vehicle": self.vehicle1.id,
                "alias": "我的小IS",
                "notes": "2020年購入",
            },
        )
        self.assertTrue(form.is_valid())

    def test_excludes_existing_vehicles(self):
        """測試排除已擁有的車輛"""
        UserVehicle.objects.create(user=self.user, vehicle=self.vehicle1)

        form = UserVehicleForm(self.user)
        vehicle_ids = [v.id for v in form.fields["vehicle"].queryset]

        self.assertNotIn(self.vehicle1.id, vehicle_ids)
        self.assertIn(self.vehicle2.id, vehicle_ids)

    def test_alias_optional(self):
        """測試別名為選填"""
        form = UserVehicleForm(
            self.user,
            data={
                "vehicle": self.vehicle1.id,
                "alias": "",
            },
        )
        self.assertTrue(form.is_valid())


class RatingFormTests(TestCase):
    """RatingForm 測試"""

    def test_valid_scores(self):
        """測試有效評分 (1-5)"""
        for score in range(1, 6):
            form = RatingForm(data={"score": str(score)})
            self.assertTrue(form.is_valid(), f"Score {score} should be valid")

    def test_invalid_score_zero(self):
        """測試無效評分 (0)"""
        form = RatingForm(data={"score": "0"})
        self.assertFalse(form.is_valid())

    def test_invalid_score_six(self):
        """測試無效評分 (6)"""
        form = RatingForm(data={"score": "6"})
        self.assertFalse(form.is_valid())

    def test_score_required(self):
        """測試評分為必填"""
        form = RatingForm(data={})
        self.assertFalse(form.is_valid())


class VehicleIntroFormTests(TestCase):
    """VehicleIntroForm 測試"""

    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            type="car",
            brand="Ferrari",
            model="488",
        )

    def test_valid_form(self):
        """測試有效表單"""
        form = VehicleIntroForm(
            data={"intro_md": "# 488 GTB\n\n這是一台經典的中置引擎跑車。"},
            instance=self.vehicle,
        )
        self.assertTrue(form.is_valid())

    def test_intro_optional(self):
        """測試簡介為選填"""
        form = VehicleIntroForm(
            data={"intro_md": ""},
            instance=self.vehicle,
        )
        self.assertTrue(form.is_valid())


class VehiclePhotoFormTests(TestCase):
    """VehiclePhotoForm 測試"""

    def test_requires_image_or_url(self):
        """測試必須提供圖片或 URL"""
        form = VehiclePhotoForm(
            data={
                "image": None,
                "image_url": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_valid_with_url(self):
        """測試只提供 URL 有效"""
        form = VehiclePhotoForm(
            data={
                "image_url": "https://example.com/car.jpg",
            }
        )
        self.assertTrue(form.is_valid())

    def test_valid_with_image(self):
        """測試只提供圖片有效"""
        # 創建有效的 JPEG 圖片（最小有效 JPEG）
        import io
        from PIL import Image

        img_io = io.BytesIO()
        img = Image.new("RGB", (100, 100), color="red")
        img.save(img_io, format="JPEG")
        img_io.seek(0)

        image = SimpleUploadedFile(
            "test.jpg",
            img_io.read(),
            content_type="image/jpeg",
        )
        form = VehiclePhotoForm(
            data={"image_url": ""},
            files={"image": image},
        )
        self.assertTrue(form.is_valid(), form.errors)
