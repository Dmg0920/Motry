import hashlib
from typing import Optional
from urllib.parse import quote_plus

from django.core.management.base import BaseCommand
from django.db import transaction
from motry.models import Vehicle, VehicleImage


class Command(BaseCommand):
	help = "為現有車輛重新抓取圖片（從多個來源）"

	def add_arguments(self, parser):
		parser.add_argument(
			"--makes",
			nargs="+",
			help="指定要更新的品牌，例如：BMW Toyota Honda。未提供時會更新所有品牌。"
		)
		parser.add_argument(
			"--missing-only",
			action="store_true",
			help="僅更新沒有圖片或圖片為default的車輛"
		)
		parser.add_argument(
			"--dry-run",
			action="store_true",
			help="僅列出將更新的車輛，不實際更新"
		)

	def handle(self, *args, **options):
		makes_option = options.get("makes")
		missing_only = options["missing_only"]
		dry_run = options["dry_run"]

		# 構建查詢
		vehicles_query = Vehicle.objects.all()
		if makes_option:
			vehicles_query = vehicles_query.filter(brand__in=makes_option)
		
		vehicles = vehicles_query.prefetch_related("images").order_by("brand", "model")
		total = vehicles.count()
		
		if total == 0:
			self.stdout.write(self.style.WARNING("沒有找到符合條件的車輛"))
			return

		self.stdout.write(f"找到 {total} 台車輛")
		if dry_run:
			self.stdout.write(self.style.WARNING("這是 dry-run 模式，不會實際更新"))

		updated_count = 0
		skipped_count = 0

		for vehicle in vehicles:
			# 檢查是否需要更新
			if missing_only:
				has_valid_image = False
				# 檢查是否有有效的圖片
				if vehicle.cover_url and "default" not in vehicle.cover_url.lower():
					has_valid_image = True
				else:
					for img in vehicle.images.all():
						if img.image_url and "default" not in img.image_url.lower():
							has_valid_image = True
							break
				
				if has_valid_image:
					skipped_count += 1
					continue

			# 獲取車輛信息
			make = vehicle.brand
			model_parts = vehicle.model.split()
			# 嘗試提取年份和車型名稱
			year = None
			model_name = vehicle.model
			
			if vehicle.years_from:
				year = str(vehicle.years_from)
			
			# 嘗試從model中提取車型名稱（移除年份）
			if model_parts and model_parts[0].isdigit():
				year = model_parts[0]
				model_name = " ".join(model_parts[1:])
			
			# 獲取新圖片
			new_image_url = self._fetch_image_from_multiple_sources(
				make, model_name, year
			)

			if dry_run:
				self.stdout.write(f"  - {vehicle.brand} {vehicle.model}: {new_image_url}")
			else:
				with transaction.atomic():
					# 更新封面圖
					if not vehicle.cover_url or "default" in vehicle.cover_url.lower():
						vehicle.cover_url = new_image_url
						vehicle.save(update_fields=["cover_url"])
					
					# 更新或創建官方圖集的第一張圖片
					first_image, created = VehicleImage.objects.get_or_create(
						vehicle=vehicle,
						sort_order=1,
						defaults={"image_url": new_image_url}
					)
					if not created and ("default" in first_image.image_url.lower() or not first_image.image_url):
						first_image.image_url = new_image_url
						first_image.save(update_fields=["image_url"])

				updated_count += 1
				if updated_count % 10 == 0:
					self.stdout.write(f"已更新 {updated_count} 台車輛...")

		if not dry_run:
			self.stdout.write(
				self.style.SUCCESS(
					f"完成！更新了 {updated_count} 台車輛的圖片"
					f"{f'，跳過了 {skipped_count} 台已有有效圖片的車輛' if missing_only else ''}"
				)
			)
		else:
			self.stdout.write(
				self.style.SUCCESS(
					f"將更新 {updated_count} 台車輛"
					f"{f'，將跳過 {skipped_count} 台已有有效圖片的車輛' if missing_only else ''}"
				)
			)

	def _fetch_image_from_multiple_sources(self, make: str, model_name: str, year: Optional[str] = None) -> str:
		"""從多個來源嘗試獲取車輛圖片（與sync_carquery共用邏輯）"""
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

