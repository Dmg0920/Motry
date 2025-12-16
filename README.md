# Motry - 車款搜尋與心得分享平台

**Motry** 是一個基於 Django MTV 架構開發的車輛資訊社群平台。專案整合了車款資料庫搜尋、使用者心得分享、即時互動通知以及個人化車庫管理功能。系統後端採用 Redis 進行資料快取與訊息佇列處理，並結合 WebSocket 實現即時推播，旨在提供高效且具互動性的使用者體驗。

## 🛠 技術架構 (Tech Stack)

  * **核心框架**: Python, Django (MTV Pattern)
  * **資料庫**: SQLite (開發環境), 支援 PostgreSQL/MySQL
  * **非同步與快取**: Redis
  * **即時通訊**: Django Channels (WebSocket)
  * **背景任務**: Celery (非同步任務處理)
  * **前端技術**: HTML5, CSS3, JavaScript (AJAX), Bootstrap (or custom CSS)
  * **部署支援**: Whitenoise (靜態檔管理)

## ✨ 功能特色

### 1\. 車輛資料與搜尋

  * **進階搜尋**: 支援依據關鍵字、車型 (Type)、品牌 (Brand) 進行篩選。
  * **車款詳情**: 完整呈現規格數據、圖集展示。
  * **外部資料整合**: 內建管理指令可同步 **NHTSA** 與 **CarQuery** API 資料。

### 2\. 社群互動

  * **心得分享**: 使用者可針對特定車款發布圖文心得 (Posts)。
  * **互動機制**: 支援留言 (Comments)、按讚 (Likes) 與星級評分 (Ratings)。
  * **即時通知**: 當有新貼文發布時，線上使用者會透過 WebSocket 收到即時推播提示。

### 3\. 個人化車庫 (My Garage) & 最愛

  * **我的車庫**: 模擬真實車庫概念，使用者可加入擁有的車輛，並上傳愛車照片與備註 (UserVehicle)。
  * **我的最愛**: 快速收藏/追蹤感興趣的車款 (FavoriteVehicle)，支援 AJAX 無刷新操作。
  * **會員系統**: 包含註冊、登入、個人資料管理 (自訂頭像、電話、簡介)。

### 4\. 效能優化與 API

  * **Redis 快取**: 針對品牌清單 (Context Processor) 與車輛列表 API 進行快取，減少資料庫查詢負擔。
  * **RESTful API**: 提供車庫操作、最愛切換及車輛資料讀取的 JSON API。
  * **資料匯出**: 整合 Celery 背景任務，支援將車輛資料匯出為 CSV。

-----

## 🚀 快速開始 (Installation)

### 1\. 環境建置

```bash
# 1. Clone 專案並進入目錄
git clone <YOUR_REPO_URL>
cd motry

# 2. 建立虛擬環境
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. 安裝依賴套件
pip install --upgrade pip
pip install -r requirements.txt
```

### 2\. 環境變數設定

複製範例檔並設定 `SECRET_KEY` 與資料庫連線資訊：

```bash
cp .env.example .env

# 產生一組新的 Secret Key
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

### 3\. 啟動服務 (Redis & Django)

本專案依賴 Redis 服務，請確保本地已安裝並啟動 Redis (預設 `localhost:6379`)。

```bash
# 4. 資料庫遷移與建立超級使用者
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# 5. 啟動開發伺服器
python manage.py runserver
```

  * **前台首頁**: `http://127.0.0.1:8000/`
  * **後台管理**: `http://127.0.0.1:8000/admin/`

-----

## 🗄️ 資料庫模型設計

系統主要由以下實體關係構成：

  * **User**: 擴充 AbstractUser，增加電話、頭像等欄位。
  * **Vehicle**: 核心模型，包含品牌、型號、排氣量等規格。
      * 關聯: `VehicleImage` (一對多), `Rating` (一對多), `Post` (一對多)。
  * **Post & Interaction**:
      * `Post`: 包含內文與關聯車款。
      * `Comment`: 貼文留言。
      * `Like`: 按讚機制 (每人每文限一次)。
  * **Personalization**:
      * `UserVehicle`: **我的車庫** (擁有關係，含備註與圖片)。
      * `FavoriteVehicle`: **我的最愛** (收藏清單)。

-----

## 📡 API 與進階功能說明

### 內部 API (AJAX 整合)

前端透過 JavaScript 非同步呼叫以下接口：

  * **我的車庫**: `POST /api/garage/add/<id>/`, `POST /api/garage/remove/<id>/`
  * **我的最愛**: `POST /api/favorites/add/<id>/`, `POST /api/favorites/remove/<id>/`
  * **車輛資料**: `GET /api/vehicles/` (包含 Redis 快取機制)

### WebSocket 即時通知

  * **路由**: `ws://<host>/ws/motry/notifications/`
  * **機制**: 透過 Django Signals 監聽 `Post` save 事件，利用 Channels Group 發送廣播。

### 資料匯入工具 (Management Commands)

專案內建爬蟲指令，用於初始化資料庫：

```bash
# 僅同步車型名稱 (NHTSA)
python manage.py sync_vehicles --makes BMW Toyota

# 同步詳細規格 (CarQuery)
python manage.py sync_carquery --makes BMW --years 2023 --timeout 60
```

### Celery 背景任務

  * 目前實作：車輛資料 CSV 匯出 (`apps.motry.tasks`)。
  * 啟動 Worker (需另開終端機):
    ```bash
    celery -A config worker -l info
    ```

-----

## 📦 部署須知 (Deployment)

若要部署至正式環境，請注意以下設定：

1.  **環境變數**: 確保 `.env` 中 `DJANGO_DEBUG=0`，並設定正確的 `ALLOWED_HOSTS` 與 `REDIS_URI`。
2.  **靜態檔**: 執行 `python manage.py collectstatic` 將檔案收集至 `staticfiles` 目錄 (已整合 Whitenoise)。
3.  **ASGI**: 由於使用了 WebSocket，建議使用 `daphne` 或 `uvicorn` 搭配 `gunicorn` 進行部署，並指派至 `config.asgi:application`。

-----

### License

本專案為開發示範用途。

-----