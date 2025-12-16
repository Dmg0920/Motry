# Motry

以 Django MTV 與 SQLite 實作的車款搜尋與心得分享應用，涵蓋課程第 1～12 週的核心內容（Git、環境、MTV、CRUD、Auth、AJAX、Redis、WebSocket）。已加入 Week 13 的 Celery 背景任務示範（匯出車輛 CSV），尚未設定 Beat 排程。

## 環境建置與 Git 流程（Week 1–2）
```bash
# 於專案根目錄（本檔同層）
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# 建立本地環境變數（請依需求調整值）
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```
離開虛擬環境：`deactivate`

Git 建議流程：
```bash
git init
git checkout -b main
git add .
git commit -m "chore: bootstrap Motry"
git remote add origin <YOUR_REPO_URL>
git push -u origin main
```
之後依功能開分支 (`git checkout -b feat/...`)，完成後 merge 回 main。

## 專案啟動
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
- 前台首頁：`/`
- Django Admin：`/admin/`

## 功能摘要與重要路由
- 首頁與搜尋：`/`、`/search?query=&type=&brand=`
- 車款頁：`/vehicle/<id>/`（規格、圖集、心得流、評分）
- 發文 / 留言 / 按讚：`/post/new`、`/comment/new`、`/like/toggle/<post_id>/`
- 我的車庫（擁有/收藏車輛，可寫備註）：`/garage/`
- 我的最愛（快速追蹤喜歡的車款）：`/favorites/`
- Auth：`/auth/register`、`/auth/login`、`/auth/logout`

## 資料庫設計概覽（Week 5–6）
- `User`（自訂欄位：電話、頭像、個人簡介）
- `Vehicle` ⟷ `VehicleImage`：一對多
- `Vehicle` ⟷ `Tag`：多對多（through `PostTag` 連結 `Post`）
- `Vehicle` ⟷ `Post` ⟷ `Comment`：一對多鏈
- `Post` ⟷ `Like`：一對多（unique_together 限制每人一讚）
- `Vehicle` ⟷ `Rating`：一對多（每人一分）
- `User` ⟷ `UserVehicle`：一對多（我的車庫/閱讀清單概念）
- `User` ⟷ `FavoriteVehicle`：一對多（我的最愛清單）

## Auth、我的車庫與我的最愛（Week 10）
- `AUTH_USER_MODEL = accounts.User`（繼承 `AbstractUser`）。
- 登入/註冊/登出路由已配置。
- `UserVehicle` 對應課程的「閱讀清單」實作：收藏車輛、備註、圖片上傳，並在車款頁或 `我的車庫` 頁面管理。
- `FavoriteVehicle` 提供輕量的「我的最愛」清單，僅標記喜歡的車款，車款頁可 AJAX 加入/移除，並在 `/favorites/` 檢視。

## CRUD 與模板（Week 7）
- `apps/motry/views.py` 含搜尋、車款詳情、發文、留言、刪文/刪留言、評分、按讚等流程，搭配 Django messages 呈現操作結果。
- 模板繼承 `core/base.html`，含導航、品牌篩選、訊息區塊；`vehicle_detail.html` 同時提供「我的最愛」與「我的車庫」按鈕。

## 靜態檔與部署（Week 9）
- `STATIC_ROOT = staticfiles`、`MEDIA_ROOT = media`，Whitenoise 已啟用。
- 可自訂 `STATICFILES_DIRS`（預設空 list）。
- 部署前請設定環境變數：`DJANGO_DEBUG=0`、`SECRET_KEY`、`ALLOWED_HOSTS`、`REDIS_URI`。
- 收集靜態檔：`python manage.py collectstatic`

## API 範例（Week 11）
- AJAX 我的車庫：
  - `POST /api/garage/add/<vehicle_id>/` → `{"success": true, "in_garage": true, "user_vehicle_id": ...}`
  - `POST /api/garage/remove/<vehicle_id>/` → `{"success": true, "in_garage": false}`
- AJAX 我的最愛：
  - `POST /api/favorites/add/<vehicle_id>/` → `{"success": true, "favorite": true}`
  - `POST /api/favorites/remove/<vehicle_id>/` → `{"success": true, "favorite": false}`
- Read-only JSON：
  - `GET /api/vehicles/`
  - 範例回應：
    ```json
    {
      "success": true,
      "data": {
        "vehicles": [
          {"id": 1, "type": "car", "brand": "BMW", "model": "M3", "displacement_cc": 2993, "horsepower_ps": 510, "cylinders": 6}
        ]
      }
    }
    ```

## Redis 快取與 Context Processor（Week 12）
- `apps.motry.context_processors.vehicle_brand_map`：品牌清單優先從 Redis 取，用不到 DB。
- `apps/motry/views.VehicleListAPIView`：車輛列表快取 60 秒（`api:vehicle_list`）。
- `CACHES` 使用 `REDIS_URI`，預設 `redis://127.0.0.1:6379/1`。

## Redis Demo（Week 12）
啟動本地 Redis（macOS 例）：`brew install redis && brew services start redis`

執行示範：
```bash
export REDIS_URI=redis://127.0.0.1:6379/0  # 可省略用預設
python redis_basic_demo.py     # String/Hash/List CRUD 範例
python redis_cache_demo.py     # 模擬昂貴計算 + 快取 TTL
```
兩個檔案純 Python，不會 import Django。

## 即時通知 WebSocket（Week 12）
- 套件：`channels`、`channels-redis`，ASGI 由 `config/asgi.py` 路由 HTTP/WebSocket。
- 路由：`ws://<host>/ws/motry/notifications/`
- 事件：新增貼文 (`post_save`) 觸發推播，前端 `static/motry/js/notifications.js` 會顯示右下角提示。

## 資料匯入（既有管理指令）
```bash
# NHTSA：僅抓車型名稱
python manage.py sync_vehicles --makes BMW Toyota

# CarQuery：含年份、排氣量、馬力等規格
python manage.py sync_carquery --makes BMW Toyota --years 2022 2023 --timeout 60 --retries 5
# 每月排程示例（僅抓當年度）
python manage.py sync_carquery --timeout 60 --retries 5
# 取得所有年份（注意耗時）
# python manage.py sync_carquery --makes BMW --all-years
```

## 課程週次對應表
- Week 1–2：`.gitignore`、`requirements.txt`、README 的環境建置與 Git 流程。
- Week 3：Django MTV 架構 → `config/`、`apps/`、`manage.py`。
- Week 5–6：資料庫設計 → README「資料庫設計概覽」、`apps/motry/models/`。
- Week 7：CRUD → 搜尋、車款詳情、貼文/留言/評分/按讚、模板與 messages。
- Week 9：靜態檔與部署 → Whitenoise/`STATIC_ROOT`/`collectstatic` 說明。
- Week 10：Auth & 閱讀清單 → 自訂 User + 我的車庫（UserVehicle）與我的最愛（FavoriteVehicle）。
- Week 11：AJAX & API → 車庫與最愛 API、`VehicleListAPIView`、前端 `sendRequest`/`vehicle_detail.js`。
- Week 12：Redis & WebSocket → 品牌快取、Redis demo 腳本、WebSocket 新貼文通知。
- Week 13：Celery → `apps/motry/tasks.py` 匯出車輛 CSV（基礎任務，未含 Beat 排程）。

## 未來工作
- Celery Beat 排程、更多任務（目前僅匯出 CSV，未啟用排程）。
- 可選：整合 `django-allauth` Google SSO（需設定 OAuth client）。

## License
僅教學與內部使用示例，請依實際專案補充 License。
