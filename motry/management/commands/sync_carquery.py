import hashlib
import json
import time
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote_plus

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from motry.models import Vehicle, VehicleImage


CARQUERY_ENDPOINT = "https://www.carqueryapi.com/api/0.3/"


class Command(BaseCommand):
	help = "透過 CarQuery API 匯入車輛詳細規格，避免手動輸入產生錯誤。"

	def add_arguments(self, parser):
		parser.add_argument(
			"--makes",
			nargs="+",
			help="指定要同步的品牌，例如：BMW Toyota Honda。未提供時會使用資料庫現有品牌。"
		)
		parser.add_argument(
			"--years",
			nargs="+",
			type=int,
			help="限制同步的年份，可輸入多個年份；未指定時預設同步當年度資料。"
		)
		parser.add_argument(
			"--all-years",
			action="store_true",
			help="同步 CarQuery 可得的所有年份（可能筆數較大，需注意執行時間）。"
		)
		parser.add_argument(
			"--timeout",
			type=int,
			default=30,
			help="CarQuery API 請求逾時秒數（預設 30）。網路較慢時可調高。"
		)
		parser.add_argument(
			"--retries",
			type=int,
			default=3,
			help="CarQuery API 重試次數（預設 3 次）。"
		)
		parser.add_argument(
			"--dry-run",
			action="store_true",
			help="僅列出將匯入的車款，不寫入資料庫。"
		)

	def handle(self, *args, **options):
		makes_option: List[str] = options.get("makes")
		if makes_option:
			makes = makes_option
		else:
			makes = list(
				Vehicle.objects.filter(type__iexact="car")
				.values_list("brand", flat=True)
				.distinct()
				.order_by("brand")
			)
			if not makes:
				raise CommandError("資料庫尚無任何品牌，請使用 --makes 指定至少一個品牌。")

		all_years: bool = options["all_years"]
		if all_years and options.get("years"):
			raise CommandError("不可同時使用 --years 與 --all-years")

		if all_years:
			years: List[int] = []
		else:
			years = options.get("years") or [datetime.utcnow().year]

		dry_run: bool = options["dry_run"]

		timeout: int = options["timeout"]
		retries: int = max(1, options["retries"])

		session = requests.Session()
		session.headers.update({"User-Agent": "Motry sync_carquery"})
		total_created = 0
		total_updated = 0

		for make in makes:
			self.stdout.write(self.style.HTTP_INFO(f"同步 {make} 車輛資料..."))
			try:
				trims = self._fetch_trims(session, make, years, timeout, retries)
			except CommandError as exc:
				self.stderr.write(self.style.ERROR(str(exc)))
				continue

			if dry_run:
				for t in trims[:10]:
					self.stdout.write(f"- {t['model_year']} {t['model_name']} {t['model_trim']}".strip())
				if len(trims) > 10:
					self.stdout.write(f"... 共 {len(trims)} 筆（dry-run）")
				continue

			created, updated = self._upsert_trims(make, trims)
			total_created += created
			total_updated += updated
			self.stdout.write(self.style.SUCCESS(f"{make}: 新增 {created} 筆，更新 {updated} 筆"))

		if not dry_run:
			self.stdout.write(self.style.SUCCESS(f"同步完成：新增 {total_created}、更新 {total_updated}"))

	def _fetch_trims(
		self,
		session: requests.Session,
		make: str,
		years: Iterable[int],
		timeout: int,
		retries: int,
	) -> List[Dict]:
		params = {
			"cmd": "getTrims",
			"make": make,
			"full_results": 1,
			"limit": 10000,
		}
		if years:
			# CarQuery 一次只能查一個年份，因此逐年查詢再合併
			results: List[Dict] = []
			for year in years:
				params["year"] = year
				results.extend(self._request_carquery(session, params, timeout, retries))
			return results
		return self._request_carquery(session, params, timeout, retries)

	def _request_carquery(
		self,
		session: requests.Session,
		params: Dict,
		timeout: int,
		retries: int,
	) -> List[Dict]:
		last_exc: Optional[Exception] = None
		for attempt in range(1, retries + 1):
			try:
				resp = session.get(CARQUERY_ENDPOINT, params=params, timeout=timeout)
				resp.raise_for_status()
				data = self._parse_carquery_payload(resp.text)
				return data.get("Trims", [])
			except (requests.Timeout, requests.ConnectionError) as exc:
				last_exc = exc
				sleep_for = min(5 * attempt, 15)
				self.stderr.write(
					self.style.WARNING(
						f"CarQuery 連線失敗（第 {attempt}/{retries} 次）：{exc}. "
						f"{'即將重試...' if attempt < retries else ''}"
					)
				)
				if attempt < retries:
					time.sleep(sleep_for)
			except requests.RequestException as exc:
				raise CommandError(f"呼叫 CarQuery 失敗：{exc}") from exc

		raise CommandError(
			f"呼叫 CarQuery 失敗：{last_exc}。"
			" 可嘗試調高 --timeout 或 --retries 後再執行。"
		)

	def _parse_carquery_payload(self, payload: str) -> Dict:
		text = payload.strip()
		start = text.find("{")
		end = text.rfind("}")
		if start == -1 or end == -1:
			raise CommandError("CarQuery 回傳格式無法解析")
		json_str = text[start : end + 1]
		return json.loads(json_str)

	@transaction.atomic
	def _upsert_trims(self, make: str, trims: Iterable[Dict]) -> Tuple[int, int]:
		created = 0
		updated = 0

		for trim in trims:
			model_name = (trim.get("model_name") or "").strip()
			if not model_name:
				continue

			trim_name = (trim.get("model_trim") or "").strip()
			label = f"{trim.get('model_year', '').strip()} {model_name} {trim_name}".strip()

			displacement_cc = self._parse_int(trim.get("model_engine_cc"))
			cylinders = self._parse_int(trim.get("model_engine_cyl"))
			horsepower = self._parse_int(trim.get("model_engine_power_ps"))
			msrp = self._parse_int(trim.get("model_msrp"))
			image_url = (trim.get("model_image") or trim.get("model_img") or "").strip()
			
			# 如果沒有圖片或圖片是default，嘗試從多個來源獲取
			if not image_url or "default" in image_url.lower():
				image_url = self._fetch_image_from_multiple_sources(make, model_name, trim.get("model_year"))

			year = self._parse_int(trim.get("model_year"))
			defaults = {
				"type": "car",
				"generation": trim_name,
				"years_from": year,
				"years_to": year,
				"displacement_cc": displacement_cc,
				"cylinders": cylinders,
				"horsepower_ps": horsepower,
				"msrp_new": msrp,
				"intro_md": self._build_intro(make, trim),
			}

			obj, was_created = Vehicle.objects.update_or_create(
				brand=make,
				model=label,
				defaults=defaults,
			)

			if image_url:
				update_fields = []
				if not obj.cover_url:
					obj.cover_url = image_url
					update_fields.append("cover_url")
				if update_fields:
					obj.save(update_fields=update_fields)
				VehicleImage.objects.get_or_create(
					vehicle=obj,
					image_url=image_url,
					defaults={"sort_order": 1},
				)

			if was_created:
				created += 1
			else:
				updated += 1
		return created, updated

	def _fetch_image_from_multiple_sources(self, make: str, model_name: str, year: Optional[str] = None) -> str:
		"""從多個來源嘗試獲取車輛圖片"""
		# 構建多種搜索查詢變體，提高找到圖片的機率
		search_variants = [
			f"{make} {model_name}",
			f"{make} {model_name} car",
			f"{year} {make} {model_name}" if year else None,
			f"{make} {model_name} vehicle",
		]
		
		# 嘗試多個圖片來源（按優先順序）
		sources = [
			self._try_loremflickr,  # LoremFlickr通常比較可靠
			self._try_picsum_photos,  # Picsum Photos作為備選
		]
		
		# 對每個搜索變體嘗試所有來源
		for search_query in filter(None, search_variants):
			for source_func in sources:
				try:
					image_url = source_func(search_query, make, model_name, year)
					if image_url and "default" not in image_url.lower():
						return image_url
				except Exception:
					# 如果某個來源失敗，繼續嘗試下一個
					continue
		
		# 如果所有來源都失敗，使用fallback
		return self._fallback_image(make, model_name)
	
	def _try_loremflickr(self, query: str, make: str, model_name: str, year: Optional[str] = None) -> str:
		"""使用LoremFlickr獲取圖片（基於關鍵字）"""
		# 構建搜索關鍵字
		keywords = [make, model_name]
		if year:
			keywords.append(str(year))
		search_terms = "+".join(filter(None, [quote_plus(k or "") for k in keywords])) or "car"
		
		# 生成確定性的seed，確保同一車輛總是得到相同的圖片
		seed_source = "-".join(filter(None, [make or "", model_name or "", str(year) if year else ""])) or "motry"
		seed = int(hashlib.sha1(seed_source.encode("utf-8")).hexdigest(), 16) % 10000
		
		return f"https://loremflickr.com/800/450/{search_terms}?lock={seed}"
	
	def _try_picsum_photos(self, query: str, make: str, model_name: str, year: Optional[str] = None) -> str:
		"""使用Picsum Photos作為備選（隨機但穩定）"""
		# Picsum Photos提供隨機圖片，但我們可以基於seed獲得穩定圖片
		seed_source = "-".join(filter(None, [make or "", model_name or "", str(year) if year else ""])) or "motry"
		seed = int(hashlib.sha1(seed_source.encode("utf-8")).hexdigest(), 16) % 1000
		return f"https://picsum.photos/seed/{seed}/800/450"
	
	def _fallback_image(self, make: str, model_name: str) -> str:
		"""最終fallback圖片（使用LoremFlickr）"""
		query = "+".join(filter(None, [quote_plus(make or ""), quote_plus(model_name or "")])) or "car"
		seed_source = "-".join(filter(None, [make or "", model_name or ""])) or "motry"
		seed = int(hashlib.sha1(seed_source.encode("utf-8")).hexdigest(), 16) % 10000
		return f"https://loremflickr.com/800/450/{query}?lock={seed}"

	def _parse_int(self, value) -> int:
		try:
			if value in (None, "", "0", "0.0"):
				return None
			return int(float(value))
		except (ValueError, TypeError):
			return None

	def _build_intro(self, make: str, trim: Dict) -> str:
		year = trim.get("model_year")
		model = trim.get("model_name")
		trim_name = trim.get("model_trim") or ""
		engine = trim.get("model_engine_type") or ""
		body = trim.get("model_body") or ""
		category = trim.get("model_category") or ""

		parts = [
			f"{year} {make} {model} {trim_name}".strip(),
			f"車身型式：{body or category}".strip(),
		]
		if engine:
			parts.append(f"引擎：{engine}")
		if trim.get("model_transmission_type"):
			parts.append(f"變速箱：{trim['model_transmission_type']}")

		return " / ".join(p for p in parts if p)
