from django.db import models
import uuid

from users.models import Participant, User

SENDER_TYPE = ["USER", "PARTICIPANT"]


class CustomerKey(models.Model):
    key = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="customer_keys"
    )
    is_active = models.BooleanField(default=True)
    plan = models.CharField(max_length=20, default="FREE")
    history_limit = models.PositiveIntegerField(default=50)
    allow_anonymous = models.BooleanField(default=True)
    show_social_links = models.BooleanField(default=False)
    social_facebook = models.URLField(max_length=255, null=True, blank=True)
    social_zalo = models.CharField(max_length=100, null=True, blank=True)
    social_phone = models.CharField(max_length=50, null=True, blank=True)
    widget_position = models.CharField(max_length=20, default="bottom-right")
    created_at = models.DateTimeField(auto_now_add=True)


class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_rooms"
    )
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        null=True,
        blank=True,
    )
    customer_key = models.ForeignKey(
        CustomerKey,
        on_delete=models.CASCADE,
        related_name="chat_rooms",
        default=None,
        null=True,
        blank=True,
    )
    unread_count = models.PositiveIntegerField(default=0)
    last_activity_at = models.DateTimeField(null=True, blank=True)


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

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["chat_room", "created_at"])]


from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_customer_key(sender, instance, created, **kwargs):
    if created:
        # Create CustomerKey
        customer_key = CustomerKey.objects.create(user=instance)
        # Update User with the linked CustomerKey
        instance.customer_key = customer_key
        instance.save(update_fields=["customer_key"])


@receiver(post_save, sender=ChatMessage)
def update_room_activity_and_unread(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        room = instance.chat_room
        if instance.sender_type == "PARTICIPANT":
            room.unread_count = (room.unread_count or 0) + 1
        room.last_activity_at = instance.created_at
        room.save(
            update_fields=[
                field
                for field in ["unread_count", "last_activity_at"]
                if getattr(room, field, None) is not None
            ]
        )
    except Exception:
        # Be conservative: don't crash the save hook
        pass
