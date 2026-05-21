from django.urls import path
from . import apis
from . import web_views

urlpatterns = [
    path("login/", web_views.login_view, name="login"),
    path("logout/", web_views.logout_view, name="logout"),
    path("register/", web_views.register_view, name="register"),
    path("chat/", web_views.chat_view, name="chat"),
    path("profile/", web_views.profile_view, name="profile"),
    path("integration/", web_views.integration_view, name="integration"),
    path(
        "widget-config/",
        apis.WidgetConfigAPIView.as_view(),
        name="widget_config",
    ),
    path("room-history/", web_views.room_history, name="room_history"),
    path(
        "widget-history/",
        apis.WidgetHistoryAPIView.as_view(),
        name="widget_history",
    ),
]
