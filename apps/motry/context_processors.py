import json
from typing import Dict, List

from django.core.cache import cache
from django.utils.safestring import mark_safe

from .cache_keys import BRAND_MAP_CACHE_KEY
from .forms import BRAND_CHOICES
from .models import Vehicle

BRAND_MAP_CACHE_TTL = 600  # 10 分鐘


def _build_brand_list() -> List[str]:
	"""取得所有機車品牌列表"""
	brands_qs = (
		Vehicle.objects.values_list("brand", flat=True)
		.distinct()
		.order_by("brand")
	)
	brands = list(brands_qs)
	if not brands:
		brands = [label for label, _ in BRAND_CHOICES]
	return brands


def vehicle_brand_map(request) -> Dict[str, object]:
	# Week 12 Redis 快取示範：優先從 Redis 取得品牌列表，沒有才查 DB 再寫回快取
	brands = cache.get(BRAND_MAP_CACHE_KEY)
	if brands is None:
		brands = _build_brand_list()
		cache.set(BRAND_MAP_CACHE_KEY, brands, BRAND_MAP_CACHE_TTL)

	return {
		"brand_list": brands,
		"brand_list_json": mark_safe(json.dumps(brands, ensure_ascii=False)),
	}
