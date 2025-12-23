from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from apps.accounts.forms import CustomUserCreationForm
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, Max, Q, Prefetch
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from celery.result import AsyncResult
from .forms import (
	PostCreateForm,
	CommentCreateForm,
	VehicleCreateForm,
	UserVehicleForm,
	RatingForm,
	VehicleIntroForm,
	VehiclePhotoForm,
)
from .models import (
	Vehicle,
	Post,
	PostImage,
	Comment,
	PostTag,
	Like,
	UserVehicle,
	FavoriteVehicle,
	Rating,
)


VEHICLE_LIST_CACHE_KEY = "api:vehicle_list"
VEHICLE_LIST_CACHE_TIMEOUT = 60  # seconds


def _vehicle_detail_queryset():
	return Vehicle.objects.annotate(
		avg_rating=Avg("ratings__score"),
		rating_count=Count("ratings"),
	).prefetch_related(
		"images",
		Prefetch(
			"posts",
			queryset=Post.objects.filter(is_deleted=False)
			.select_related("vehicle", "user")
			.prefetch_related(
				"images",
				"post_tags__tag",
				Prefetch(
					"comments",
					queryset=Comment.objects.filter(is_deleted=False)
					.select_related("user")
					.prefetch_related("replies__user")
					.order_by("created_at"),
				),
			)
			.annotate(num_likes=Count("likes"), num_comments=Count("comments"))
			.order_by("-created_at"),
		),
	)


def _build_vehicle_detail_context(
	request: HttpRequest,
	vehicle: Vehicle,
	intro_form: VehicleIntroForm | None = None,
	photo_form: VehiclePhotoForm | None = None,
) -> dict:
	post_form = PostCreateForm(initial={"vehicle_id": vehicle.id}) if request.user.is_authenticated else None
	comment_form = CommentCreateForm() if request.user.is_authenticated else None

	user_rating = None
	rating_form = None
	if request.user.is_authenticated:
		user_rating = Rating.objects.filter(vehicle=vehicle, user=request.user).first()
		initial_score = str(user_rating.score) if user_rating else ""
		rating_form = RatingForm(initial={"score": initial_score})

	user_vehicle_entry = None
	favorite_entry = None
	if request.user.is_authenticated:
		user_vehicle_entry = UserVehicle.objects.filter(user=request.user, vehicle=vehicle).first()
		favorite_entry = FavoriteVehicle.objects.filter(user=request.user, vehicle=vehicle).first()

	gallery_images = vehicle.get_gallery_images()

	return {
		"vehicle": vehicle,
		"post_form": post_form,
		"comment_form": comment_form,
		"user_rating": user_rating,
		"rating_form": rating_form,
		"user_vehicle_entry": user_vehicle_entry,
		"favorite_entry": favorite_entry,
		"intro_form": intro_form or VehicleIntroForm(instance=vehicle),
		"photo_form": photo_form or VehiclePhotoForm(),
		"gallery_images": gallery_images,
	}


@ensure_csrf_cookie
def search(request: HttpRequest) -> HttpResponse:
	query = request.GET.get("query", "").strip()
	brand = request.GET.get("brand", "").strip()
	displacement_min = request.GET.get("displacement_min", "").strip()
	displacement_max = request.GET.get("displacement_max", "").strip()
	hp_min = request.GET.get("hp_min", "").strip()
	hp_max = request.GET.get("hp_max", "").strip()
	cylinders = request.GET.get("cylinders", "").strip()

	qs = Vehicle.objects.all()
	if query:
		qs = qs.filter(Q(brand__icontains=query) | Q(model__icontains=query))
	if brand:
		qs = qs.filter(brand__icontains=brand)
	if displacement_min:
		try:
			qs = qs.filter(displacement_cc__gte=int(displacement_min))
		except ValueError:
			pass
	if displacement_max:
		try:
			qs = qs.filter(displacement_cc__lte=int(displacement_max))
		except ValueError:
			pass
	if hp_min:
		try:
			qs = qs.filter(horsepower_ps__gte=int(hp_min))
		except ValueError:
			pass
	if hp_max:
		try:
			qs = qs.filter(horsepower_ps__lte=int(hp_max))
		except ValueError:
			pass
	if cylinders:
		try:
			cyl_values = [int(c.strip()) for c in cylinders.split(",") if c.strip()]
			if cyl_values:
				qs = qs.filter(cylinders__in=cyl_values)
		except ValueError:
			pass

	qs = qs.prefetch_related("images").order_by("brand", "model")
	# 分頁設定
	page_number = request.GET.get("page") or 1
	paginator = Paginator(qs, 20)
	page_obj = paginator.get_page(page_number)

	context = {
		"vehicles": page_obj.object_list,
		"page_obj": page_obj,
		"query": query,
		"brand": brand,
		"displacement_min": displacement_min,
		"displacement_max": displacement_max,
		"hp_min": hp_min,
		"hp_max": hp_max,
		"cylinders": cylinders,
	}
	return render(request, "motry/search_results.html", context)


def vehicle_detail(request: HttpRequest, id: int) -> HttpResponse:
	vehicle = get_object_or_404(_vehicle_detail_queryset(), pk=id)
	context = _build_vehicle_detail_context(request, vehicle)
	return render(request, "motry/vehicle_detail.html", context)


@login_required
def vehicle_create(request: HttpRequest) -> HttpResponse:
	if request.method == "POST":
		form = VehicleCreateForm(request.POST)
		if form.is_valid():
			vehicle = form.save()
			messages.success(request, "車款已建立！")
			return redirect("vehicle_detail", id=vehicle.id)
	else:
		form = VehicleCreateForm()
	return render(request, "motry/vehicle_form.html", {"form": form})


@login_required
def vehicle_intro_update(request: HttpRequest, id: int) -> HttpResponse:
	if request.method != "POST":
		return redirect("vehicle_detail", id=id)

	vehicle = get_object_or_404(_vehicle_detail_queryset(), pk=id)
	form = VehicleIntroForm(request.POST, instance=vehicle)
	if form.is_valid():
		form.save()
		messages.success(request, "感謝補充！車輛簡介已更新，稍後就能在頁面上看到變更。")
		return redirect("vehicle_detail", id=id)

	context = _build_vehicle_detail_context(request, vehicle, intro_form=form)
	return render(request, "motry/vehicle_detail.html", context)


@login_required
def vehicle_photo_upload(request: HttpRequest, id: int) -> HttpResponse:
	if request.method != "POST":
		return redirect("vehicle_detail", id=id)

	vehicle = get_object_or_404(_vehicle_detail_queryset(), pk=id)
	form = VehiclePhotoForm(request.POST, request.FILES)
	if form.is_valid():
		photo = form.save(commit=False)
		photo.vehicle = vehicle
		if photo.sort_order is None:
			next_order = vehicle.images.aggregate(Max("sort_order")).get("sort_order__max") or 0
			photo.sort_order = next_order + 1
		photo.save()
		messages.success(request, "已收到車輛美照！感謝你的分享。")
		return redirect("vehicle_detail", id=id)

	context = _build_vehicle_detail_context(request, vehicle, photo_form=form)
	return render(request, "motry/vehicle_detail.html", context)


@login_required
@ratelimit(key='user', rate='10/m', method='POST', block=True)
def post_create(request: HttpRequest) -> HttpResponse:
	user = request.user
	user_vehicles = list(user.user_vehicles.select_related("vehicle").order_by("vehicle__brand", "vehicle__model"))

	if request.method != "POST":
		vehicle_id = request.GET.get("vehicle")
		selected_user_vehicle = None
		user_vehicle_param = request.GET.get("user_vehicle")

		if user_vehicle_param:
			selected_user_vehicle = next((uv for uv in user_vehicles if str(uv.id) == user_vehicle_param), None)
			if selected_user_vehicle:
				vehicle_id = selected_user_vehicle.vehicle_id

		initial = {}
		if vehicle_id:
			initial["vehicle_id"] = vehicle_id
		if selected_user_vehicle:
			initial["user_vehicle_id"] = selected_user_vehicle.id

		form = PostCreateForm(initial=initial)
		_prepare_user_vehicle_field(form, user_vehicles)
		selected_vehicle = Vehicle.objects.filter(pk=vehicle_id).first() if vehicle_id else None
		return render(
			request,
			"motry/post_form.html",
			{
				"form": form,
				"user_vehicles": user_vehicles,
				"selected_user_vehicle": selected_user_vehicle,
				"selected_vehicle": selected_vehicle,
			},
		)

	post_data = request.POST.copy()
	user_vehicle_id = post_data.get("user_vehicle_id")
	selected_user_vehicle = None
	if user_vehicle_id:
		selected_user_vehicle = next((uv for uv in user_vehicles if str(uv.id) == user_vehicle_id), None)
		if selected_user_vehicle and not post_data.get("vehicle_id"):
			post_data["vehicle_id"] = str(selected_user_vehicle.vehicle_id)

	form = PostCreateForm(post_data, request.FILES)
	_prepare_user_vehicle_field(form, user_vehicles)

	if not form.is_valid():
		selected_vehicle = None
		vehicle_id = form.data.get("vehicle_id")
		if vehicle_id:
			selected_vehicle = Vehicle.objects.filter(pk=vehicle_id).first()
		return render(
			request,
			"motry/post_form.html",
			{
				"form": form,
				"user_vehicles": user_vehicles,
				"selected_user_vehicle": selected_user_vehicle,
				"selected_vehicle": selected_vehicle,
			},
		)

	vehicle = get_object_or_404(Vehicle, pk=form.cleaned_data["vehicle_id"])
	user_vehicle = None
	user_vehicle_clean = form.cleaned_data.get("user_vehicle_id")
	if user_vehicle_clean:
		user_vehicle = next((uv for uv in user_vehicles if uv.id == user_vehicle_clean), None)

	# 使用交易保護，確保貼文、標籤、圖片都成功建立
	with transaction.atomic():
		post = Post.objects.create(
			vehicle=vehicle,
			user=user,
			user_vehicle=user_vehicle,
			body_text=form.cleaned_data["body_text"],
		)

		for tag in form.cleaned_data["tags"]:
			PostTag.objects.create(post=post, tag=tag)

		for img_file in form.images():
			PostImage.objects.create(post=post, image=img_file)

	messages.success(request, "貼文已建立！")
	return redirect("vehicle_detail", id=vehicle.id)


@login_required
@ratelimit(key='user', rate='20/m', method='POST', block=True)
def comment_create(request: HttpRequest) -> HttpResponse:
	if request.method != "POST":
		return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

	form = CommentCreateForm(request.POST, request.FILES)
	if not form.is_valid():
		messages.error(request, "留言失敗")
		return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

	comment: Comment = form.save(commit=False)
	comment.user = request.user
	# 如果上傳了圖片檔案，優先使用檔案
	if form.cleaned_data.get("image"):
		comment.image = form.cleaned_data["image"]
		comment.image_url = ""  # 清除URL，使用檔案
	comment.save()
	messages.success(request, "留言已送出！")
	return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required
@require_POST
def post_delete(request: HttpRequest, post_id: int) -> HttpResponse:
	post = get_object_or_404(Post.objects.select_related("vehicle", "user"), pk=post_id)
	fallback = reverse("vehicle_detail", args=[post.vehicle_id])
	redirect_candidate = request.POST.get("next") or request.META.get("HTTP_REFERER")
	redirect_url = _safe_redirect(request, redirect_candidate, fallback)

	if not (post.user_id == request.user.id or request.user.is_staff):
		messages.error(request, "沒有權限刪除這篇貼文。")
		return HttpResponseRedirect(redirect_url)

	# 軟刪除：標記為已刪除而非真正刪除
	post.is_deleted = True
	post.save(update_fields=["is_deleted"])
	messages.success(request, "貼文已刪除。")
	return HttpResponseRedirect(redirect_url)


@login_required
@require_POST
def comment_delete(request: HttpRequest, comment_id: int) -> HttpResponse:
	comment = get_object_or_404(Comment.objects.select_related("post", "user"), pk=comment_id)
	fallback = reverse("vehicle_detail", args=[comment.post.vehicle_id])
	redirect_candidate = request.POST.get("next") or request.META.get("HTTP_REFERER")
	redirect_url = _safe_redirect(request, redirect_candidate, fallback)

	if not (comment.user_id == request.user.id or request.user.is_staff):
		messages.error(request, "沒有權限刪除這則留言。")
		return HttpResponseRedirect(redirect_url)

	# 軟刪除：標記為已刪除而非真正刪除
	comment.is_deleted = True
	comment.save(update_fields=["is_deleted"])
	messages.success(request, "留言已刪除。")
	return HttpResponseRedirect(redirect_url)


@login_required
@ratelimit(key='user', rate='30/m', method='POST', block=True)
def rate_vehicle(request: HttpRequest, id: int) -> HttpResponse:
	vehicle = get_object_or_404(Vehicle, pk=id)
	fallback = reverse("vehicle_detail", args=[vehicle.id])
	redirect_candidate = request.POST.get("next") or request.META.get("HTTP_REFERER")
	redirect_url = _safe_redirect(request, redirect_candidate, fallback)

	if request.method != "POST":
		return HttpResponseRedirect(redirect_url)

	form = RatingForm(request.POST)
	if not form.is_valid():
		for error in form.errors.get("score", []):
			messages.error(request, error)
		return HttpResponseRedirect(redirect_url)

	score = int(form.cleaned_data["score"])
	_, created = Rating.objects.update_or_create(
		vehicle=vehicle,
		user=request.user,
		defaults={"score": score},
	)
	messages.success(request, "評分已更新！" if not created else "感謝你的評分！")
	return HttpResponseRedirect(redirect_url)


@login_required
@ratelimit(key='user', rate='60/m', method=['GET', 'POST'], block=True)
def like_toggle(request: HttpRequest, post_id: int) -> HttpResponse:
	post = get_object_or_404(Post, pk=post_id)
	existing = Like.objects.filter(post=post, user=request.user).first()
	if existing:
		existing.delete()
		messages.info(request, "已取消按讚")
	else:
		Like.objects.create(post=post, user=request.user)
		messages.success(request, "已按讚！")
	return HttpResponseRedirect(request.META.get("HTTP_REFERER", reverse("vehicle_detail", args=[post.vehicle_id])))


@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def register(request: HttpRequest) -> HttpResponse:
	if request.user.is_authenticated:
		return redirect("core:home")

	if request.method == "POST":
		form = CustomUserCreationForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user, backend='django.contrib.auth.backends.ModelBackend')
			messages.success(request, "註冊成功，歡迎加入 Motry！")
			return redirect("core:home")
	else:
		form = CustomUserCreationForm()

	return render(request, "motry/auth/register.html", {"form": form})


@login_required
def user_garage(request: HttpRequest) -> HttpResponse:
	user = request.user
	user_vehicles = user.user_vehicles.select_related("vehicle").prefetch_related("vehicle__images").order_by("-created_at")
	form = UserVehicleForm(user, request.POST or None, request.FILES or None)
	can_add = form.fields["vehicle"].queryset.exists()
	if request.method == "POST" and form.is_valid():
		garage = form.save(commit=False)
		garage.user = user
		# 如果上傳了圖片檔案，優先使用檔案
		if form.cleaned_data.get("image"):
			garage.image = form.cleaned_data["image"]
			garage.image_url = ""  # 清除URL，使用檔案
		garage.save()
		messages.success(request, "已將車輛加入我的車庫！")
		return redirect("user_garage")

	return render(
		request,
		"motry/garage.html",
		{
			"form": form,
			"user_vehicles": user_vehicles,
			"can_add": can_add,
		},
	)


@login_required
def user_vehicle_delete(request: HttpRequest, user_vehicle_id: int) -> HttpResponse:
	user_vehicle = get_object_or_404(UserVehicle.objects.select_related("vehicle"), pk=user_vehicle_id)
	
	if user_vehicle.user_id != request.user.id:
		messages.error(request, "沒有權限刪除此車輛。")
		return redirect("user_garage")

	if request.method == "POST":
		vehicle_name = str(user_vehicle.vehicle)
		user_vehicle.delete()
		messages.success(request, f"已從車庫中移除 {vehicle_name}。")
		return redirect("user_garage")

	return redirect("user_garage")


def _api_collection_add(
	request: HttpRequest,
	vehicle_id: int,
	model_class,
	collection_name: str,
	state_key: str,
	id_key: str,
) -> JsonResponse:
	"""
	通用的「加入收藏」API 處理函式。
	減少 garage/favorite add 的重複程式碼。
	"""
	vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
	existing = model_class.objects.filter(user=request.user, vehicle=vehicle).first()
	if existing:
		return JsonResponse(
			{
				"success": False,
				"message": f"{vehicle} 已在你的{collection_name}中。",
				state_key: True,
				id_key: existing.id,
			},
			status=200,
		)

	item = model_class.objects.create(user=request.user, vehicle=vehicle)
	return JsonResponse(
		{
			"success": True,
			"message": f"已將 {vehicle} 加入{collection_name}！",
			state_key: True,
			id_key: item.id,
		},
		status=201,
	)


def _api_collection_remove(
	request: HttpRequest,
	vehicle_id: int,
	model_class,
	collection_name: str,
	state_key: str,
	not_found_msg: str,
) -> JsonResponse:
	"""
	通用的「移除收藏」API 處理函式。
	減少 garage/favorite remove 的重複程式碼。
	"""
	vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
	item = model_class.objects.filter(user=request.user, vehicle=vehicle).first()
	if not item:
		return JsonResponse(
			{
				"success": False,
				"message": not_found_msg,
				state_key: False,
			},
			status=404,
		)

	item.delete()
	return JsonResponse(
		{
			"success": True,
			"message": f"已將 {vehicle} 從{collection_name}移除。",
			state_key: False,
		},
		status=200,
	)


@login_required
@require_POST
@ratelimit(key='user', rate='30/m', method='POST', block=True)
def api_garage_add(request: HttpRequest, vehicle_id: int) -> JsonResponse:
	"""
	Week 10/11 範例：將車輛加入「我的車庫」。
	- Method: POST
	- URL: /api/garage/add/<vehicle_id>/
	- Response: {"success": bool, "message": str, "in_garage": bool, "user_vehicle_id": int}
	"""
	return _api_collection_add(
		request, vehicle_id, UserVehicle,
		collection_name="車庫",
		state_key="in_garage",
		id_key="user_vehicle_id",
	)


@login_required
@require_POST
@ratelimit(key='user', rate='30/m', method='POST', block=True)
def api_garage_remove(request: HttpRequest, vehicle_id: int) -> JsonResponse:
	"""
	Week 10/11 範例：自車庫移除車輛。
	- Method: POST
	- URL: /api/garage/remove/<vehicle_id>/
	- Response: {"success": bool, "message": str, "in_garage": bool}
	"""
	return _api_collection_remove(
		request, vehicle_id, UserVehicle,
		collection_name="車庫",
		state_key="in_garage",
		not_found_msg="這台車尚未收藏於車庫。",
	)


@login_required
@require_POST
@ratelimit(key='user', rate='30/m', method='POST', block=True)
def api_favorite_add(request: HttpRequest, vehicle_id: int) -> JsonResponse:
	"""
	Week 11 AJAX 範例：加入「我的最愛」（車款清單）。
	- Method: POST
	- URL: /api/favorites/add/<vehicle_id>/
	- Response: {"success": bool, "favorite": bool, "favorite_id": int}
	"""
	return _api_collection_add(
		request, vehicle_id, FavoriteVehicle,
		collection_name="最愛清單",
		state_key="favorite",
		id_key="favorite_id",
	)


@login_required
@require_POST
@ratelimit(key='user', rate='30/m', method='POST', block=True)
def api_favorite_remove(request: HttpRequest, vehicle_id: int) -> JsonResponse:
	"""
	Week 11 AJAX 範例：從我的最愛清單移除車輛。
	- Method: POST
	- URL: /api/favorites/remove/<vehicle_id>/
	"""
	return _api_collection_remove(
		request, vehicle_id, FavoriteVehicle,
		collection_name="最愛清單",
		state_key="favorite",
		not_found_msg="這台車尚未加入我的最愛。",
	)


@login_required
def user_favorites(request: HttpRequest) -> HttpResponse:
	favorites = (
		request.user.favorite_vehicles.select_related("vehicle")
		.prefetch_related("vehicle__images")
		.order_by("-created_at")
	)
	return render(
		request,
		"motry/favorites.html",
		{
			"favorites": favorites,
		},
	)


class VehicleListAPIView(View):
	"""
	Read-only JSON API（Week 11 範例）：回傳車輛清單並使用 Redis 快取 60 秒。
	Response:
	{
		"success": true,
		"data": {"vehicles": [{id, brand, model, displacement_cc, horsepower_ps, cylinders}]}
	}
	"""

	def get(self, _request: HttpRequest) -> JsonResponse:
		cached = cache.get(VEHICLE_LIST_CACHE_KEY)
		if cached is not None:
			return JsonResponse(cached, status=200)

		vehicles = list(
			Vehicle.objects.order_by("brand", "model").values(
				"id",
				"brand",
				"model",
				"displacement_cc",
				"horsepower_ps",
				"cylinders",
			)
		)
		response_data = {
			"success": True,
			"data": {
				"vehicles": vehicles,
			},
		}
		cache.set(VEHICLE_LIST_CACHE_KEY, response_data, VEHICLE_LIST_CACHE_TIMEOUT)
		return JsonResponse(response_data, status=200)


def _prepare_user_vehicle_field(form: PostCreateForm, user_vehicles: list[UserVehicle]) -> None:
	choices = [("", "選擇我的車（可選）")] + [
		(uv.id, f"{uv.alias or (uv.vehicle.brand + ' ' + uv.vehicle.model)}") for uv in user_vehicles
	]
	widget = forms.Select(attrs={"class": "form-select"})
	widget.choices = choices
	form.fields["user_vehicle_id"].widget = widget
	form.fields["user_vehicle_id"].choices = choices
	form.fields["user_vehicle_id"].required = False


def _safe_redirect(request: HttpRequest, target: str | None, fallback: str) -> str:
	if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
		return target
	return fallback

# AJAX 端點
@login_required
@require_POST
@ratelimit(key='user', rate='30/m', method='POST', block=True)
def rate_vehicle_ajax(request: HttpRequest, id: int) -> JsonResponse:
	"""AJAX 版本的車輛評分"""
	vehicle = get_object_or_404(Vehicle, pk=id)
	
	if request.method != "POST":
		return JsonResponse({"success": False, "error": "Invalid method"}, status=405)
	
	form = RatingForm(request.POST)
	if not form.is_valid():
		errors = form.errors.get("score", ["評分無效"])
		return JsonResponse({"success": False, "error": str(errors[0])}, status=400)
	
	score = int(form.cleaned_data["score"])
	_, created = Rating.objects.update_or_create(
		vehicle=vehicle,
		user=request.user,
		defaults={"score": score},
	)
	
	# 重新計算平均評分
	stats = vehicle.ratings.aggregate(avg=Avg("score"), count=Count("id"))
	
	return JsonResponse({
		"success": True,
		"created": created,
		"score": score,
		"avg_rating": round(stats["avg"] or 0, 1),
		"rating_count": stats["count"] or 0,
		"message": "評分已更新!" if not created else "感謝你的評分!"
	})


@login_required
@require_POST
@ratelimit(key='user', rate='60/m', method='POST', block=True)
def comment_create_ajax(request: HttpRequest) -> JsonResponse:
	"""AJAX 版本的留言創建"""
	form = CommentCreateForm(request.POST, request.FILES)
	if not form.is_valid():
		return JsonResponse({"success": False, "error": "留言失敗,請檢查輸入"}, status=400)
	
	comment: Comment = form.save(commit=False)
	comment.user = request.user
	
	# 檢查父留言的深度限制
	if comment.parent_id:
		parent = Comment.objects.get(pk=comment.parent_id)
		if not parent.can_reply():
			return JsonResponse({"success": False, "error": "已達最大回覆深度(3層)"}, status=400)
	
	# 如果上傳了圖片檔案，優先使用檔案
	if form.cleaned_data.get("image"):
		comment.image = form.cleaned_data["image"]
		comment.image_url = ""
	comment.save()
	
	# 返回渲染後的留言 HTML
	from django.template.loader import render_to_string
	comment_html = render_to_string('motry/partials/comment_item.html', {
		'comment': comment,
		'user': request.user,
	})
	
	return JsonResponse({
		"success": True,
		"comment_id": comment.id,
		"comment_html": comment_html,
		"parent_id": comment.parent_id,
		"message": "留言已送出!"
	})


# ==========================================
# Celery 背景任務相關端點
# ==========================================

@staff_member_required
@require_POST
def export_vehicles_csv(request: HttpRequest) -> JsonResponse:
	"""
	觸發 Celery 背景任務：匯出車輛資料為 CSV。
	- Method: POST
	- URL: /api/export/vehicles/
	- 僅限管理員使用
	- Response: {"success": bool, "task_id": str, "message": str}
	"""
	from .tasks import export_vehicles_to_csv

	task = export_vehicles_to_csv.delay(user_id=request.user.id)
	return JsonResponse({
		"success": True,
		"task_id": task.id,
		"message": "匯出任務已排入背景處理，請稍後查詢結果。",
	})


@staff_member_required
def export_task_status(request: HttpRequest, task_id: str) -> JsonResponse:  # noqa: ARG001
	"""
	查詢 Celery 任務狀態。
	- Method: GET
	- URL: /api/export/status/<task_id>/
	- Response: {"task_id": str, "status": str, "result": str|null}
	"""
	result = AsyncResult(task_id)
	response_data = {
		"task_id": task_id,
		"status": result.status,
		"result": None,
	}

	if result.successful():
		file_path = result.result
		# 轉換為相對於 MEDIA_URL 的路徑
		from django.conf import settings
		import os
		if file_path and file_path.startswith(str(settings.MEDIA_ROOT)):
			relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
			response_data["result"] = f"{settings.MEDIA_URL}{relative_path}"
		else:
			response_data["result"] = file_path
	elif result.failed():
		response_data["result"] = str(result.result)

	return JsonResponse(response_data)
