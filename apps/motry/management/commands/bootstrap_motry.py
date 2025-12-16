from django.core.management import BaseCommand, call_command
from django.db import OperationalError, ProgrammingError

from apps.motry.models import Vehicle


class Command(BaseCommand):
    help = (
        "一次性初始化 Motry 專案：執行 migrate，"
        "並在資料庫尚無車輛資料時匯入預設車輛清單（fixtures/vehicles.json）。"
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO("執行 migrate ..."))
        call_command("migrate", interactive=False)

        # 檢查 Vehicle 資料表是否存在，且目前是否已有資料
        try:
            has_any_vehicle = Vehicle.objects.exists()
        except (OperationalError, ProgrammingError):
            # 在極端情況（例如 migrate 尚未完全執行成功）時，避免程式中斷
            self.stdout.write(
                self.style.WARNING(
                    "無法檢查 Vehicle 資料表狀態，略過預設車輛匯入步驟。"
                )
            )
            return

        if has_any_vehicle:
            self.stdout.write(
                self.style.SUCCESS(
                    "資料庫中已存在車輛資料，略過 fixtures 匯入。"
                )
            )
            return

        self.stdout.write(
            self.style.HTTP_INFO(
                "資料庫目前沒有任何車輛資料，開始匯入預設清單（fixtures/vehicles.json）..."
            )
        )
        try:
            # 使用專案內建的預設車輛資料
            call_command("loaddata", "apps/motry/fixtures/vehicles.json")
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(
                self.style.ERROR(f"匯入預設車輛資料失敗：{exc}")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                "初始化完成：migrate 已執行，且預設車輛資料已成功匯入。"
            )
        )

