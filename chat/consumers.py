from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
import json
from urllib.parse import parse_qs
from users.models import Participant
from chat.models import ChatMessage, ChatRoom


class ChatForUserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        query_string = parse_qs(self.scope["query_string"].decode("utf-8"))
        self.token = query_string.get("token", [None])[0]
        self.username = query_string.get("username", [None])[0]

        # Check if user is anonymous or missing required parameters
        if (
            isinstance(self.user, AnonymousUser)
            or not self.username
            or not self.token
        ):
            await self.close()
            return

        # Get or create the participant and chat room
        self.participant = await self.get_or_create_participant()
        self.chat_room = await self.get_or_create_chat_room()

        # Use the chat room's ID for the group name
        self.chat_room_group_name = f"chat_room_{self.chat_room.id}"

        # Add the user to the chat room group
        await self.channel_layer.group_add(
            self.chat_room_group_name, self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the chat room group if it exists
        if hasattr(self, "chat_room_group_name"):
            await self.channel_layer.group_discard(
                self.chat_room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        # Parse the incoming message
        text_data_json = json.loads(text_data)
        message = text_data_json.get("message", "")

        if message:
            await self.create_message(message)

        # Broadcast the message to the chat room group
        await self.channel_layer.group_send(
            self.chat_room_group_name,
            {
                "type": "chat_message",
                "message": message,
            },
        )

    async def chat_message(self, event):
        # Send the message to the WebSocket
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))

    @database_sync_to_async
    def get_or_create_participant(self):
        # Get or create the participant for the user
        participant, _ = Participant.objects.get_or_create(
            user=self.user,
            defaults={"name": self.username, "device": self.token},
        )
        return participant

    @database_sync_to_async
    def get_or_create_chat_room(self):
        # Get or create a chat room for the user and participant
        chat_room, _ = ChatRoom.objects.get_or_create(
            user=self.user, participant=self.participant
        )
        return chat_room

    @database_sync_to_async
    def create_message(self, message):
        # Get or create a chat room for the user and participant
        message = ChatMessage.objects.create(
            chat_room=self.chat_room, sender_type="PARTICIPANT", content=message
        )
        return message


class ChatForAdminConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        query_string = parse_qs(self.scope["query_string"].decode("utf-8"))
        self.token = query_string.get("token", [None])[0]
        self.username = query_string.get("username", [None])[0]

        # Check if user is anonymous or missing required parameters
        if (
            isinstance(self.user, AnonymousUser)
            or not self.username
            or not self.token
        ):
            await self.close()
            return

        # Get all chat rooms for the user
        self.chat_rooms = await self.get_all_chat_room()

        # Admin group name for WebSocket
        self.room_group_admin_name = f"admin_{self.token}"

        # Add the admin to their own group
        await self.channel_layer.group_add(
            self.room_group_admin_name, self.channel_name
        )

        # Add admin to all chat room groups
        for room_id in self.chat_rooms:
            room_group_name = f"chat_room_{room_id}"
            await self.channel_layer.group_add(
                room_group_name, self.channel_name
            )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Remove admin from their own group
        if hasattr(self, "room_group_admin_name"):
            await self.channel_layer.group_discard(
                self.room_group_admin_name, self.channel_name
            )

        # Remove admin from all chat room groups
        if hasattr(self, "chat_rooms"):
            for room_id in self.chat_rooms:
                room_group_name = f"chat_room_{room_id}"
                await self.channel_layer.group_discard(
                    room_group_name, self.channel_name
                )

    async def receive(self, text_data):
        # Parse the received message
        text_data_json = json.loads(text_data)
        message = text_data_json.get("message", "")
        username = text_data_json.get("username", "")
        chat_room_id = text_data_json.get("chat_room_id")
        if message and chat_room_id:
            await self.create_message(chat_room_id, message)

        if username:
            room_group_user_name = f"user_{username}"
            # Send the message to the specified user's group
            await self.channel_layer.group_send(
                room_group_user_name,
                {"type": "chat_message", "message": message},
            )

    async def chat_message(self, event):
        # Send the message to WebSocket
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))

    @database_sync_to_async
    def get_all_chat_room(self):
        # Fetch all chat room IDs for the current admin user
        chat_rooms = ChatRoom.objects.filter(user=self.user).values_list(
            "id", flat=True
        )
        return list(chat_rooms)

    @database_sync_to_async
    def create_message(self, chat_room_id, message):
        # Get or create a chat room for the user and participant
        message = ChatMessage.objects.create(
            chat_room_id=chat_room_id, sender_type="USER", content=message
        )
        return message
