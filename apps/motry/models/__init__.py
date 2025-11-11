from django.conf import settings
from django.db import models
from django.utils import timezone


class Vehicle(models.Model):
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


class VehicleImage(models.Model):
	vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="images")
	image_url = models.CharField(max_length=255)
	sort_order = models.SmallIntegerField(null=True, blank=True)

	class Meta:
		ordering = ["sort_order", "id"]

	def __str__(self) -> str:
		return f"{self.vehicle} image #{self.id}"


class Post(models.Model):
	vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="posts")
	user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="posts")
	body_text = models.TextField(max_length=2000)
	user_vehicle = models.ForeignKey("UserVehicle", null=True, blank=True, on_delete=models.SET_NULL, related_name="posts")
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"Post {self.id} on {self.vehicle}"


class PostImage(models.Model):
	post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
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
	post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
	user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="comments")
	body_text = models.TextField()
	image_url = models.URLField(blank=True)
	image = models.ImageField(upload_to="comments/%Y/%m/", blank=True, null=True)
	created_at = models.DateTimeField(default=timezone.now)
	
	@property
	def image_url_or_file(self):
		"""返回圖片URL或檔案URL"""
		if self.image:
			return self.image.url
		return self.image_url if self.image_url else ""

	class Meta:
		ordering = ["created_at", "id"]

	def __str__(self) -> str:
		return f"Comment {self.id} on post {self.post_id}"


class Tag(models.Model):
	name = models.CharField(max_length=30, unique=True)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name


class PostTag(models.Model):
	post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_tags")
	tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="tag_posts")

	class Meta:
		unique_together = ("post", "tag")

	def __str__(self) -> str:
		return f"Post {self.post_id} - Tag {self.tag_id}"


class Like(models.Model):
	post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes")
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		unique_together = ("post", "user")

	def __str__(self) -> str:
		return f"Like by {self.user_id} on {self.post_id}"


class Rating(models.Model):
	vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="ratings")
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings")
	score = models.SmallIntegerField()
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		unique_together = ("vehicle", "user")

	def __str__(self) -> str:
		return f"Rating {self.score} for {self.vehicle_id} by {self.user_id}"


class UserVehicle(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_vehicles")
	vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="user_vehicles")
	alias = models.CharField(max_length=100, blank=True)
	notes = models.TextField(blank=True)
	image_url = models.URLField(blank=True)
	image = models.ImageField(upload_to="user_vehicles/%Y/%m/", blank=True, null=True)
	created_at = models.DateTimeField(default=timezone.now)
	
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
