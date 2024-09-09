from django.contrib.auth import authenticate, login, logout
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
        messages = ChatMessage.objects.filter(chat_room_id=room).all()
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
    return render(request, "admin/profile.html", {"user": request.user})


def logout_view(request):
    """
    Handle logout
    """
    logout(request)
    return redirect("login")
