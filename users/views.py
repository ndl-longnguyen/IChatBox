from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
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
    rooms = ChatRoom.objects.filter(user=request.user).all()
    messages = None
    if room:
        try:
            active_room = ChatRoom.objects.get(id=room, user=request.user)
            messages = ChatMessage.objects.filter(
                chat_room=active_room
            ).order_by("created_at")
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
            customer_key = getattr(request.user, "customer_key", None)
            if customer_key:
                customer_key.allow_anonymous = allow_anonymous
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

    messages = ChatMessage.objects.filter(chat_room=room).order_by(
        "-created_at"
    )[:limit]
    serialized = [
        {
            "sender_type": msg.sender_type,
            "message": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in reversed(list(messages))
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
        }
    )
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Headers"] = "*"
    return response
