from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import render, redirect
from common.messages import MESSAGES
from users.forms import UserRegistrationForm
from chat.models import ChatMessage, ChatRoom

LOGIN_URL = "/admin/login"


def login_view(request):
    """
    Hanle login
    """
    if request.method == "GET":
        return render(request, "admin/signin.html")

    elif request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("chat")
        else:
            return render(
                request,
                "admin/signin.html",
                {"error": MESSAGES["error"]["login"]},
            )

    return HttpResponseNotAllowed(["GET", "POST"])


def register_view(request):
    """
    Handle register
    """
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserRegistrationForm()

    return render(request, "admin/signup.html", {"form": form})


@login_required(login_url=LOGIN_URL)
def chat_view(request):
    """
    Handle chat page
    """
    room = request.GET.get("room")
    rooms = ChatRoom.objects.filter(user=request.user).order_by(
        "-last_activity_at", "-id"
    )
    messages = None
    show_load_more = False
    if room:
        try:
            active_room = ChatRoom.objects.get(id=room, user=request.user)
            # Reset unread counter when admin opens the room
            if getattr(active_room, "unread_count", 0):
                active_room.unread_count = 0
                active_room.save(update_fields=["unread_count"])

            recent_messages = list(
                ChatMessage.objects.filter(chat_room=active_room).order_by(
                    "-created_at"
                )[:50]
            )
            messages = list(reversed(recent_messages))
            show_load_more = len(messages) == 50
        except ChatRoom.DoesNotExist:
            room = None
            messages = None
    return render(
        request,
        "admin/chat.html",
        {
            "user": request.user,
            "rooms": rooms,
            "room": room,
            "messages": messages,
            "show_load_more": show_load_more,
        },
    )


@login_required(login_url=LOGIN_URL)
def profile_view(request):
    success = None
    error = None

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_profile":
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            current_password = request.POST.get("current_password", "")
            new_password = request.POST.get("new_password", "")
            confirm_password = request.POST.get("confirm_password", "")

            if not first_name or not last_name:
                error = "First name and last name are required."
            else:
                if current_password or new_password or confirm_password:
                    if not current_password:
                        error = "Current password is required to change your password."
                    elif not request.user.check_password(current_password):
                        error = "Current password is incorrect."
                    elif new_password != confirm_password:
                        error = "New password and confirmation do not match."
                    elif not new_password:
                        error = "New password cannot be empty."
                    else:
                        request.user.set_password(new_password)

                if not error:
                    request.user.first_name = first_name
                    request.user.last_name = last_name
                    request.user.save()
                    if new_password:
                        update_session_auth_hash(request, request.user)
                    success = "Account profile saved successfully!"

        elif action == "update_widget":
            allow_anonymous = request.POST.get("allow_anonymous") == "on"
            show_social_links = request.POST.get("show_social_links") == "on"
            social_facebook = (
                request.POST.get("social_facebook", "").strip() or None
            )
            social_zalo = request.POST.get("social_zalo", "").strip() or None
            social_phone = request.POST.get("social_phone", "").strip() or None
            widget_position = request.POST.get(
                "widget_position", "bottom-right"
            )
            if widget_position not in [
                "bottom-right",
                "bottom-left",
                "top-right",
                "top-left",
            ]:
                widget_position = "bottom-right"
            customer_key = getattr(request.user, "customer_key", None)
            if customer_key:
                customer_key.allow_anonymous = allow_anonymous
                customer_key.show_social_links = show_social_links
                customer_key.social_facebook = social_facebook
                customer_key.social_zalo = social_zalo
                customer_key.social_phone = social_phone
                customer_key.widget_position = widget_position
                customer_key.save()
                success = "Widget settings saved successfully!"

    return render(
        request,
        "admin/profile.html",
        {
            "user": request.user,
            "success": success,
            "error": error,
        },
    )


@login_required(login_url=LOGIN_URL)
def integration_view(request):
    """
    Show license & integration instructions (separate page from profile/settings)
    """
    return render(request, "admin/integration.html", {"user": request.user})


def logout_view(request):
    """
    Handle logout
    """
    logout(request)
    return redirect("login")


from django.http import JsonResponse
from chat.models import CustomerKey
from users.models import Participant
from chat.models import ChatRoom, ChatMessage


def widget_config(request):
    token = request.GET.get("token")
    if not token:
        response = JsonResponse({"error": "Token is required"}, status=400)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "*"
        return response
    try:
        key = CustomerKey.objects.get(key=token)
        if not key.is_active:
            response = JsonResponse({"error": "Key is inactive"}, status=403)
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Headers"] = "*"
            return response
        response = JsonResponse(
            {
                "allow_anonymous": key.allow_anonymous,
                "plan": key.plan,
                "history_limit": key.history_limit,
                "show_social_links": key.show_social_links,
                "social_facebook": key.social_facebook,
                "social_zalo": key.social_zalo,
                "social_phone": key.social_phone,
                "widget_position": key.widget_position or "bottom-right",
            }
        )
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "*"
        return response
    except (CustomerKey.DoesNotExist, ValueError):
        response = JsonResponse({"error": "Invalid token"}, status=404)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "*"
        return response


@login_required(login_url=LOGIN_URL)
def room_history(request):
    room_id = request.GET.get("room")
    limit = request.GET.get("limit")
    before_message_id = request.GET.get("before")
    try:
        limit = int(limit) if limit else 50
    except ValueError:
        limit = 50
    limit = max(1, min(limit, 200))

    if not room_id:
        return JsonResponse({"error": "room is required"}, status=400)

    try:
        room = ChatRoom.objects.get(id=room_id, user=request.user)
    except (ChatRoom.DoesNotExist, ValueError):
        return JsonResponse({"error": "Room not found"}, status=404)

    messages_qs = ChatMessage.objects.filter(chat_room=room)
    if before_message_id:
        try:
            before_message = ChatMessage.objects.get(
                id=before_message_id, chat_room=room
            )
            messages_qs = messages_qs.filter(
                Q(created_at__lt=before_message.created_at)
                | (
                    Q(created_at=before_message.created_at)
                    & Q(id__lt=before_message.id)
                )
            )
        except (ChatMessage.DoesNotExist, ValueError):
            pass

    messages = list(messages_qs.order_by("-created_at", "-id")[: limit + 1])
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:-1]

    serialized = [
        {
            "id": str(msg.id),
            "sender_type": msg.sender_type,
            "message": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in reversed(messages)
    ]

    return JsonResponse(
        {
            "messages": serialized,
            "has_more": has_more,
            "next_cursor": serialized[0]["id"] if serialized else None,
        }
    )


def widget_history(request):
    token = request.GET.get("token")
    device = request.GET.get("device")
    limit = request.GET.get("limit")
    try:
        limit = int(limit) if limit else 50
    except ValueError:
        limit = 50
    limit = max(1, min(limit, 200))

    if not token or not device:
        response = JsonResponse(
            {"error": "token and device are required"},
            status=400,
        )
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "*"
        return response

    try:
        key = CustomerKey.objects.get(key=token)
        if not key.is_active:
            response = JsonResponse({"error": "Key is inactive"}, status=403)
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Headers"] = "*"
            return response
    except (CustomerKey.DoesNotExist, ValueError):
        response = JsonResponse({"error": "Invalid token"}, status=404)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "*"
        return response

    # Enforce plan limit (server-side source of truth)
    limit = min(limit, int(key.history_limit or 0) or 50)

    before_message_id = request.GET.get("before")
    participant = Participant.objects.filter(
        user=key.user, device=device
    ).first()
    if not participant:
        response = JsonResponse(
            {"messages": [], "participant": None},
            status=200,
        )
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "*"
        return response

    room = ChatRoom.objects.filter(
        user=key.user, participant=participant
    ).first()
    if not room:
        response = JsonResponse(
            {"messages": [], "participant": {"name": participant.name}},
            status=200,
        )
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "*"
        return response

    messages_qs = ChatMessage.objects.filter(chat_room=room)
    if before_message_id:
        try:
            before_message = ChatMessage.objects.get(
                id=before_message_id, chat_room=room
            )
            messages_qs = messages_qs.filter(
                Q(created_at__lt=before_message.created_at)
                | (
                    Q(created_at=before_message.created_at)
                    & Q(id__lt=before_message.id)
                )
            )
        except (ChatMessage.DoesNotExist, ValueError):
            pass

    messages = list(messages_qs.order_by("-created_at", "-id")[: limit + 1])
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:-1]

    serialized = [
        {
            "id": str(msg.id),
            "sender_type": msg.sender_type,
            "message": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in reversed(messages)
    ]

    response = JsonResponse(
        {
            "participant": {
                "name": participant.name,
                "email": participant.email,
                "phone": participant.phone,
                "device": participant.device,
            },
            "messages": serialized,
            "has_more": has_more,
            "next_cursor": serialized[0]["id"] if serialized else None,
        }
    )
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Headers"] = "*"
    return response
