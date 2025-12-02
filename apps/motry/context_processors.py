import json
from typing import Dict, List

from django.core.cache import cache
from django.utils.safestring import mark_safe

from .cache_keys import BRAND_MAP_CACHE_KEY
from .forms import BRANDS_BY_TYPE
from .models import Vehicle

BRAND_MAP_CACHE_TTL = 600  # 10 分鐘


def _build_brand_map() -> Dict[str, List[str]]:
	car_brands_qs = (
		Vehicle.objects.filter(type__iexact="car")
		.values_list("brand", flat=True)
		.distinct()
		.order_by("brand")
	)
	bike_brands_qs = (
		Vehicle.objects.filter(type__iexact="bike")
		.values_list("brand", flat=True)
		.distinct()
		.order_by("brand")
	)

	brand_map: Dict[str, List[str]] = {
		"car": list(car_brands_qs),
		"bike": list(bike_brands_qs),
	}

	if not brand_map["car"]:
		brand_map["car"] = [label for label, _ in BRANDS_BY_TYPE["car"]]
	if not brand_map["bike"]:
		brand_map["bike"] = [label for label, _ in BRANDS_BY_TYPE["bike"]]

	return brand_map


def vehicle_brand_map(request) -> Dict[str, object]:
	# Week 12 Redis 快取示範：優先從 Redis 取得品牌 map，沒有才查 DB 再寫回快取
	brand_map = cache.get(BRAND_MAP_CACHE_KEY)
	if brand_map is None:
		brand_map = _build_brand_map()
		cache.set(BRAND_MAP_CACHE_KEY, brand_map, BRAND_MAP_CACHE_TTL)

	return {
		"brand_map": brand_map,
		"brand_map_json": mark_safe(json.dumps(brand_map, ensure_ascii=False)),
	}
