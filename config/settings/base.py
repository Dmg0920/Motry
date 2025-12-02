import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"

_allowed_hosts = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost")
ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(",") if host.strip()]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "channels",
    "daphne",
]

LOCAL_APPS = [
    "apps.core",
    "apps.motry",
    "apps.accounts",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← 加在這裡 (SecurityMiddleware 之後)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.motry.context_processors.vehicle_brand_map",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "zh-hant"
TIME_ZONE = "Asia/Taipei"
USE_I18N = True
USE_TZ = True

# 靜態檔案設定
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # collectstatic 產出
# 可放自訂前端資源的目錄；預設留空避免找不到路徑時報錯
STATICFILES_DIRS: list[Path] = []

# Whitenoise 設定
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",  # ← 使用 Whitenoise
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

_csrf_origins = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1:8000,http://localhost:8000",
)
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in _csrf_origins.split(",") if origin.strip()
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}

# 自訂使用者模型
AUTH_USER_MODEL = 'accounts.User'

# config/settings/base.py

SITE_ID = 1

# config/settings/base.py

AUTHENTICATION_BACKENDS = [
    # Django 預設的認證後端
    'django.contrib.auth.backends.ModelBackend',

    # allauth 的認證後端 (支援社交登入)
    'allauth.account.auth_backends.AuthenticationBackend',
]

# config/settings/base.py

# allauth 設定
ACCOUNT_LOGIN_METHODS = {"username", "email"}  # 允許使用 username 或 email 登入
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]  # 只要求必填的欄位
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # email 驗證為選填 (可改為 'mandatory' 強制驗證)
LOGIN_REDIRECT_URL = '/'  # 登入後導向首頁
LOGOUT_REDIRECT_URL = '/'  # 登出後導向首頁

# 社交登入設定
SOCIALACCOUNT_AUTO_SIGNUP = True  # 使用社交登入時自動建立帳號
SOCIALACCOUNT_QUERY_EMAIL = True  # 向社交平台請求 email
SOCIALACCOUNT_LOGIN_ON_GET = True  # 直接重定向到 OAuth 頁面，跳過中間確認頁面
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True  # 允許使用 email 進行社交帳號認證
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True  # 自動連結相同 email 的既有帳號

# Google OAuth 設定：指定要取得的資訊範圍
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',  # 取得個人資料（名字、頭像等）
            'email',    # 取得 email
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',  # 不需要 refresh token
        },
        'FETCH_USERINFO': True,  # 從 Google 取得用戶資訊
    }
}

AUTH_USER_MODEL = 'accounts.User'

# ==========================================
# Cache 設定 - 使用 Redis
# ==========================================
REDIS_URI = os.getenv("REDIS_URI", "redis://127.0.0.1:6379/1")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URI,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "TIMEOUT": 300,  # 預設快取時間 5 分鐘（單位：秒）
    }
}

# Channels WebSocket 設定（Week12 即時通知）
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URI],
        },
    }
}

# ==========================================
# Celery 設定 - 使用 Redis 作為 Broker
# ==========================================
# Broker：任務佇列存放的地方（使用 Redis）
CELERY_BROKER_URL = REDIS_URI

# Result Backend：任務結果存放的地方（可選，這裡也用 Redis）
CELERY_RESULT_BACKEND = REDIS_URI

# 時區設定（與 Django 一致）
CELERY_TIMEZONE = TIME_ZONE

# 接受的內容類型
CELERY_ACCEPT_CONTENT = ['json']

# 任務序列化格式
CELERY_TASK_SERIALIZER = 'json'

# 結果序列化格式
CELERY_RESULT_SERIALIZER = 'json'

# 啟動時重試連線（消除 Celery 6.0 棄用警告）
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
