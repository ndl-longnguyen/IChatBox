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
