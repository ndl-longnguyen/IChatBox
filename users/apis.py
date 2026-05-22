import uuid

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from chat.models import ChatMessage, ChatRoom, CustomerKey
from users.models import Participant


class WidgetCorsMixin:
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "*"
        return response


class WidgetConfigResponseSerializer(serializers.Serializer):
    allow_anonymous = serializers.BooleanField()
    plan = serializers.CharField()
    history_limit = serializers.IntegerField()
    show_social_links = serializers.BooleanField()
    social_facebook = serializers.CharField(allow_null=True)
    social_zalo = serializers.CharField(allow_null=True)
    social_phone = serializers.CharField(allow_null=True)
    widget_position = serializers.CharField()


class WidgetIPThrottle(SimpleRateThrottle):
    scope = "widget_ip"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"widget_ip:{ident}"


class WidgetTokenThrottle(SimpleRateThrottle):
    scope = "widget_token"

    def get_cache_key(self, request, view):
        token = (request.query_params.get("token") or "").strip()
        if not token:
            return None
        return f"widget_token:{token}"


def get_active_customer_key_or_none(token):
    # Fail fast: require a valid UUID format.
    try:
        token_uuid = uuid.UUID(str(token))
    except (ValueError, AttributeError, TypeError):
        return None

    try:
        key = CustomerKey.objects.get(key=token_uuid)
    except CustomerKey.DoesNotExist:
        return None

    if not getattr(key, "is_active", True):
        return None

    return key


class WidgetConfigAPIView(WidgetCorsMixin, APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [WidgetIPThrottle, WidgetTokenThrottle]

    def get(self, request):
        token = (request.query_params.get("token") or "").strip()
        if not token:
            return Response({"error": "Token is required"}, status=400)

        key = get_active_customer_key_or_none(token)
        if not key:
            # Generic 404 to avoid leaking key existence/inactive status.
            return Response({"error": "Invalid token"}, status=404)

        payload = {
            "allow_anonymous": key.allow_anonymous,
            "plan": key.plan,
            "history_limit": key.history_limit,
            "show_social_links": getattr(key, "show_social_links", False),
            "social_facebook": getattr(key, "social_facebook", None),
            "social_zalo": getattr(key, "social_zalo", None),
            "social_phone": getattr(key, "social_phone", None),
            "widget_position": (
                getattr(key, "widget_position", None) or "bottom-right"
            ),
        }
        return Response(WidgetConfigResponseSerializer(payload).data)


class ChatMessageWidgetSerializer(serializers.ModelSerializer):
    message = serializers.CharField(source="content")

    class Meta:
        model = ChatMessage
        fields = ["id", "sender_type", "message", "created_at"]


class WidgetHistoryAPIView(WidgetCorsMixin, APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [WidgetIPThrottle, WidgetTokenThrottle]

    def get(self, request):
        token = (request.query_params.get("token") or "").strip()
        device = (request.query_params.get("device") or "").strip()
        before_message_id = (request.query_params.get("before") or "").strip()
        if not token or not device:
            return Response(
                {"error": "token and device are required"}, status=400
            )

        key = get_active_customer_key_or_none(token)
        if not key:
            return Response({"error": "Invalid token"}, status=404)

        participant = Participant.objects.filter(
            user=key.user, device=device
        ).first()
        if not participant:
            return Response({"messages": [], "participant": None})

        room = ChatRoom.objects.filter(
            user=key.user, participant=participant
        ).first()
        if not room:
            return Response(
                {"messages": [], "participant": {"name": participant.name}}
            )

        try:
            requested_limit = int(request.query_params.get("limit") or 50)
        except ValueError:
            requested_limit = 50
        requested_limit = max(1, min(requested_limit, 200))

        # Enforce plan limit (server-side source of truth)
        effective_limit = min(
            requested_limit, int(key.history_limit or 0) or 50
        )

        qs = ChatMessage.objects.filter(chat_room=room)
        if before_message_id:
            try:
                before_message = ChatMessage.objects.get(
                    id=before_message_id, chat_room=room
                )
                qs = qs.filter(
                    created_at__lt=before_message.created_at
                ) | qs.filter(
                    created_at=before_message.created_at,
                    id__lt=before_message.id,
                )
            except (ChatMessage.DoesNotExist, ValueError):
                return Response({"error": "Invalid cursor"}, status=400)

        qs = qs.order_by("-created_at", "-id")

        # Grab one extra to know if there are more messages
        rows = list(qs[: effective_limit + 1])
        has_more = len(rows) > effective_limit
        rows = rows[:effective_limit]

        data = ChatMessageWidgetSerializer(rows, many=True).data
        data = list(reversed(data))  # chronological order for UI rendering

        next_cursor = rows[-1].id if rows else None

        return Response(
            {
                "participant": {
                    "name": participant.name,
                    "email": participant.email,
                    "phone": participant.phone,
                    "device": participant.device,
                },
                "messages": data,
                "has_more": has_more,
                "next_cursor": str(next_cursor) if next_cursor else None,
            }
        )
