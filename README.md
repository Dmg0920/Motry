# Motry - 機車搜尋與車友分享平台

**Motry** 是一個以機車為主的車款資訊與社群平台，提供規格搜尋、車款詳情、心得分享與個人車庫管理。後端以 Django + Channels 打造，即時通知、快取與背景任務一應俱全，適合做為機車社群產品的實作範例。

## 🧩 功能概覽

- **機車搜尋**：品牌、關鍵字、排氣量、馬力、缸數等條件篩選
- **車款詳情**：規格卡、圖片集、簡介與評分
- **社群互動**：貼文、留言、按讚、評分
- **我的車庫**：收藏愛車、上傳照片、管理備註
- **我的最愛**：追蹤感興趣的車款
- **即時通知**：新貼文/互動即時推播
- **資料匯出**：後台 CSV 匯出（Celery）

## 🛠 技術架構

- **核心框架**：Python, Django
- **即時通訊**：Django Channels (WebSocket)
- **背景任務**：Celery
- **快取/佇列**：Redis
- **資料庫**：SQLite（開發） / PostgreSQL（生產）
- **前端**：HTML/CSS/JS（含 AJAX）
- **靜態檔**：Whitenoise

## 🚀 本地啟動

### 1) 安裝依賴

```bash
git clone <YOUR_REPO_URL>
cd motry
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) 環境變數

```bash
cp .env.example .env
# 至少設定
# SECRET_KEY=...
# API_NINJAS_KEY=...  (同步機車資料用)
```

主要環境變數：
- `SECRET_KEY`
- `DJANGO_DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `REDIS_URI`（可選，啟用快取/Channels）
- `API_NINJAS_KEY`（同步機車資料）

### 3) 建立資料庫與帳號

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- 前台：`http://127.0.0.1:8000/`
- 後台：`http://127.0.0.1:8000/admin/`

## 🗃️ 匯入機車資料（Ninja API）

專案內建 API Ninjas 同步指令：

```bash
# 同步預設品牌（Yamaha/Honda/Kawasaki/Suzuki/Ducati/KTM）
python manage.py sync_motorcycles

# 指定品牌
python manage.py sync_motorcycles --makes Yamaha Honda

# 指定年份/筆數
python manage.py sync_motorcycles --makes Yamaha --year 2023 --limit 30

# 只查看將匯入內容（不寫入）
python manage.py sync_motorcycles --makes Yamaha --dry-run
```

如果你要載入範例資料（含 tags）：

```bash
bash init_data.sh
```

## 📡 主要 API

- `GET /api/vehicles/`：車款清單（含快取）
- `POST /api/garage/add/<id>/`：加入我的車庫
- `POST /api/garage/remove/<id>/`：移除我的車庫
- `POST /api/favorites/add/<id>/`：加入我的最愛
- `POST /api/favorites/remove/<id>/`：移除我的最愛

## 🔧 常用指令

```bash
# 匯出車輛 CSV（後台）
POST /api/export/vehicles/

# 查詢匯出任務狀態
GET /api/export/status/<task_id>/

# 更新車輛圖片（可選）
python manage.py update_vehicle_images --missing-only
```

## ☁️ Zeabur 部署（摘要）

1. 設定環境變數（`DJANGO_SETTINGS_MODULE=config.settings.production`、`SECRET_KEY`、`ALLOWED_HOSTS`、`CSRF_TRUSTED_ORIGINS`、`REDIS_URI`、`API_NINJAS_KEY`）
2. 連接 PostgreSQL / Redis
3. 佈署後執行：

```bash
python manage.py migrate
python manage.py sync_motorcycles --makes Yamaha Honda Kawasaki
```

詳細部署請見 `DEPLOYMENT.md`。

---

本專案為開發示範用途。
