from django.urls import path
from . import apis
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("chat/", views.chat_view, name="chat"),
    path("profile/", views.profile_view, name="profile"),
    path("integration/", views.integration_view, name="integration"),
    path(
        "widget-config/",
        apis.WidgetConfigAPIView.as_view(),
        name="widget_config",
    ),
    path("room-history/", views.room_history, name="room_history"),
    path(
        "widget-history/",
        apis.WidgetHistoryAPIView.as_view(),
        name="widget_history",
    ),
]
