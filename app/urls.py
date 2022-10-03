from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.authtoken.views import ObtainAuthToken
from . import views

app_name = "app"

urlpatterns = [
    path("login/", views.oidc_login, name="oidc_login"),
    path("logout/", views.oidc_logout, name="oidc_logout"),
    path("globus-auth-redirect/", views.oidc_callback, name="oidc_callback"),
] + format_suffix_patterns([
    # token views
    path("token", views.TokenView.as_view(), name="my-token"),
    # user views
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("users/~self", views.UserSelfDetailView.as_view(), name="user-detail-self"),
    path("users/<str:username>", views.UserDetailView.as_view(), name="user-detail"),
    path("users/<str:username>/access", views.UserAccessView.as_view(), name="user-access"),
    # keeping old profiles/ path for now. replaced by users/.
    path("profiles/<str:username>/access", views.UserAccessView.as_view(), name="user-access"),
])
