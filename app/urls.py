from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.permissions import AllowAny
from oidc_auth import views as oidc_views
from . import views

app_name = "app"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path(
        "update-my-keys", views.UpdateSSHPublicKeysView.as_view(), name="update-my-keys"
    ),
    path(
        "complete-login/",
        views.CompleteLoginView.as_view(template_name="create-user.html"),
        name="complete-login",
    ),
    path(
        "login/",
        oidc_views.LoginView.as_view(complete_login_url="app:complete-login"),
        name="login",
    ),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path(
        "portal-logout/", views.LogoutView.as_view(redirect_field_name="callback")
    ),  # for portal compatibility
    path("nodes/<str:vsn>/authorized_keys", views.NodeAuthorizedKeysView.as_view()),
    path("nodes/<str:vsn>/users", views.NodeUsersView.as_view()),
    path("service-node-users", views.ServiceNodeUsersListView.as_view()),
] + format_suffix_patterns(
    [
        # token views
        path("token", views.TokenView.as_view(), name="my-token"),
        path("token_info/", views.TokenInfoView.as_view(), name="token-info"),
        # user views
        path("users/", views.UserListView.as_view(), name="user-list"),
        path(
            "users/~self", views.UserSelfDetailView.as_view(), name="user-detail-self"
        ),
        path(
            "users/<str:username>", views.UserDetailView.as_view(), name="user-detail"
        ),
        path(
            "users/<str:username>/access",
            views.UserAccessView.as_view(),
            name="user-access",
        ),
        path(
            "users/<str:username>/projects",
            views.UserProjectsView.as_view(),
            name="user-projects",
        ),
        # keeping old profiles/ path for now. replaced by users/.
        path(
            "profiles/<str:username>/access",
            views.UserAccessView.as_view(permission_classes=[AllowAny]),
            name="user-access-old",
        ),
        # keeping compatibility with existing portal user profiles
        path("user_profile/<str:username>", views.UserProfileView.as_view()),
        # feedback
        path("send-request/", views.SendFeedbackView.as_view(), name="send-request"),

    ]
)
