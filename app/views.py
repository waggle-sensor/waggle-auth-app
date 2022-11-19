from django.conf import settings
from django.contrib.auth import login, get_user_model
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from .serializers import UserSerializer, UserProfileSerializer
from .forms import UpdateSSHPublicKeysForm, CompleteLoginForm
from .permissions import IsSelf
from django_slack import slack_message

User = get_user_model()


class HomeView(TemplateView):
    template_name = "index.html"

    def get(self, request):
        try:
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
        return Response({
            "user_uuid": str(request.user.id),
            "token": token.key,
        })


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

        return Response({
            "active": True,
            "scope": "default",
            "client_id": "some-client-id",
            "username": token.user.username,
            "exp": 0,
        })


class UserAccessView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request, username: str, format=None) -> Response:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise Http404

        access_by_vsn = {}

        for access in ["develop", "schedule", "access_files"]:
            vsns = user.project_set.filter(**{
                f"usermembership__can_{access}": True,
                f"nodemembership__can_{access}": True,
            }).values_list("nodes__vsn", flat=True)

            for vsn in vsns:
                if vsn not in access_by_vsn:
                    access_by_vsn[vsn] = set()
                access_by_vsn[vsn].add(access)

        data = [{"vsn": vsn, "access": sorted(access)} for vsn, access in sorted(access_by_vsn.items())]

        return Response(data)


class UpdateSSHPublicKeysView(LoginRequiredMixin, FormView):
    form_class = UpdateSSHPublicKeysForm
    template_name="update-my-keys.html"
    success_url = "/"

    def get_initial(self):
        return {
            "ssh_public_keys": self.request.user.ssh_public_keys
        }

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
            return HttpResponseBadRequest("missing oidc user info subject from session data")

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
        slack_message("new-user.slack", {
            "user": user,
        })

        return self.login_and_redirect(user)

    def login_and_redirect(self, user):
        login(self.request, user)

        response = redirect(self.request.session.get("oidc_auth_next", settings.LOGIN_REDIRECT_URL))

        token, _ = Token.objects.get_or_create(user=user)

        # this seems strange to set the data this way, can we tie all this to the user session?
        # users can also modify these with no real checks to protect them. that seems potentially dangerous!
        set_site_cookie(response, "sage_uuid", str(user.id))
        set_site_cookie(response, "sage_username", user.username)
        set_site_cookie(response, "sage_token", token.key)

        return response


class LogoutView(auth_views.LogoutView):

    success_url_allowed_hosts = settings.SUCCESS_URL_ALLOWED_HOSTS

    def dispatch(self, *args, **kwargs):
        response = super().dispatch(*args, **kwargs)
        response.delete_cookie("sage_uuid", domain=settings.SAGE_COOKIE_DOMAIN)
        response.delete_cookie("sage_username", domain=settings.SAGE_COOKIE_DOMAIN)
        response.delete_cookie("sage_token", domain=settings.SAGE_COOKIE_DOMAIN)
        return response


def set_site_cookie(response: HttpResponse, key: str, value: str):
    response.set_cookie(
        key=key,
        value=value,
        samesite="Strict",
        secure=settings.SESSION_COOKIE_SECURE,
        domain=settings.SAGE_COOKIE_DOMAIN,
    )
