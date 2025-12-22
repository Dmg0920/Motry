from typing import Iterable, Tuple

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from requests.utils import quote

from apps.motry.models import Vehicle


class Command(BaseCommand):
	help = "同步 NHTSA 機車清單至本地資料庫（以品牌名稱為單位抓取車型）"

	DEFAULT_MAKES = [
		"Yamaha",
		"Honda",
		"Kawasaki",
		"Suzuki",
		"Ducati",
		"KTM",
	]

	def add_arguments(self, parser):
		parser.add_argument(
			"--makes",
			nargs="+",
			help="指定要同步的機車品牌，例如：Honda Yamaha。未指定時預設抓取常見機車品牌。",
		)
		parser.add_argument(
			"--limit",
			type=int,
			default=None,
			help="每個品牌最多匯入幾筆車型（預設全部）。",
		)

	def handle(self, *args, **options):
		makes = options.get("makes") or self.DEFAULT_MAKES
		limit = options.get("limit")

		session = requests.Session()
		total_created = 0
		total_skipped = 0

		for make in makes:
			make = make.strip()
			if not make:
				continue
			self.stdout.write(self.style.HTTP_INFO(f"抓取 {make} 車型..."))
			try:
				results = self._fetch_models(session, make)
			except CommandError as exc:
				self.stderr.write(self.style.ERROR(str(exc)))
				continue

			if limit is not None:
				results = results[:limit]

			created, skipped = self._upsert_models(results, make)
			total_created += created
			total_skipped += skipped
			self.stdout.write(
				self.style.SUCCESS(f"{make}: 新增 {created} 筆，略過 {skipped} 筆（已存在）")
			)

		self.stdout.write(
			self.style.SUCCESS(f"同步完成：新增 {total_created} 筆，略過 {total_skipped} 筆。")
		)

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
	def _upsert_models(self, results: Iterable[dict], make: str) -> Tuple[int, int]:
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
					"generation": "",
					"intro_md": "",
				},
			)
			if was_created:
				created += 1
			else:
				skipped += 1
		return created, skipped
