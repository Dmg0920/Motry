from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from apps.motry.utils import is_placeholder_image


class Vehicle(models.Model):
	"""核心車輛資料表（Week 5/6 範例：一對多/多對多的中心實體）。"""

	type = models.CharField(max_length=10)  # car/bike
	brand = models.CharField(max_length=50)
	model = models.CharField(max_length=100)
	generation = models.CharField(max_length=50, blank=True)
	years_from = models.SmallIntegerField(null=True, blank=True)
	years_to = models.SmallIntegerField(null=True, blank=True)
	displacement_cc = models.IntegerField(null=True, blank=True)
	cylinders = models.SmallIntegerField(null=True, blank=True)
	horsepower_ps = models.IntegerField(null=True, blank=True)
	msrp_new = models.IntegerField(null=True, blank=True)
	used_price_min = models.IntegerField(null=True, blank=True)
	used_price_max = models.IntegerField(null=True, blank=True)
	intro_md = models.TextField(blank=True)
	cover_url = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"{self.brand} {self.model} ({self.generation})" if self.generation else f"{self.brand} {self.model}"

	def get_gallery_images(self):
		if not hasattr(self, "_gallery_images_cache"):
			self._gallery_images_cache = [img for img in self.images.all() if getattr(img, "has_real_image", False)]
		return self._gallery_images_cache


class VehicleImage(models.Model):
	"""車輛圖片（外鍵一對多示範）。"""

	vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="images", db_index=True)
	image_url = models.CharField(max_length=255, blank=True)
	image = models.ImageField(upload_to="vehicles/%Y/%m/", blank=True, null=True)
	sort_order = models.SmallIntegerField(null=True, blank=True)

	class Meta:
		ordering = ["sort_order", "id"]

	def __str__(self) -> str:
		return f"{self.vehicle} image #{self.id}"

	@property
	def image_url_or_file(self):
		if self.image:
			return self.image.url
		return self.image_url or ""

	@property
	def has_real_image(self) -> bool:
		if self.image:
			return True
		return bool(self.image_url and not is_placeholder_image(self.image_url))


class Post(models.Model):
	"""車輛心得貼文（Week 7 CRUD 示範）。"""

	vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="posts", db_index=True)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="posts", db_index=True)
	body_text = models.TextField(max_length=2000)
	user_vehicle = models.ForeignKey("UserVehicle", null=True, blank=True, on_delete=models.SET_NULL, related_name="posts")
	created_at = models.DateTimeField(default=timezone.now, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_deleted = models.BooleanField(default=False, db_index=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"Post {self.id} on {self.vehicle}"


class PostImage(models.Model):
	"""貼文附圖。"""

	post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images", db_index=True)
	image_url = models.CharField(max_length=255, blank=True)
	image = models.ImageField(upload_to="posts/%Y/%m/", blank=True, null=True)

	def __str__(self) -> str:
		return f"Post {self.post_id} image #{self.id}"
	
	@property
	def image_url_or_file(self):
		"""返回圖片URL或檔案URL"""
		if self.image:
			return self.image.url
		return self.image_url if self.image_url else ""


class Comment(models.Model):
	"""巢狀留言（Post → Comment,支援最多三層）。"""

	post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments", db_index=True)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="comments", db_index=True)
	parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
	body_text = models.TextField()
	image_url = models.URLField(blank=True)
	image = models.ImageField(upload_to="comments/%Y/%m/", blank=True, null=True)
	created_at = models.DateTimeField(default=timezone.now, db_index=True)
	is_deleted = models.BooleanField(default=False, db_index=True)

	@property
	def image_url_or_file(self):
		"""返回圖片URL或檔案URL"""
		if self.image:
			return self.image.url
		return self.image_url if self.image_url else ""

	def get_depth(self):
		"""計算留言的層級深度"""
		depth = 0
		current = self.parent
		while current is not None:
			depth += 1
			current = current.parent
		return depth

	def can_reply(self):
		"""檢查是否可以回覆（最多三層，深度為0,1,2）"""
		return self.get_depth() < 2

	class Meta:
		ordering = ["created_at", "id"]

	def __str__(self) -> str:
		return f"Comment {self.id} on post {self.post_id}"


class Tag(models.Model):
	"""標籤（與 Post 多對多）。"""

	name = models.CharField(max_length=30, unique=True)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name


class PostTag(models.Model):
	"""Post-Tag 中介表（顯式 through model）。"""

	post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_tags", db_index=True)
	tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="tag_posts", db_index=True)

	class Meta:
		unique_together = ("post", "tag")

	def __str__(self) -> str:
		return f"Post {self.post_id} - Tag {self.tag_id}"


class Like(models.Model):
	"""按讚紀錄（Post 一對多，每人限制一筆）。"""

	post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes", db_index=True)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes", db_index=True)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		unique_together = ("post", "user")

	def __str__(self) -> str:
		return f"Like by {self.user_id} on {self.post_id}"


class Rating(models.Model):
	"""車輛評分（Vehicle 一對多，使用 unique_together 限制一人一分）。"""

	vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="ratings", db_index=True)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings", db_index=True)
	score = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		unique_together = ("vehicle", "user")

	def __str__(self) -> str:
		return f"Rating {self.score} for {self.vehicle_id} by {self.user_id}"


class UserVehicle(models.Model):
	"""使用者車庫收藏（Week 10 閱讀清單概念對應）。"""

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_vehicles", db_index=True)
	vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="user_vehicles", db_index=True)
	alias = models.CharField(max_length=100, blank=True)
	notes = models.TextField(blank=True)
	image_url = models.URLField(blank=True)
	image = models.ImageField(upload_to="user_vehicles/%Y/%m/", blank=True, null=True)
	created_at = models.DateTimeField(default=timezone.now, db_index=True)
	
	@property
	def image_url_or_file(self):
		"""返回圖片URL或檔案URL"""
		if self.image:
			return self.image.url
		return self.image_url if self.image_url else ""

	class Meta:
		unique_together = ("user", "vehicle")
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"{self.user} - {self.alias or self.vehicle}"


class FavoriteVehicle(models.Model):
	"""使用者我的最愛清單（與車庫不同，僅標記喜歡的車款）。"""

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_vehicles", db_index=True)
	vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="favorited_by", db_index=True)
	created_at = models.DateTimeField(default=timezone.now, db_index=True)

	class Meta:
		unique_together = ("user", "vehicle")
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"{self.user} ♥ {self.vehicle}"


class Notification(models.Model):
	"""使用者通知（持久化 WebSocket 通知，讓離線用戶也能收到）。"""

	class NotificationType(models.TextChoices):
		NEW_POST = "new_post", "新貼文"
		NEW_COMMENT = "new_comment", "新留言"
		NEW_LIKE = "new_like", "新按讚"
		SYSTEM = "system", "系統通知"

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="notifications",
		db_index=True,
	)
	notification_type = models.CharField(
		max_length=20,
		choices=NotificationType.choices,
		default=NotificationType.SYSTEM,
		db_index=True,
	)
	title = models.CharField(max_length=100)
	message = models.TextField(max_length=500)
	related_post = models.ForeignKey(
		Post, null=True, blank=True, on_delete=models.CASCADE, related_name="notifications"
	)
	related_vehicle = models.ForeignKey(
		Vehicle, null=True, blank=True, on_delete=models.CASCADE, related_name="notifications"
	)
	is_read = models.BooleanField(default=False, db_index=True)
	created_at = models.DateTimeField(default=timezone.now, db_index=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"Notification for {self.user}: {self.title}"
