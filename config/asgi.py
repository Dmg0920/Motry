import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from apps.motry import routing as motry_routing

# 允許環境自行設定 DJANGO_SETTINGS_MODULE，預設為開發設定
os.environ.setdefault(
	"DJANGO_SETTINGS_MODULE",
	os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.development"),
)

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
	{
		"http": django_asgi_app,
		"websocket": AuthMiddlewareStack(
			URLRouter(motry_routing.websocket_urlpatterns)
		),
	}
)
