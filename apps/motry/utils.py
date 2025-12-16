from __future__ import annotations


def is_placeholder_image(url: str) -> bool:
	"""Centralized helper to detect seed/default/empty images."""
	if not url:
		return True
	lower = url.lower()
	if "loremflickr.com" in lower or "picsum.photos" in lower:
		return True
	return "default" in lower
