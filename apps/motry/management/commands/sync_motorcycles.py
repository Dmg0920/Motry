"""
透過 API Ninjas Motorcycles API 同步機車資料至本地資料庫。

使用方式：
    python manage.py sync_motorcycles --makes Yamaha Honda Kawasaki
    python manage.py sync_motorcycles --makes Yamaha --year 2023
    python manage.py sync_motorcycles --makes Ducati --limit 50

環境變數：
    API_NINJAS_KEY: API Ninjas 的 API Key（必須）
"""

import os
import re
import time
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.motry.models import Vehicle


API_NINJAS_ENDPOINT = "https://api.api-ninjas.com/v1/motorcycles"

DEFAULT_MAKES = [
    "Yamaha",
    "Honda",
    "Kawasaki",
    "Suzuki",
    "Ducati",
    "KTM",
]


class Command(BaseCommand):
    help = "透過 API Ninjas 同步機車規格至本地資料庫"

    def add_arguments(self, parser):
        parser.add_argument(
            "--makes",
            nargs="+",
            help="指定要同步的機車品牌，例如：Yamaha Honda。未指定時預設抓取常見機車品牌。",
        )
        parser.add_argument(
            "--year",
            type=int,
            default=None,
            help="限制同步的年份（YYYY 格式），例如：2023",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=30,
            help="每個品牌最多匯入幾筆車型（預設 30，API 單次上限）",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="API 請求逾時秒數（預設 30）",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="僅列出將匯入的車款，不寫入資料庫",
        )

    def handle(self, *args, **options):
        api_key = getattr(settings, "API_NINJAS_KEY", None) or os.environ.get("API_NINJAS_KEY")
        if not api_key:
            raise CommandError(
                "請設定 API_NINJAS_KEY 環境變數或在 settings 中加入 API_NINJAS_KEY。\n"
                "可至 https://api-ninjas.com/ 免費註冊取得。"
            )

        makes = options.get("makes") or DEFAULT_MAKES
        year = options.get("year")
        limit = options.get("limit")
        timeout = options.get("timeout")
        dry_run = options.get("dry_run")

        session = requests.Session()
        session.headers.update({
            "X-Api-Key": api_key,
            "User-Agent": "Motry sync_motorcycles/1.0",
        })

        total_created = 0
        total_updated = 0
        total_skipped = 0

        for make in makes:
            make = make.strip()
            if not make:
                continue

            self.stdout.write(self.style.HTTP_INFO(f"同步 {make} 機車資料..."))

            try:
                motorcycles = self._fetch_motorcycles(session, make, year, limit, timeout)
            except CommandError as exc:
                self.stderr.write(self.style.ERROR(str(exc)))
                continue

            if not motorcycles:
                self.stdout.write(self.style.WARNING(f"  {make} 未取得任何資料"))
                continue

            if dry_run:
                for m in motorcycles[:10]:
                    self.stdout.write(f"  - {m.get('year', '')} {m.get('make', '')} {m.get('model', '')}")
                if len(motorcycles) > 10:
                    self.stdout.write(f"  ... 共 {len(motorcycles)} 筆（dry-run）")
                continue

            created, updated, skipped = self._upsert_motorcycles(motorcycles)
            total_created += created
            total_updated += updated
            total_skipped += skipped

            self.stdout.write(
                self.style.SUCCESS(f"  {make}: 新增 {created}、更新 {updated}、略過 {skipped}")
            )

            # 避免 API rate limit
            time.sleep(0.5)

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n同步完成：新增 {total_created}、更新 {total_updated}、略過 {total_skipped}"
                )
            )

    def _fetch_motorcycles(
        self,
        session: requests.Session,
        make: str,
        year: Optional[int],
        limit: int,
        timeout: int,
    ) -> List[Dict]:
        """從 API Ninjas 取得機車資料"""
        params = {"make": make}
        if year:
            params["year"] = str(year)

        try:
            resp = session.get(API_NINJAS_ENDPOINT, params=params, timeout=timeout)
            resp.raise_for_status()
        except requests.Timeout:
            raise CommandError(f"{make}: API 請求逾時，可嘗試調高 --timeout")
        except requests.RequestException as exc:
            raise CommandError(f"{make}: API 請求失敗 - {exc}")

        data = resp.json()

        if isinstance(data, dict) and "error" in data:
            raise CommandError(f"{make}: API 錯誤 - {data['error']}")

        if not isinstance(data, list):
            raise CommandError(f"{make}: API 回傳格式異常")

        return data[:limit]

    @transaction.atomic
    def _upsert_motorcycles(self, motorcycles: Iterable[Dict]) -> Tuple[int, int, int]:
        """將機車資料寫入資料庫"""
        created = 0
        updated = 0
        skipped = 0

        for moto in motorcycles:
            make = (moto.get("make") or "").strip()
            model = (moto.get("model") or "").strip()

            if not make or not model:
                skipped += 1
                continue

            year = self._parse_int(moto.get("year"))
            displacement = self._parse_displacement(moto.get("displacement"))
            power = self._parse_power(moto.get("power"))
            torque = moto.get("torque", "")

            # 構建車型名稱（含年份）
            model_name = f"{year} {model}".strip() if year else model

            defaults = {
                "generation": moto.get("type", ""),
                "years_from": year,
                "years_to": year,
                "displacement_cc": displacement,
                "horsepower_ps": power,
                "intro_md": self._build_intro(moto),
            }

            obj, was_created = Vehicle.objects.update_or_create(
                brand=make,
                model=model_name,
                defaults=defaults,
            )

            if was_created:
                created += 1
            else:
                updated += 1

        return created, updated, skipped

    def _parse_int(self, value) -> Optional[int]:
        """解析整數值"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _parse_displacement(self, value: str) -> Optional[int]:
        """解析排氣量，例如 '998 ccm' -> 998"""
        if not value:
            return None
        match = re.search(r"(\d+(?:\.\d+)?)", str(value))
        if match:
            return int(float(match.group(1)))
        return None

    def _parse_power(self, value: str) -> Optional[int]:
        """解析馬力，例如 '200 HP' -> 200"""
        if not value:
            return None
        match = re.search(r"(\d+(?:\.\d+)?)", str(value))
        if match:
            return int(float(match.group(1)))
        return None

    def _build_intro(self, moto: Dict) -> str:
        """建立車輛簡介"""
        parts = []

        if moto.get("type"):
            parts.append(f"類型：{moto['type']}")
        if moto.get("engine"):
            parts.append(f"引擎：{moto['engine']}")
        if moto.get("displacement"):
            parts.append(f"排氣量：{moto['displacement']}")
        if moto.get("power"):
            parts.append(f"馬力：{moto['power']}")
        if moto.get("torque"):
            parts.append(f"扭力：{moto['torque']}")
        if moto.get("compression"):
            parts.append(f"壓縮比：{moto['compression']}")
        if moto.get("fuel_system"):
            parts.append(f"供油：{moto['fuel_system']}")
        if moto.get("cooling"):
            parts.append(f"冷卻：{moto['cooling']}")
        if moto.get("gearbox"):
            parts.append(f"變速箱：{moto['gearbox']}")
        if moto.get("total_weight"):
            parts.append(f"重量：{moto['total_weight']}")
        if moto.get("seat_height"):
            parts.append(f"座高：{moto['seat_height']}")
        if moto.get("fuel_capacity"):
            parts.append(f"油箱：{moto['fuel_capacity']}")

        return " / ".join(parts) if parts else ""
