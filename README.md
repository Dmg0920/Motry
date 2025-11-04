# Motry

以 Django MTV 與 SQLite 實作的車款搜尋與心得分享應用。僅使用 Django Template 與標準 CRUD。

## 環境需求
- Python 3.10+（建議 3.11）
- macOS（已在 Darwin 24 測試）

## 1) 建立虛擬環境與安裝依賴
```bash
# 於專案根目錄（本檔同層）
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# 建立本地環境變數（複製後請依需求調整值）
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

若要離開虛擬環境：
```bash
deactivate
```

## 2) 初始化資料庫與管理帳號
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## 3) 啟動開發伺服器
```bash
python manage.py runserver
```
- 前台首頁：`/`
- Django Admin：`/admin/`

## 4) 功能摘要（MVP）
- 首頁搜尋：`brand/model` 關鍵字 + `type` 篩選
- 車款頁：規格卡、官方圖集、簡介、心得流（最新優先）
- 貼文：文字＋最多 6 張圖片 URL，需選 1–3 標籤
- 留言：單層
- 按讚：每人每貼文一次（再按為取消）

## 4.1) 車輛資料同步
為了避免手動輸入造成錯誤，可以透過管理指令從公開 API 匯入車輛資料：

```bash
# 安裝依賴（需 requests）
pip install -r requirements.txt

# NHTSA：僅抓車型名稱
python manage.py sync_vehicles --makes BMW Toyota

# CarQuery：含年份、排氣量、馬力等規格（建議指定年份避免過多資料）
python manage.py sync_carquery --makes BMW Toyota --years 2022 2023 --timeout 60 --retries 5

# 每月自動更新：
# - 不帶年份時，預設只同步當年度資料，適合排程（例如 cron 於每月 1 號執行一次）
python manage.py sync_carquery --timeout 60 --retries 5

# 若要一次抓取所有年份，可另加 --all-years（請留意耗時與來源限制）
# python manage.py sync_carquery --makes BMW --all-years
```

執行後即會自動填好 `Vehicle` 所需欄位，再搭配論壇/心得功能即可使用。

## 5) 重要路由
- `/` 首頁
- `/search?query=&type=&brand=` 搜尋
- `/vehicle/<id>/` 車款頁（含心得流與留言）
- `/post/new?vehicle=<id>` 發文（需登入）
- `/comment/new` 留言（需登入，從車款頁送出）
- `/like/toggle/<post_id>/` 讚/取消讚（需登入）

## 6) 管理後台
- 已註冊：`Vehicle/VehicleImage/Post/PostImage/Comment/Tag/PostTag/Like/Rating`
- 透過 Admin 建立更多 `Vehicle` 與 `Tag` 後，即可在前台測試貼文、留言、按讚

## 7) 專案結構（關鍵）
- `config/settings/`：拆分設定（`base.py`, `development.py`, `production.py`）
- `apps/core/`：全域頁面元件（`CoreConfig`、`base.html`、首頁視圖與靜態檔）
- `motry/`：主功能應用（`models.py`, `views.py`, `forms.py`, `urls.py`, `admin.py`，含 `static/motry/` 前端資源）
- `templates/`：共用模板（其餘頁面如 `search_results.html`, `vehicle_detail.html`, `post_form.html` 等）
- `manage.py` 啟動指令
- `requirements.txt` 依賴（Django 4.2 LTS）

## 8) 版本控制建議流程（Git）
```bash
# 初始化（若尚未）
git init
# 建立主分支
git checkout -b main
# 忽略檔案已在 .gitignore 定義

git add .
git commit -m "feat: bootstrap Motry Django app"

# 建立功能分支開發
git checkout -b feat/search-page
# ...修改...
git add -A && git commit -m "feat(search): implement vehicle search"
# 合併回 main（或透過 PR）
git checkout main
git merge --no-ff feat/search-page -m "merge: feat/search-page"

git tag -a v0.1.0 -m "MVP ready"
```

## 9) 常見問題
- 模板靜態樣式：範例使用 `sakura.css` CDN，若需離線請自行改為本地檔
- SQLite 資料檔：`db.sqlite3` 已在 `.gitignore` 排除；依需求自行版本化（不建議）

## 10) License
- 僅教學與內部使用示例，請依實際專案補充 License。
# Motry
