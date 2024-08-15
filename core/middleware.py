from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections

User = get_user_model()


class TokenAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        close_old_connections()
        try:
            if token := parse_qs(scope["query_string"].decode("UTF8")).get(
                "token", None
            ):
                scope["user"] = await self.get_user(token)
        except:
            scope["user"] = AnonymousUser()
        return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token):
        try:
            return User.objects.get(token=token)
        except User.DoesNotExist:
            return AnonymousUser()
