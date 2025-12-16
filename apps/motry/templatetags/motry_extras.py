import base64
import hashlib
import random
from django import template

from apps.motry.utils import is_placeholder_image

register = template.Library()


def _placeholder_svg(brand: str = "", model: str = "") -> str:
	text = f"{brand} {model}".strip() or "此車款尚無圖片"
	svg = f"""<svg width='800' height='450' xmlns='http://www.w3.org/2000/svg'>
<rect width='800' height='450' fill='#0f172a'/>
<text x='50%' y='45%' dominant-baseline='middle' text-anchor='middle' fill='#e5e7eb' font-family='-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif' font-size='26' font-weight='600'>目前該車輛沒有圖片</text>
<text x='50%' y='60%' dominant-baseline='middle' text-anchor='middle' fill='#94a3b8' font-family='-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif' font-size='18'>{text}</text>
</svg>"""
	data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
	return f"data:image/svg+xml;base64,{data}"


@register.simple_tag
def vehicle_fallback_image(brand: str = "", model: str = "") -> str:
	"""顯示文字占位圖：提示『目前該車輛沒有圖片』。"""
	return _placeholder_svg(brand, model)


@register.filter
def is_default_image(url: str) -> bool:
	"""檢查圖片URL是否為default圖片（包含'default'關鍵字）"""
	return is_placeholder_image(url)


@register.simple_tag
def vehicle_showcase_image(vehicle) -> str:
	"""隨機挑一張車輛美照展示，若無則回傳空字串。"""
	if not vehicle:
		return ""

	cached = getattr(vehicle, "_showcase_image", None)
	if cached is not None:
		return cached

	urls = []
	if hasattr(vehicle, "get_gallery_images"):
		urls = [img.image_url_or_file for img in vehicle.get_gallery_images()]
	elif hasattr(vehicle, "images"):
		urls = []
		for img in vehicle.images.all():
			if getattr(img, "has_real_image", False):
				urls.append(img.image_url_or_file)

	if urls:
		selected = random.choice(urls)
		setattr(vehicle, "_showcase_image", selected)
		return selected

	cover = getattr(vehicle, "cover_url", "")
	if cover and not is_placeholder_image(cover):
		setattr(vehicle, "_showcase_image", cover)
		return cover

	setattr(vehicle, "_showcase_image", "")
	return ""
