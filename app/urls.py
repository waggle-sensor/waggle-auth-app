from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.permissions import AllowAny
from oidc_auth import views as oidc_views
from . import views

app_name = "app"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("update-my-keys", views.UpdateSSHPublicKeysView.as_view(), name="update-my-keys"),
    path("complete-login/", views.CompleteLoginView.as_view(template_name="create-user.html"), name="complete-login"),
    path("login/", oidc_views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("globus-auth-redirect/", oidc_views.RedirectView.as_view(complete_login_url="app:complete-login"), name="redirect"),
] + format_suffix_patterns([
    # token views
    path("token", views.TokenView.as_view(), name="my-token"),
    path("token_info/", views.TokenInfoView.as_view(), name="token-info"),
    # user views
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("users/~self", views.UserSelfDetailView.as_view(), name="user-detail-self"),
    path("users/<str:username>", views.UserDetailView.as_view(), name="user-detail"),
    path("users/<str:username>/access", views.UserAccessView.as_view(), name="user-access"),
    # keeping old profiles/ path for now. replaced by users/.
    path("profiles/<str:username>/access", views.UserAccessView.as_view(permission_classes=[AllowAny]), name="user-access"),
    # keeping compatbility with existing portal user profiles
    path("user_profile/<str:username>", views.UserProfileView.as_view()),
])
