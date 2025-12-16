import random

from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.db.models import Count

from apps.motry.forms import BRANDS_BY_TYPE
from apps.motry.models import Tag, Vehicle, UserVehicle

# 快取鍵與時間常數
RECOMMENDED_VEHICLES_CACHE_KEY = "home:recommended_vehicles"
RECOMMENDED_VEHICLES_CACHE_TIMEOUT = 300  # 5 分鐘


def _get_random_vehicles(count: int = 4) -> list[Vehicle]:
    """
    使用更高效的方式獲取隨機車輛。
    先從快取取，避免每次都執行 ORDER BY RANDOM() 全表掃描。
    """
    cached = cache.get(RECOMMENDED_VEHICLES_CACHE_KEY)
    if cached is not None:
        return cached

    # 取得所有車輛 ID，然後隨機選取
    vehicle_ids = list(Vehicle.objects.values_list("id", flat=True))
    if not vehicle_ids:
        return []

    # 隨機選取 ID
    selected_ids = random.sample(vehicle_ids, min(count, len(vehicle_ids)))

    # 用選出的 ID 查詢完整資料
    vehicles = list(
        Vehicle.objects.filter(id__in=selected_ids).prefetch_related("images")
    )

    cache.set(RECOMMENDED_VEHICLES_CACHE_KEY, vehicles, RECOMMENDED_VEHICLES_CACHE_TIMEOUT)
    return vehicles


def home(request: HttpRequest) -> HttpResponse:
    popular_tags = (
        Tag.objects.annotate(post_count=Count("tag_posts"))
        .order_by("-post_count", "name")[:6]
    )

    popular_brands = []
    for type_group in BRANDS_BY_TYPE.values():
        for brand_key, brand_label in type_group:
            if brand_key not in popular_brands:
                popular_brands.append(brand_key)
            if len(popular_brands) >= 6:
                break
        if len(popular_brands) >= 6:
            break

    recommended_vehicles = _get_random_vehicles(4)

    latest_user_vehicles = (
        UserVehicle.objects.select_related("vehicle", "user")
        .prefetch_related("vehicle__images")
        .order_by("-created_at")[:6]
    )

    context = {
        "popular_tags": popular_tags,
        "popular_brands": popular_brands,
        "recommended_vehicles": recommended_vehicles,
        "latest_user_vehicles": latest_user_vehicles,
    }
    return render(request, "core/home.html", context)
