"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from oidc_auth import views as oidc_views
from django.contrib.admin.views.decorators import staff_member_required
from app.views import LogoutView

# admin site should use project login instead of custom login
# admin.site.login = staff_member_required(admin.site.login, login_url=settings.LOGIN_URL)

# admin site should also use project logout instead of custom logout
admin.site.logout = LogoutView.as_view()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path("", include("django_prometheus.urls")),
    path("", include("app.urls")),
    path("", include("manifests.urls")),
    path("_nested_admin/", include("nested_admin.urls")),
    path(
        settings.OIDC_REDIRECT_PATH,
        oidc_views.RedirectView.as_view(complete_login_url="app:complete-login"),
        name="oauth2-redirect",
    ),
]
