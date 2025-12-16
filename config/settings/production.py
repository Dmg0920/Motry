# config/settings/production.py

from .base import *
import os
from dotenv import load_dotenv
import dj_database_url

# 載入 .env 檔案 (如果存在)
load_dotenv()

DEBUG = False

# 從環境變數讀取允許的主機（去除空白並過濾空值）
_allowed_hosts = os.getenv('ALLOWED_HOSTS', '*')
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(',') if h.strip()]

# 資料庫設定
# Zeabur 會自動注入 POSTGRES_CONNECTION_STRING
postgres_connection_string = os.getenv('POSTGRES_CONNECTION_STRING')

if postgres_connection_string:
    # 在 Zeabur 上使用 PostgreSQL
    DATABASES = {
        'default': dj_database_url.parse(
            postgres_connection_string,
            conn_max_age=600  # 連線池:連線最多保持 600 秒
        )
    }
else:
    # 測試環境或本地測試時使用 SQLite (Zeabur 上會自動注入 POSTGRES_CONNECTION_STRING)
    import logging
    logging.warning("生產環境設定使用 SQLite,請確保在 Zeabur 上已設定 PostgreSQL")
    # 從 base.py 繼承 SQLite 設定
    pass

# 生產環境安全設定
SECURE_SSL_REDIRECT = True  # 強制使用 HTTPS
SESSION_COOKIE_SECURE = True  # Cookie 只能透過 HTTPS 傳輸
CSRF_COOKIE_SECURE = True  # CSRF Cookie 只能透過 HTTPS 傳輸

SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
if SECURE_HSTS_SECONDS:
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "1") == "1"
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "1") == "1"

# 信任 Zeabur 的代理伺服器
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 生產環境必須使用 Redis
if not os.getenv("REDIS_URI"):
    import logging
    logging.warning(
        "警告：生產環境未設定 REDIS_URI，將使用本地記憶體快取。"
        "強烈建議設定 Redis 以獲得更好的效能和可靠性。"
    )

# 靜態文件設定 - 確保 Whitenoise 正確配置
# base.py 已經設定了 STATIC_URL, STATIC_ROOT 和 WhiteNoise middleware
# 確保 STATIC_ROOT 存在且可寫入
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Whitenoise 配置 - 壓縮和快取靜態文件
WHITENOISE_COMPRESS_OFFLINE = True
WHITENOISE_MANIFEST_STRICT = False  # 避免找不到檔案時出錯
