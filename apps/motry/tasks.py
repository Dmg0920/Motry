"""
Celery 任務定義（Week 13）

提供背景任務與定時任務：
- export_vehicles_to_csv: 匯出車輛清單 CSV（背景任務）
- cleanup_old_exports: 清理過期匯出檔案（定時任務）
- refresh_brand_cache: 重新整理品牌快取（定時任務）
"""

import csv
import logging
import os
from datetime import timedelta
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .models import Vehicle

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def export_vehicles_to_csv(self, user_id: int | None = None) -> str:
	"""
	匯出車輛列表為 CSV 檔案，交由 Celery Worker 背景執行。

	Args:
		self: Celery task instance（因為 bind=True，可存取 request/id）
		user_id: 可選，發起匯出請求的使用者 ID（暫供記錄）

	Returns:
		str: 產出的檔案絕對路徑
	"""

	export_dir = Path(settings.MEDIA_ROOT) / "exports"
	export_dir.mkdir(parents=True, exist_ok=True)

	timestamp = timezone.localtime(timezone.now()).strftime("%Y%m%d_%H%M%S")
	filename = f"vehicle_report_{timestamp}.csv"
	if user_id:
		filename = f"vehicle_report_u{user_id}_{timestamp}.csv"

	file_path = export_dir / filename

	headers = [
		"ID",
		"Type",
		"Brand",
		"Model",
		"Generation",
		"Years",
		"Displacement_cc",
		"Cylinders",
		"Horsepower_ps",
		"MSRP_new",
	]

	with open(file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(headers)

		for vehicle in Vehicle.objects.order_by("brand", "model").iterator():
			years = f"{vehicle.years_from or ''}"
			if vehicle.years_to:
				years = f"{years}-{vehicle.years_to}" if years else str(vehicle.years_to)

			writer.writerow(
				[
					vehicle.id,
					vehicle.type,
					vehicle.brand,
					vehicle.model,
					vehicle.generation,
					years,
					vehicle.displacement_cc,
					vehicle.cylinders,
					vehicle.horsepower_ps,
					vehicle.msrp_new,
				]
			)

	return os.fspath(file_path)


@shared_task
def cleanup_old_exports(days: int = 7) -> dict:
	"""
	定時任務：清理超過指定天數的匯出檔案。

	Args:
		days: 保留天數，預設 7 天

	Returns:
		dict: 清理結果統計
	"""
	export_dir = Path(settings.MEDIA_ROOT) / "exports"
	if not export_dir.exists():
		return {"deleted": 0, "errors": 0, "message": "匯出目錄不存在"}

	cutoff_time = timezone.now() - timedelta(days=days)
	deleted_count = 0
	error_count = 0

	for file_path in export_dir.glob("*.csv"):
		try:
			# 取得檔案修改時間
			mtime = timezone.datetime.fromtimestamp(
				file_path.stat().st_mtime,
				tz=timezone.get_current_timezone()
			)
			if mtime < cutoff_time:
				file_path.unlink()
				deleted_count += 1
				logger.info(f"已刪除過期匯出檔案: {file_path.name}")
		except Exception as e:
			error_count += 1
			logger.error(f"刪除檔案失敗 {file_path}: {e}")

	return {
		"deleted": deleted_count,
		"errors": error_count,
		"message": f"已清理 {deleted_count} 個過期檔案",
	}


@shared_task
def refresh_brand_cache() -> dict:
	"""
	定時任務：主動重新整理品牌快取。

	用途：確保品牌列表快取在過期前被更新，避免用戶碰到快取未命中的情況。

	Returns:
		dict: 快取更新結果
	"""
	from .cache_keys import BRAND_MAP_CACHE_KEY
	from .context_processors import _build_brand_map, BRAND_MAP_CACHE_TTL

	try:
		brand_map = _build_brand_map()
		cache.set(BRAND_MAP_CACHE_KEY, brand_map, BRAND_MAP_CACHE_TTL)

		car_count = len(brand_map.get("car", []))
		bike_count = len(brand_map.get("bike", []))

		logger.info(f"品牌快取已更新: {car_count} 個汽車品牌, {bike_count} 個機車品牌")

		return {
			"success": True,
			"car_brands": car_count,
			"bike_brands": bike_count,
			"message": "品牌快取已更新",
		}
	except Exception as e:
		logger.error(f"品牌快取更新失敗: {e}")
		return {
			"success": False,
			"message": str(e),
		}
