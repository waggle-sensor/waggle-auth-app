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
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from oidc_auth import views as oidc_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path("", include("django_prometheus.urls")),
    # OIDC auth views
    path("login/", oidc_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("globus-auth-redirect/", oidc_views.RedirectView.as_view(), name="redirect"),
    path("complete-login/", oidc_views.CompleteLoginView.as_view(create_user_url="create-user"), name="complete-login"),
    path("create-user", oidc_views.CreateUserView.as_view(template_name="create-user.html"), name="create-user"),
    # App views
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("", include("app.urls")),
]
