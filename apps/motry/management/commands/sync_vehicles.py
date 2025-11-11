from typing import Iterable, Tuple

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from requests.utils import quote

from apps.motry.models import Vehicle


class Command(BaseCommand):
	help = "同步 NHTSA 車輛清單至本地資料庫（以品牌名稱為單位抓取車型）"

	DEFAULT_MAKES = [
		"BMW",
		"Toyota",
		"Mercedes-Benz",
		"Audi",
		"Porsche",
		"Ford",
		"Tesla",
		"Honda",
		"Nissan",
		"Hyundai",
		"Kia",
	]

	def add_arguments(self, parser):
		parser.add_argument(
			"--makes",
			nargs="+",
			help=(
				"指定要同步的品牌，可使用 '品牌:類型' 指定車種（car 或 bike），"
				"例如：'Honda:bike'。未指定時預設抓取常見汽車品牌。"
			),
		)
		parser.add_argument(
			"--limit",
			type=int,
			default=None,
			help="每個品牌最多匯入幾筆車型（預設全部）。",
		)

	def handle(self, *args, **options):
		makes_option = options.get("makes") or self.DEFAULT_MAKES
		limit = options.get("limit")

		makes = []
		for raw in makes_option:
			make, vehicle_type = self._parse_make_option(raw)
			makes.append((make, vehicle_type))

		session = requests.Session()
		total_created = 0
		total_skipped = 0

		for make, vehicle_type in makes:
			self.stdout.write(self.style.HTTP_INFO(f"抓取 {make} ({vehicle_type}) 車型..."))
			try:
				results = self._fetch_models(session, make)
			except CommandError as exc:
				self.stderr.write(self.style.ERROR(str(exc)))
				continue

			if limit is not None:
				results = results[:limit]

			created, skipped = self._upsert_models(results, make, vehicle_type)
			total_created += created
			total_skipped += skipped
			self.stdout.write(
				self.style.SUCCESS(f"{make}: 新增 {created} 筆，略過 {skipped} 筆（已存在）")
			)

		self.stdout.write(
			self.style.SUCCESS(f"同步完成：新增 {total_created} 筆，略過 {total_skipped} 筆。")
		)

	def _parse_make_option(self, option: str) -> Tuple[str, str]:
		if ":" in option:
			make, vehicle_type = option.split(":", 1)
			make = make.strip()
			vehicle_type = vehicle_type.strip().lower()
		else:
			make = option.strip()
			vehicle_type = "car"

		if vehicle_type not in {"car", "bike"}:
			raise CommandError(f"不支援的 vehicle type: '{vehicle_type}'（僅支援 car 或 bike）")
		if not make:
			raise CommandError("品牌名稱不可為空白")
		return make, vehicle_type

	def _fetch_models(self, session: requests.Session, make: str) -> Iterable[dict]:
		url = (
			f"https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake/{quote(make)}?format=json"
		)
		try:
			resp = session.get(url, timeout=15)
			resp.raise_for_status()
		except requests.RequestException as exc:
			raise CommandError(f"{make} 取得資料失敗：{exc}") from exc

		data = resp.json()
		results = data.get("Results", [])
		if not results:
			self.stdout.write(
				self.style.WARNING(f"{make} 從 API 未取得任何車型資料。")
			)
		return results

	@transaction.atomic
	def _upsert_models(
		self, results: Iterable[dict], make: str, vehicle_type: str
	) -> Tuple[int, int]:
		created = 0
		skipped = 0
		for item in results:
			model_name = (item.get("Model_Name") or "").strip()
			if not model_name:
				skipped += 1
				continue

			obj, was_created = Vehicle.objects.get_or_create(
				brand=make,
				model=model_name,
				defaults={
					"type": vehicle_type,
					"generation": "",
					"intro_md": "",
				},
			)
			if was_created:
				created += 1
			else:
				skipped += 1
		return created, skipped
