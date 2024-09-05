from django.db import models
import uuid

from users.models import Participant, User

SENDER_TYPE = ["USER", "PARTICIPANT"]


class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_rooms"
    )
    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="chat_messages"
    )


class ChatMessage(models.Model):
    SENDER_TYPE_CHOICES = [(item, item) for item in SENDER_TYPE]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="chat_messages"
    )
    sender_type = models.CharField(
        max_length=20, choices=SENDER_TYPE_CHOICES, default="USER"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
