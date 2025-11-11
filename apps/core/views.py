from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.db.models import Count

from apps.motry.forms import BRANDS_BY_TYPE
from apps.motry.models import Tag, Vehicle, UserVehicle


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

    recommended_vehicles = list(
        Vehicle.objects.prefetch_related("images").order_by("?")[:4]
    )

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
