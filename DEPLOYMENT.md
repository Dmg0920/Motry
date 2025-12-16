# Zeabur 部署指南

## 已完成的配置

### 1. 靜態文件配置
- ✅ 已安裝 `whitenoise==6.11.0`
- ✅ 已在 [config/settings/base.py](config/settings/base.py:45) 配置 WhiteNoiseMiddleware
- ✅ 已配置 STATIC_ROOT 和 WhiteNoise 壓縮存儲

### 2. Zeabur 配置文件
已創建 [zbpack.json](zbpack.json) 配置:
```json
{
  "build_command": "python manage.py collectstatic --noinput",
  "start_command": "daphne -b 0.0.0.0 -p $PORT config.asgi:application"
}
```

### 3. 生產環境設定
在 [config/settings/production.py](config/settings/production.py) 已配置:
- PostgreSQL 數據庫支持
- Whitenoise 靜態文件服務
- 安全性設定 (HTTPS, Cookie 等)

## 部署步驟

### 1. 在 Zeabur 上配置環境變數

在 Zeabur 專案的環境變數設定中添加:

```bash
# Django 設定
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-domain.zeabur.app,*.zeabur.app
CSRF_TRUSTED_ORIGINS=https://your-domain.zeabur.app

# PostgreSQL (Zeabur 會自動注入,無需手動設定)
# POSTGRES_CONNECTION_STRING=postgresql://...

# Redis (如果使用 Redis 服務)
REDIS_URI=redis://your-redis-host:6379/0
USE_REDIS=1

# Google OAuth (如果使用)
SOCIALACCOUNT_PROVIDERS__GOOGLE__APP__CLIENT_ID=your-google-client-id
SOCIALACCOUNT_PROVIDERS__GOOGLE__APP__SECRET=your-google-client-secret
```

### 2. 連接 PostgreSQL 數據庫

在 Zeabur:
1. 添加 PostgreSQL 服務
2. Zeabur 會自動將 `POSTGRES_CONNECTION_STRING` 注入到環境變數
3. 無需手動配置

### 3. 連接 Redis (可選,但建議)

在 Zeabur:
1. 添加 Redis 服務
2. 複製 Redis 連接 URI
3. 在環境變數設定 `REDIS_URI`

### 4. 部署

1. 將代碼推送到 Git
2. 在 Zeabur 連接你的 Git 倉庫
3. Zeabur 會自動:
   - 安裝依賴 (`requirements.txt`)
   - 運行 `python manage.py collectstatic --noinput`
   - 啟動 Daphne 服務器

### 5. 運行數據庫遷移

部署後,在 Zeabur 控制台運行:
```bash
python manage.py migrate
```

## 檢查清單

- [ ] 已在 Zeabur 設定所有必要的環境變數
- [ ] 已添加 PostgreSQL 服務
- [ ] 已添加 Redis 服務 (建議)
- [ ] 已在 ALLOWED_HOSTS 添加你的域名
- [ ] 已在 CSRF_TRUSTED_ORIGINS 添加你的域名
- [ ] 已運行 `python manage.py migrate`
- [ ] 已創建超級用戶 (如需要): `python manage.py createsuperuser`

## 故障排除

### 靜態文件 404
- ✅ 已配置 Whitenoise - 靜態文件會由 Whitenoise 自動提供
- ✅ 已在 zbpack.json 配置自動運行 collectstatic
- 確保 `staticfiles/` 目錄已被 git ignore (已配置)

### WebSocket 連接問題
- 確保使用 `wss://` (HTTPS WebSocket)
- 檢查 Zeabur 是否支持 WebSocket (預設支持)

### 數據庫連接錯誤
- 確認 Zeabur 已正確注入 `POSTGRES_CONNECTION_STRING`
- 在 Zeabur 控制台檢查環境變數

## 本地測試生產配置

```bash
# 設定環境變數
export DJANGO_SETTINGS_MODULE=config.settings.production
export SECRET_KEY=test-secret-key
export ALLOWED_HOSTS=localhost,127.0.0.1

# 收集靜態文件
python manage.py collectstatic --noinput

# 運行服務器 (使用 daphne)
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

## 相關文件

- [base.py](config/settings/base.py) - 基礎設定
- [production.py](config/settings/production.py) - 生產環境設定
- [zbpack.json](zbpack.json) - Zeabur 部署配置
- [requirements.txt](requirements.txt) - Python 依賴

## 注意事項

1. **靜態文件**: Whitenoise 會在應用啟動時自動提供靜態文件,無需額外配置
2. **數據庫**: 生產環境必須使用 PostgreSQL,不支持 SQLite
3. **HTTPS**: 生產環境強制使用 HTTPS
4. **Redis**: 建議使用 Redis 以獲得更好的性能 (Cache 和 WebSocket)
