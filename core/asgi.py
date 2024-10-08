import os
from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path
from chat.consumers import ChatForUserConsumer, ChatForAdminConsumer
from core.middleware import TokenAuthMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
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
