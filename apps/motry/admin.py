from django.contrib import admin
from .models import Vehicle, VehicleImage, Post, PostImage, Comment, Tag, PostTag, Like, Rating, UserVehicle, FavoriteVehicle


class VehicleImageInline(admin.TabularInline):
	model = VehicleImage
	extra = 1


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
	list_display = ("id", "brand", "model", "type", "years_from", "years_to")
	list_filter = ("type", "brand")
	search_fields = ("brand", "model")
	inlines = [VehicleImageInline]


class PostImageInline(admin.TabularInline):
	model = PostImage
	extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
	list_display = ("id", "vehicle", "user", "created_at")
	list_filter = ("vehicle",)
	search_fields = ("body_text",)
	inlines = [PostImageInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
	list_display = ("id", "post", "user", "created_at")
	search_fields = ("body_text",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
	list_display = ("id", "name")
	search_fields = ("name",)


@admin.register(PostTag)
class PostTagAdmin(admin.ModelAdmin):
	list_display = ("post", "tag")
	list_filter = ("tag",)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
	list_display = ("id", "post", "user", "created_at")
	list_filter = ("created_at",)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
	list_display = ("id", "vehicle", "user", "score", "created_at")
	list_filter = ("score",)


@admin.register(UserVehicle)
class UserVehicleAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "vehicle", "alias", "created_at")
	search_fields = ("user__username", "vehicle__brand", "vehicle__model", "alias")


@admin.register(FavoriteVehicle)
class FavoriteVehicleAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "vehicle", "created_at")
	search_fields = ("user__username", "vehicle__brand", "vehicle__model")
