from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("chat/", views.chat_view, name="chat"),
    path("profile/", views.profile_view, name="profile"),
]
