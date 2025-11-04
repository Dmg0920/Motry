from .base import *

DEBUG = True

if not SECRET_KEY:
    SECRET_KEY = "dev-secret-key-change-in-production"

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
