import os
from django.core.wsgi import get_wsgi_application

# 允許環境自行設定 DJANGO_SETTINGS_MODULE，預設為開發設定
os.environ.setdefault(
	"DJANGO_SETTINGS_MODULE",
	os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.development"),
)

application = get_wsgi_application()
