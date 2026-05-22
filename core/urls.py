"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path, re_path

urlpatterns = [
    path("supper-admin/", admin.site.urls),
    path("admin/", include("users.urls")),
]

urlpatterns += staticfiles_urlpatterns()

# Always-on fallback static serving for ASGI/Daphne without an external web server.
# This keeps `/static/...` working even when DEBUG is misconfigured.
from django.contrib.staticfiles import finders
from django.http import FileResponse, Http404


def _static_serve(request, path):
    absolute = finders.find(path)
    if not absolute:
        raise Http404()
    return FileResponse(open(absolute, "rb"))


urlpatterns += [
    re_path(r"static/(?P<path>.*)", _static_serve),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
