from django.conf import settings
from django.contrib.auth import login, get_user_model
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseBadRequest,
    Http404,
)
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django_slack import slack_message
from .serializers import UserSerializer, UserProfileSerializer
from .forms import UpdateSSHPublicKeysForm, CompleteLoginForm
from .permissions import IsSelf, IsMatchingUsername
from .models import Node
import re

User = get_user_model()


class HomeView(TemplateView):
    template_name = "index.html"

    def get(self, request):
        try:
            # TODO Review why we're doing this check and redirect.
            callback = request.GET["callback"]
            return redirect(f"/login/?next={callback}")
        except KeyError:
            return super().get(request)


class UserListView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class UserDetailView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser | IsSelf]
    lookup_field = "username"


class UserSelfDetailView(RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserProfileView(RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = "username"
    permission_classes = [IsAdminUser | IsSelf]


class TokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, format=None) -> Response:
        token, _ = Token.objects.get_or_create(user=request.user)
        return Response(
            {
                "user_uuid": str(request.user.id),
                "token": token.key,
            }
        )

    def delete(self, request: Request, format=None) -> Response:
        Token.objects.filter(user=request.user).delete()
        return Response()


class TokenInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, format=None) -> Response:
        token_key = request.data.get("token")

        # TODO use drf serializer to handle validation
        if token_key is None:
            return HttpResponseBadRequest("missing token data")
        if not isinstance(token_key, str):
            return HttpResponseBadRequest("invalid token data")

        token = get_object_or_404(Token, key=token_key)

        return Response(
            {
                "active": True,
                "scope": "default",
                "client_id": "some-client-id",
                "username": token.user.username,
                "exp": 0,
            }
        )


class UserAccessView(APIView):
    permission_classes = [IsAdminUser | IsMatchingUsername]

    def get(self, request: Request, username: str, format=None) -> Response:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise Http404

        # users who are not approved should not have any access
        if not user.is_approved:
            return Response([])

        access_by_vsn = {}

        for access in ["develop", "schedule", "access_files"]:
            vsns = user.project_set.filter(
                **{
                    f"usermembership__can_{access}": True,
                    f"nodemembership__can_{access}": True,
                }
            ).values_list("nodes__vsn", flat=True)

            for vsn in vsns:
                if vsn not in access_by_vsn:
                    access_by_vsn[vsn] = set()
                access_by_vsn[vsn].add(access)

        data = [
            {"vsn": vsn, "access": sorted(access)}
            for vsn, access in sorted(access_by_vsn.items())
        ]

        return Response(data)


class NodeAuthorizedKeysView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, vsn: str) -> Response:
        try:
            node = Node.objects.get(vsn=vsn)
        except Node.DoesNotExist:
            raise Http404

        queryset = node.project_set.filter(
            usermembership__can_develop=True,
            nodemembership__can_develop=True,
        )

        user_filter = request.query_params.get("user")
        if user_filter:
            queryset = queryset.filter(users__username=user_filter)

        user_ssh_public_keys = queryset.values_list(
            "users__ssh_public_keys", flat=True
        ).distinct()

        keys = []

        for s in user_ssh_public_keys:
            keys += s.splitlines()

        return HttpResponse("\n".join(keys), content_type="text/plain")
        # TODO(sean) figure out correct way to get rest framework to return plain text
        # return Response("\n".join(keys), content_type="text/plain")


class NodeUsersView(APIView):
    """
    This view provides the list of users and their ssh public keys who have developer access to a specific node.

    TODO(sean) Consider adding an endpoint which authenticates a username + ssh public key instead of providing
    the list for local tracking.
    """

    permission_classes = [AllowAny]

    # Used to filter only keys with valid type and content. This also excludes the comment to prevent accidentally
    # leaking sensitive information about user, even if this is unlikely to happen.
    ssh_public_key_pattern = re.compile(r"(ssh-\S+\s+\S+)")

    def get(self, request: Request, vsn: str) -> Response:
        try:
            node = Node.objects.get(vsn=vsn)
        except Node.DoesNotExist:
            raise Http404

        items = node.project_set.filter(
            usermembership__can_develop=True,
            nodemembership__can_develop=True,
        ).values_list("users__username", "users__ssh_public_keys")

        results = [
            {
                "user": username,
                "ssh_public_keys": "".join(
                    s + "\n"
                    for s in self.ssh_public_key_pattern.findall(ssh_public_keys)
                ),
            }
            for username, ssh_public_keys in items
        ]

        return Response(results)


class UpdateSSHPublicKeysView(LoginRequiredMixin, FormView):
    form_class = UpdateSSHPublicKeysForm
    template_name = "update-my-keys.html"
    success_url = "/"

    def get_initial(self):
        return {"ssh_public_keys": self.request.user.ssh_public_keys}

    def form_valid(self, form) -> HttpResponse:
        cleaned_data = form.cleaned_data
        user = self.request.user
        user.ssh_public_keys = cleaned_data["ssh_public_keys"]
        user.save()
        return HttpResponseRedirect("/")


class CompleteLoginView(FormView):
    form_class = CompleteLoginForm
    template_name = None

    def get(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return self.login_and_redirect(request.user)

        try:
            user_info = request.session["oidc_auth_user_info"]
        except KeyError:
            return HttpResponseBadRequest("missing oidc_auth_user_info session key")

        try:
            sub = user_info["sub"]
        except KeyError:
            return HttpResponseBadRequest(
                "missing oidc user info subject from session data"
            )

        try:
            user = User.objects.get(id=sub)
        except User.DoesNotExist:
            return super().get(request)

        return self.login_and_redirect(user)

    def form_valid(self, form):
        cleaned_data = form.cleaned_data

        user_info = self.request.session["oidc_auth_user_info"]

        user = User.objects.create_user(
            id=user_info["sub"],
            username=cleaned_data["username"],
            name=user_info.get("name"),
            email=user_info.get("email"),
            organization=user_info.get("organization"),
        )

        # notify channel of new user
        slack_message(
            "new-user.slack",
            {
                "user": user,
            },
        )

        return self.login_and_redirect(user)

    def login_and_redirect(self, user):
        login(self.request, user)

        response = redirect(
            self.request.session.get("oidc_auth_next", settings.LOGIN_REDIRECT_URL)
        )

        token, _ = Token.objects.get_or_create(user=user)

        # this seems strange to set the data this way, can we tie all this to the user session?
        # users can also modify these with no real checks to protect them. that seems potentially dangerous!
        set_site_cookie(response, "sage_uuid", str(user.id))
        set_site_cookie(response, "sage_username", user.username)
        set_site_cookie(response, "sage_token", token.key)

        return response


class LogoutView(auth_views.LogoutView):
    def get_success_url_allowed_hosts(self):
        return settings.SUCCESS_URL_ALLOWED_HOSTS

    # TODO Figure out if get_success_url is the correct function to use here.
    def get_success_url(self):
        success_url = super().get_success_url()
        redirect_uri = self.request.build_absolute_uri(success_url)
        return f"https://auth.globus.org/v2/web/logout?redirect_uri={redirect_uri}"

    def dispatch(self, *args, **kwargs):
        response = super().dispatch(*args, **kwargs)

        # delete sage cookies
        response.delete_cookie("sage_uuid", domain=settings.SAGE_COOKIE_DOMAIN)
        response.delete_cookie("sage_username", domain=settings.SAGE_COOKIE_DOMAIN)
        response.delete_cookie("sage_token", domain=settings.SAGE_COOKIE_DOMAIN)

        # NOTE get_success_url will cause this to redirect through globus logout
        return response


def set_site_cookie(response: HttpResponse, key: str, value: str):
    response.set_cookie(
        key=key,
        value=value,
        samesite="Strict",
        secure=settings.SESSION_COOKIE_SECURE,
        domain=settings.SAGE_COOKIE_DOMAIN,
    )
