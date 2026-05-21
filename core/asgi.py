import os

# Ensure settings are configured before importing Django/channels modules
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

django_asgi_app = get_asgi_application()

# Import consumers only after Django has finished setup (app registry ready).
from chat.consumers import (
    ChatForUserConsumer,
    ChatForAdminConsumer,
)  # noqa: E402
from core.middleware import TokenAuthMiddleware  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            TokenAuthMiddleware(
                URLRouter(
                    [
                        path("ws/user/chat/", ChatForUserConsumer.as_asgi()),
                        path("ws/admin/chat/", ChatForAdminConsumer.as_asgi()),
                    ]
                )
            )
        ),
    }
)
