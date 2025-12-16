"""
Celery 任務定義（Week 13）

目前提供「匯出車輛清單 CSV」的背景任務示範，之後可再串接 WebSocket 或通知。
"""

import csv
import os
from datetime import datetime
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import Vehicle


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
