from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

app_name = "app"

urlpatterns = [
    path("login/", views.oidc_login, name="oidc_login"),
    path("logout/", views.oidc_logout, name="oidc_logout"),
    path("globus-auth-redirect/", views.oidc_callback, name="oidc_callback"),
] + format_suffix_patterns([
    path("profiles/<str:username>/access", views.UserAccessView.as_view(), name="user_access"),
])
