"""
Model 單元測試

測試所有 Model 的建立、關聯、方法和約束條件。
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.motry.models import (
    Vehicle,
    VehicleImage,
    Post,
    PostImage,
    Comment,
    Tag,
    PostTag,
    Like,
    Rating,
    UserVehicle,
    FavoriteVehicle,
    Notification,
)

User = get_user_model()


class VehicleModelTests(TestCase):
    """Vehicle Model 測試"""

    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            brand="Honda",
            model="CB650R",
            generation="2019-",
            years_from=2019,
            years_to=2023,
            displacement_cc=649,
            cylinders=4,
            horsepower_ps=95,
            msrp_new=380000,
        )

    def test_vehicle_creation(self):
        """測試車輛建立"""
        self.assertEqual(self.vehicle.brand, "Honda")
        self.assertEqual(self.vehicle.model, "CB650R")

    def test_vehicle_str_with_generation(self):
        """測試 __str__ 方法（有世代）"""
        self.assertEqual(str(self.vehicle), "Honda CB650R (2019-)")

    def test_vehicle_str_without_generation(self):
        """測試 __str__ 方法（無世代）"""
        vehicle = Vehicle.objects.create(
            brand="Yamaha",
            model="MT-07",
        )
        self.assertEqual(str(vehicle), "Yamaha MT-07")

    def test_vehicle_optional_fields(self):
        """測試可選欄位可為空"""
        vehicle = Vehicle.objects.create(
            brand="Kawasaki",
            model="Ninja 400",
        )
        self.assertIsNone(vehicle.displacement_cc)
        self.assertIsNone(vehicle.horsepower_ps)
        self.assertEqual(vehicle.intro_md, "")


class VehicleImageModelTests(TestCase):
    """VehicleImage Model 測試"""

    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            brand="Yamaha",
            model="YZF-R6",
        )
        self.image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image_url="https://example.com/supra.jpg",
            sort_order=1,
        )

    def test_vehicle_image_relation(self):
        """測試圖片與車輛的關聯"""
        self.assertEqual(self.image.vehicle, self.vehicle)
        self.assertIn(self.image, self.vehicle.images.all())

    def test_image_url_or_file_property(self):
        """測試 image_url_or_file 屬性"""
        self.assertEqual(self.image.image_url_or_file, "https://example.com/supra.jpg")

    def test_has_real_image_with_url(self):
        """測試 has_real_image 屬性（有 URL）"""
        self.assertTrue(self.image.has_real_image)

    def test_has_real_image_without_url(self):
        """測試 has_real_image 屬性（無 URL）"""
        empty_image = VehicleImage.objects.create(
            vehicle=self.vehicle,
            image_url="",
        )
        self.assertFalse(empty_image.has_real_image)


class PostModelTests(TestCase):
    """Post Model 測試"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            brand="Honda",
            model="CBR600RR",
        )
        self.post = Post.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            body_text="這是一篇測試心得文章",
        )

    def test_post_creation(self):
        """測試貼文建立"""
        self.assertEqual(self.post.vehicle, self.vehicle)
        self.assertEqual(self.post.user, self.user)
        self.assertFalse(self.post.is_deleted)

    def test_post_str(self):
        """測試 __str__ 方法"""
        self.assertIn("Post", str(self.post))
        self.assertIn(str(self.post.id), str(self.post))

    def test_post_soft_delete(self):
        """測試軟刪除"""
        self.post.is_deleted = True
        self.post.save()
        self.assertTrue(Post.objects.get(pk=self.post.pk).is_deleted)

    def test_post_user_nullable(self):
        """測試用戶可為空（用戶刪除後保留貼文）"""
        post = Post.objects.create(
            vehicle=self.vehicle,
            user=None,
            body_text="匿名貼文",
        )
        self.assertIsNone(post.user)


class CommentModelTests(TestCase):
    """Comment Model 測試（巢狀留言）"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="commenter",
            email="commenter@example.com",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            brand="Yamaha",
            model="MT-07",
        )
        self.post = Post.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            body_text="測試貼文",
        )
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user,
            body_text="這是第一層留言",
        )

    def test_comment_creation(self):
        """測試留言建立"""
        self.assertEqual(self.comment.post, self.post)
        self.assertEqual(self.comment.user, self.user)
        self.assertIsNone(self.comment.parent)

    def test_comment_depth_level_0(self):
        """測試留言深度 - 第一層"""
        self.assertEqual(self.comment.get_depth(), 0)
        self.assertTrue(self.comment.can_reply())

    def test_comment_depth_level_1(self):
        """測試留言深度 - 第二層"""
        reply = Comment.objects.create(
            post=self.post,
            user=self.user,
            parent=self.comment,
            body_text="這是第二層回覆",
        )
        self.assertEqual(reply.get_depth(), 1)
        self.assertTrue(reply.can_reply())

    def test_comment_depth_level_2(self):
        """測試留言深度 - 第三層（最大深度）"""
        level1 = Comment.objects.create(
            post=self.post,
            user=self.user,
            parent=self.comment,
            body_text="第二層",
        )
        level2 = Comment.objects.create(
            post=self.post,
            user=self.user,
            parent=level1,
            body_text="第三層",
        )
        self.assertEqual(level2.get_depth(), 2)
        self.assertFalse(level2.can_reply())  # 不能再回覆

    def test_comment_soft_delete(self):
        """測試留言軟刪除"""
        self.comment.is_deleted = True
        self.comment.save()
        self.assertTrue(Comment.objects.get(pk=self.comment.pk).is_deleted)


class TagModelTests(TestCase):
    """Tag Model 測試"""

    def test_tag_creation(self):
        """測試標籤建立"""
        tag = Tag.objects.create(name="心得分享")
        self.assertEqual(str(tag), "心得分享")

    def test_tag_unique_constraint(self):
        """測試標籤名稱唯一約束"""
        Tag.objects.create(name="開箱")
        with self.assertRaises(IntegrityError):
            Tag.objects.create(name="開箱")


class PostTagModelTests(TestCase):
    """PostTag Model 測試"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="tagger",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            brand="Suzuki",
            model="GSX-R1000",
        )
        self.post = Post.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            body_text="測試貼文",
        )
        self.tag = Tag.objects.create(name="跑車")

    def test_post_tag_creation(self):
        """測試貼文標籤關聯建立"""
        post_tag = PostTag.objects.create(post=self.post, tag=self.tag)
        self.assertEqual(post_tag.post, self.post)
        self.assertEqual(post_tag.tag, self.tag)

    def test_post_tag_unique_together(self):
        """測試同一貼文不能重複標籤"""
        PostTag.objects.create(post=self.post, tag=self.tag)
        with self.assertRaises(IntegrityError):
            PostTag.objects.create(post=self.post, tag=self.tag)


class LikeModelTests(TestCase):
    """Like Model 測試"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="liker",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            
            brand="Tesla",
            model="Model 3",
        )
        self.post = Post.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            body_text="測試貼文",
        )

    def test_like_creation(self):
        """測試按讚建立"""
        like = Like.objects.create(post=self.post, user=self.user)
        self.assertEqual(like.post, self.post)
        self.assertEqual(like.user, self.user)

    def test_like_unique_together(self):
        """測試同一用戶不能重複按讚"""
        Like.objects.create(post=self.post, user=self.user)
        with self.assertRaises(IntegrityError):
            Like.objects.create(post=self.post, user=self.user)

    def test_like_count(self):
        """測試按讚計數"""
        user2 = User.objects.create_user(username="liker2", password="testpass123")
        Like.objects.create(post=self.post, user=self.user)
        Like.objects.create(post=self.post, user=user2)
        self.assertEqual(self.post.likes.count(), 2)


class RatingModelTests(TestCase):
    """Rating Model 測試"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="rater",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            
            brand="Porsche",
            model="911",
        )

    def test_rating_creation(self):
        """測試評分建立"""
        rating = Rating.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            score=5,
        )
        self.assertEqual(rating.score, 5)

    def test_rating_unique_together(self):
        """測試同一用戶對同一車輛只能評一次分"""
        Rating.objects.create(vehicle=self.vehicle, user=self.user, score=4)
        with self.assertRaises(IntegrityError):
            Rating.objects.create(vehicle=self.vehicle, user=self.user, score=5)

    def test_rating_score_range(self):
        """測試評分範圍驗證 (1-5)"""
        rating = Rating(vehicle=self.vehicle, user=self.user, score=6)
        with self.assertRaises(ValidationError):
            rating.full_clean()

        rating.score = 0
        with self.assertRaises(ValidationError):
            rating.full_clean()

    def test_rating_update(self):
        """測試評分更新"""
        rating = Rating.objects.create(
            vehicle=self.vehicle,
            user=self.user,
            score=3,
        )
        rating.score = 5
        rating.save()
        self.assertEqual(Rating.objects.get(pk=rating.pk).score, 5)


class UserVehicleModelTests(TestCase):
    """UserVehicle Model 測試（我的車庫）"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            
            brand="Lexus",
            model="IS300",
        )

    def test_user_vehicle_creation(self):
        """測試車庫收藏建立"""
        uv = UserVehicle.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            alias="我的小IS",
            notes="2020年購入",
        )
        self.assertEqual(uv.alias, "我的小IS")
        self.assertEqual(uv.vehicle, self.vehicle)

    def test_user_vehicle_unique_together(self):
        """測試同一車輛不能重複加入車庫"""
        UserVehicle.objects.create(user=self.user, vehicle=self.vehicle)
        with self.assertRaises(IntegrityError):
            UserVehicle.objects.create(user=self.user, vehicle=self.vehicle)

    def test_user_vehicle_str_with_alias(self):
        """測試 __str__ 方法（有別名）"""
        uv = UserVehicle.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            alias="小IS",
        )
        self.assertIn("小IS", str(uv))

    def test_user_vehicle_str_without_alias(self):
        """測試 __str__ 方法（無別名）"""
        uv = UserVehicle.objects.create(
            user=self.user,
            vehicle=self.vehicle,
        )
        self.assertIn("Lexus", str(uv))


class FavoriteVehicleModelTests(TestCase):
    """FavoriteVehicle Model 測試（我的最愛）"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="fan",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            
            brand="Ducati",
            model="Panigale V4",
        )

    def test_favorite_creation(self):
        """測試最愛建立"""
        fav = FavoriteVehicle.objects.create(
            user=self.user,
            vehicle=self.vehicle,
        )
        self.assertEqual(fav.user, self.user)
        self.assertEqual(fav.vehicle, self.vehicle)

    def test_favorite_unique_together(self):
        """測試同一車輛不能重複加入最愛"""
        FavoriteVehicle.objects.create(user=self.user, vehicle=self.vehicle)
        with self.assertRaises(IntegrityError):
            FavoriteVehicle.objects.create(user=self.user, vehicle=self.vehicle)

    def test_favorite_str(self):
        """測試 __str__ 方法"""
        fav = FavoriteVehicle.objects.create(user=self.user, vehicle=self.vehicle)
        self.assertIn("♥", str(fav))


class NotificationModelTests(TestCase):
    """Notification Model 測試"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="receiver",
            password="testpass123",
        )

    def test_notification_creation(self):
        """測試通知建立"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type=Notification.NotificationType.NEW_POST,
            title="新貼文通知",
            message="有人在你收藏的車款發表了新心得",
        )
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.notification_type, "new_post")

    def test_notification_mark_as_read(self):
        """測試標記為已讀"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type=Notification.NotificationType.SYSTEM,
            title="系統通知",
            message="歡迎加入 Motry！",
        )
        notification.is_read = True
        notification.save()
        self.assertTrue(Notification.objects.get(pk=notification.pk).is_read)

    def test_notification_types(self):
        """測試通知類型選項"""
        types = [choice[0] for choice in Notification.NotificationType.choices]
        self.assertIn("new_post", types)
        self.assertIn("new_comment", types)
        self.assertIn("new_like", types)
        self.assertIn("system", types)
