import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY must be set in production environment.")

_allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
if _allowed_hosts:
    ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(",") if host.strip()]
else:
    ALLOWED_HOSTS = ["*"]

postgres_connection_string = os.getenv("POSTGRES_CONNECTION_STRING") or os.getenv(
    "DATABASE_URL"
)

if postgres_connection_string:
    DATABASES = {
        "default": dj_database_url.parse(
            postgres_connection_string,
            conn_max_age=int(os.getenv("DB_CONN_MAX_AGE", "600")),
            ssl_require=os.getenv("DB_SSL_REQUIRE", "1") == "1",
        )
    }

SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "1") == "1"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
