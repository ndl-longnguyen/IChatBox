from django.contrib import admin

from chat.models import ChatMessage, ChatRoom, CustomerKey


@admin.action(description="Rotate key (generate new UUID)")
def rotate_customer_key(modeladmin, request, queryset):
    # One key per user currently; rotation invalidates embedded keys on websites.
    import uuid

    for customer_key in queryset:
        customer_key.key = uuid.uuid4()
        customer_key.save(update_fields=["key"])


@admin.action(description="Disable key")
def disable_customer_key(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.action(description="Enable key")
def enable_customer_key(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.register(CustomerKey)
class CustomerKeyAdmin(admin.ModelAdmin):
    list_display = (
        "key",
        "user",
        "is_active",
        "plan",
        "history_limit",
        "allow_anonymous",
        "created_at",
    )
    list_filter = ("is_active", "plan", "allow_anonymous", "created_at")
    search_fields = ("key", "user__username")
    readonly_fields = ("key", "created_at")
    actions = [rotate_customer_key, disable_customer_key, enable_customer_key]


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "participant", "customer_key")
    search_fields = (
        "id",
        "user__username",
        "participant__id",
        "participant__device",
    )
    readonly_fields = ("id",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "chat_room", "sender_type", "created_at")
    list_filter = ("sender_type", "created_at")
    search_fields = ("id", "chat_room__id", "content")
    readonly_fields = ("id", "created_at", "updated_at")
