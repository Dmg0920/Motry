import json
from typing import Dict, List

from django.utils.safestring import mark_safe

from .forms import BRANDS_BY_TYPE
from .models import Vehicle


def vehicle_brand_map(request) -> Dict[str, object]:
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

	# 後備：若資料庫尚未有任何車款，使用預設品牌清單
	if not brand_map["car"]:
		brand_map["car"] = [label for label, _ in BRANDS_BY_TYPE["car"]]
	if not brand_map["bike"]:
		brand_map["bike"] = [label for label, _ in BRANDS_BY_TYPE["bike"]]

	return {
		"brand_map": brand_map,
		"brand_map_json": mark_safe(json.dumps(brand_map, ensure_ascii=False)),
	}
