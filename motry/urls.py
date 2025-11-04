from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
	path("search", views.search, name="search"),
	path("vehicle/new/", views.vehicle_create, name="vehicle_create"),
	path("vehicle/<int:id>/", views.vehicle_detail, name="vehicle_detail"),
	path("post/new", views.post_create, name="post_create"),
	path("comment/new", views.comment_create, name="comment_create"),
	path("vehicle/<int:id>/rate/", views.rate_vehicle, name="rate_vehicle"),
	path("post/<int:post_id>/delete/", views.post_delete, name="post_delete"),
	path("comment/<int:comment_id>/delete/", views.comment_delete, name="comment_delete"),
	path("like/toggle/<int:post_id>/", views.like_toggle, name="like_toggle"),
	path("garage/", views.user_garage, name="user_garage"),
	path("garage/<int:user_vehicle_id>/delete/", views.user_vehicle_delete, name="user_vehicle_delete"),
	path("auth/register/", views.register, name="register"),
	path("auth/login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
	path("auth/logout/", auth_views.LogoutView.as_view(), name="logout"),
]
