import asyncio
import json
import logging
import socket
import urllib.error
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from ai.services import (
    _is_meaningless_message,
    _is_vague_question,
    _query_intents,
    build_general_assistant_reply,
    build_prompt,
    call_ollama_async,
    get_or_create_ai_settings,
    retrieve_relevant_chunks,
    save_ai_reply,
)
from users.models import Participant
from chat.models import ChatMessage, ChatRoom, CustomerKey

User = get_user_model()
logger = logging.getLogger(__name__)


def normalize_visitor_value(value):
    normalized = (value or "").strip()
    return normalized or None


def has_required_visitor_info(allow_anonymous, username, phone, email):
    if allow_anonymous:
        return True

    normalized_username = normalize_visitor_value(username)
    normalized_phone = normalize_visitor_value(phone)
    normalized_email = normalize_visitor_value(email)

    return bool(normalized_username and (normalized_phone or normalized_email))


async def discard_channel_group(
    channel_layer, group_name, channel_name, timeout=2
):
    try:
        await asyncio.wait_for(
            channel_layer.group_discard(group_name, channel_name),
            timeout=timeout,
        )
    except (asyncio.TimeoutError, asyncio.CancelledError):
        logger.debug(
            "Timed out discarding channel %s from %s", channel_name, group_name
        )
    except Exception:
        logger.exception(
            "Failed to discard channel %s from %s", channel_name, group_name
        )


class ChatForUserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = parse_qs(self.scope["query_string"].decode("utf-8"))
        self.license_key_str = query_string.get("token", [None])[
            0
        ]  # Treat token parameter as license key
        self.raw_username = normalize_visitor_value(
            query_string.get("username", [None])[0]
        )
        self.username = self.raw_username or "Guest"
        self.device = (
            normalize_visitor_value(query_string.get("device", [None])[0])
            or self.username
        )
        self.phone = normalize_visitor_value(
            query_string.get("phone", [None])[0]
        )
        self.email = normalize_visitor_value(
            query_string.get("email", [None])[0]
        )

        if not self.license_key_str:
            await self.close()
            return

        # Fetch CustomerKey and associated admin user
        self.customer_key = await self.get_customer_key(self.license_key_str)
        if not self.customer_key:
            await self.close()
            return
        if not getattr(self.customer_key, "is_active", True):
            await self.close(code=4403)
            return

        self.customer_user = await self.get_customer_user(self.customer_key)
        if not self.customer_user:
            await self.close()
            return

        if not has_required_visitor_info(
            self.customer_key.allow_anonymous,
            self.raw_username,
            self.phone,
            self.email,
        ):
            await self.close(code=4403)
            return

        # Get or create the participant and chat room
        self.participant = await self.get_or_create_participant()
        self.chat_room, created = await self.get_or_create_chat_room()

        # Use the chat room's ID for the group name
        self.chat_room_group_name = f"chat_room_{self.chat_room.id}"

        # Add the visitor to the chat room group
        await self.channel_layer.group_add(
            self.chat_room_group_name, self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

        # If a new room was created, notify the admin's global channel group in real-time
        if created:
            admin_group_name = f"admin_{self.customer_user.token}"
            await self.channel_layer.group_send(
                admin_group_name,
                {
                    "type": "new_room",
                    "room_id": str(self.chat_room.id),
                    "participant_name": self.participant.name,
                },
            )

    async def disconnect(self, close_code):
        task = getattr(self, "_ai_task", None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Leave the chat room group if it exists
        if hasattr(self, "chat_room_group_name"):
            await discard_channel_group(
                self.channel_layer,
                self.chat_room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        # Parse the incoming message
        text_data_json = json.loads(text_data)
        message = text_data_json.get("message", "").strip()

        if message:
            await self.create_message(message)

            # Broadcast the message to the chat room group
            await self.channel_layer.group_send(
                self.chat_room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender_type": "PARTICIPANT",
                    "chat_room_id": str(self.chat_room.id),
                },
            )

            # Notify the admin UI in real time without subscribing the admin to every room group
            admin_group_name = f"admin_{self.customer_user.token}"
            await self.channel_layer.group_send(
                admin_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender_type": "PARTICIPANT",
                    "chat_room_id": str(self.chat_room.id),
                },
            )
            # Run AI in the background so we don't block the WS receive loop.
            self._ai_task = asyncio.create_task(
                self.send_ai_auto_reply(message)
            )

    async def chat_message(self, event):
        # Send the message to the WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message": event["message"],
                    "sender_type": event["sender_type"],
                    "chat_room_id": event["chat_room_id"],
                }
            )
        )

    @database_sync_to_async
    def get_customer_key(self, key_str):
        try:
            return CustomerKey.objects.get(key=key_str)
        except (CustomerKey.DoesNotExist, ValueError):
            return None

    @database_sync_to_async
    def get_customer_user(self, customer_key):
        return customer_key.user

    @database_sync_to_async
    def get_or_create_participant(self):
        # Participant belongs to the customer admin user, and is identified by device/visitor ID
        participant, created = Participant.objects.get_or_create(
            user=self.customer_user,
            device=self.device,
            defaults={
                "name": self.username,
                "phone": self.phone,
                "email": self.email,
            },
        )
        if not created:
            updated = False
            if (
                self.username
                and participant.name != self.username
                and self.username != "Guest"
            ):
                participant.name = self.username
                updated = True
            if self.phone and participant.phone != self.phone:
                participant.phone = self.phone
                updated = True
            if self.email and participant.email != self.email:
                participant.email = self.email
                updated = True
            if updated:
                participant.save()
        return participant

    @database_sync_to_async
    def get_or_create_chat_room(self):
        # Get or create a chat room for the user, participant, and key
        chat_room, created = ChatRoom.objects.get_or_create(
            user=self.customer_user,
            participant=self.participant,
            defaults={"customer_key": self.customer_key},
        )
        return chat_room, created

    @database_sync_to_async
    def create_message(self, message):
        # Create a new message from the participant
        return ChatMessage.objects.create(
            chat_room=self.chat_room, sender_type="PARTICIPANT", content=message
        )

    async def send_ai_auto_reply(self, visitor_message):
        try:
            reply = await asyncio.wait_for(
                self._generate_ai_reply(visitor_message),
                timeout=70,
            )
        except asyncio.CancelledError:
            return
        except asyncio.TimeoutError:
            logger.warning(
                "Local AI auto-reply timed out for room %s", self.chat_room.id
            )
            return
        except Exception:
            logger.exception(
                "AI auto-reply failed for room %s", self.chat_room.id
            )
            return

        if not reply:
            return

        await database_sync_to_async(save_ai_reply)(self.chat_room.id, reply)
        ai_event = {
            "type": "chat_message",
            "message": reply,
            "sender_type": "USER",
            "chat_room_id": str(self.chat_room.id),
        }
        await self.channel_layer.group_send(self.chat_room_group_name, ai_event)
        await self.channel_layer.group_send(
            f"admin_{self.customer_user.token}",
            ai_event,
        )

    async def _generate_ai_reply(self, visitor_message):
        ai_settings = await database_sync_to_async(get_or_create_ai_settings)(
            self.customer_user
        )
        if not ai_settings.auto_reply_enabled:
            return None

        language = ai_settings.language or "vi"
        if _is_meaningless_message(visitor_message) or _is_vague_question(
            visitor_message
        ):
            return build_general_assistant_reply(
                visitor_message, language=language
            )

        chunks = await database_sync_to_async(retrieve_relevant_chunks)(
            self.customer_user,
            visitor_message,
            ai_settings.max_context_chunks,
        )
        if not chunks:
            intents = _query_intents(visitor_message)
            if "pricing" in intents:
                if language == "vi":
                    return (
                        "Mình chưa có đủ dữ liệu bảng giá/sản phẩm để trả lời chính xác. "
                        "Bạn vui lòng cho biết bạn quan tâm sản phẩm nào hoặc chờ nhân viên hỗ trợ."
                    )
                return (
                    "I don't have enough pricing/product data to answer accurately. "
                    "Please tell me which product you mean, or wait for a human agent."
                )
            return build_general_assistant_reply(
                visitor_message, language=language
            )

        prompt = build_prompt(visitor_message, chunks, ai_settings)
        try:
            reply = await call_ollama_async(prompt, ai_settings)
        except (
            urllib.error.URLError,
            TimeoutError,
            socket.timeout,
            OSError,
            json.JSONDecodeError,
        ) as exc:
            logger.warning(
                "Local AI auto-reply failed for room %s: %s",
                self.chat_room.id,
                exc,
            )
            return None

        if reply:
            return reply[:4000]
        return build_general_assistant_reply(visitor_message, language=language)


class ChatForAdminConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        # Admin must be authenticated
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return

        # Admin group name for WebSocket global notifications (e.g. new chat rooms)
        self.room_group_admin_name = f"admin_{self.user.token}"

        # Add the admin to their own global group
        await self.channel_layer.group_add(
            self.room_group_admin_name, self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Remove admin from their own global group
        if hasattr(self, "room_group_admin_name"):
            await discard_channel_group(
                self.channel_layer,
                self.room_group_admin_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        # Parse the received message
        text_data_json = json.loads(text_data)
        message = text_data_json.get("message", "").strip()
        chat_room_id = text_data_json.get("chat_room_id")

        if message and chat_room_id:
            # Save the message
            await self.create_message(chat_room_id, message)

            # Broadcast the message to the chat room group so the participant receives it
            await self.channel_layer.group_send(
                f"chat_room_{chat_room_id}",
                {
                    "type": "chat_message",
                    "message": message,
                    "sender_type": "USER",
                    "chat_room_id": chat_room_id,
                },
            )

            # Notify all connected admin sockets about the outgoing message
            await self.channel_layer.group_send(
                self.room_group_admin_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender_type": "USER",
                    "chat_room_id": chat_room_id,
                },
            )

    async def chat_message(self, event):
        # Send the message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message": event["message"],
                    "sender_type": event["sender_type"],
                    "chat_room_id": event["chat_room_id"],
                }
            )
        )

    async def new_room(self, event):
        # Admin receives all realtime notifications through its own admin group.
        room_id = event["room_id"]

        # Send a notification to the admin UI to append the new chat room to the sidebar
        await self.send(
            text_data=json.dumps(
                {
                    "type": "new_room",
                    "room_id": room_id,
                    "participant_name": event["participant_name"],
                }
            )
        )

    @database_sync_to_async
    def get_all_chat_rooms(self):
        # Fetch all chat room IDs for the current admin user
        chat_rooms = ChatRoom.objects.filter(user=self.user).values_list(
            "id", flat=True
        )
        return [str(rid) for rid in chat_rooms]

    @database_sync_to_async
    def create_message(self, chat_room_id, message):
        # Create a new message from the admin
        return ChatMessage.objects.create(
            chat_room_id=chat_room_id, sender_type="USER", content=message
        )
