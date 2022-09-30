from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import UserAccessView, oidc_login, oidc_logout, oidc_callback

app_name = "app"

urlpatterns = [
    path("login/", oidc_login, name="oidc_login"),
    path("logout/", oidc_logout, name="oidc_logout"),
    path("globus-auth-redirect/", oidc_callback, name="oidc_callback"),
] + format_suffix_patterns([
    path("profiles/<str:username>/access", UserAccessView.as_view(), name="user_access"),
])
