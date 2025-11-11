import hashlib
from urllib.parse import quote_plus

from django import template

register = template.Library()


@register.simple_tag
def vehicle_fallback_image(brand: str = "", model: str = "") -> str:
	query_parts = [part for part in [brand or "", model or ""] if part]
	keyword = "+".join(quote_plus(part) for part in query_parts) or "car"
	seed_source = "-".join(part.lower() for part in query_parts) or "motry"
	seed = int(hashlib.sha1(seed_source.encode("utf-8")).hexdigest(), 16) % 10000
	return f"https://loremflickr.com/800/450/{keyword}?lock={seed}"


@register.filter
def is_default_image(url: str) -> bool:
	"""檢查圖片URL是否為default圖片（包含'default'關鍵字）"""
	if not url:
		return True
	return "default" in url.lower()
