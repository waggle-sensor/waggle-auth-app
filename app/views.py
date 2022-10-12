from django.conf import settings
from django.contrib.auth import login, logout, get_user_model
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.utils.http import urlencode
from django import forms
from django.views.generic import FormView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.authtoken.models import Token
import requests
from secrets import compare_digest, token_urlsafe
from .serializers import UserSerializer

User = get_user_model()


class UserListView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class UserDetailView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "username"
    permission_classes = [IsAdminUser]


class UserSelfDetailView(RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class TokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, format=None) -> Response:
        token, _ = Token.objects.get_or_create(user=request.user)
        return Response({"token": token.key})


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


def oidc_login(request: HttpRequest) -> HttpResponse:
    state = token_urlsafe(24)
    uri = get_oidc_authorize_uri(state)
    response = HttpResponseRedirect(uri, status=status.HTTP_302_FOUND)
    response.set_cookie("statetoken", state, max_age=60, samesite="lax")
    return response


def oidc_callback(request: HttpRequest) -> HttpResponse:
    code = request.GET.get("code")
    if code is None:
        return JsonResponse({"error": "missing code from authorization server"}, status=status.HTTP_502_BAD_GATEWAY)

    state = request.GET.get("state")
    if state is None:
        return JsonResponse({"error": "missing state from authorization server"}, status=status.HTTP_502_BAD_GATEWAY)

    state_token = request.COOKIES.get("statetoken")
    if state_token is None:
        return JsonResponse({"error": "missing state token from client"}, status=status.HTTP_400_BAD_REQUEST)

    if not compare_digest(state, state_token):
        return JsonResponse({"error": f"state doesn't match state cookie: {state!r} - {state_token!r}"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        access_token = exchange_code_for_access_token(code)
    except Exception:
        return JsonResponse({"error": "failed to exchange code for access token"}, status=status.HTTP_502_BAD_GATEWAY)

    try:
        userinfo = get_oidc_userinfo(access_token)
    except Exception:
        return JsonResponse({"error": "failed to get user info from authorization server"}, status=status.HTTP_502_BAD_GATEWAY)

    globus_subject = userinfo.get("sub")
    globus_preferred_username = userinfo.get("preferred_username")
    if globus_subject is None or globus_preferred_username is None:
        return JsonResponse({"error": "missing user info from authorization server"}, status=status.HTTP_502_BAD_GATEWAY)

    try:
        user = User.objects.get(globus_preferred_username=globus_preferred_username)
    except User.DoesNotExist:
        # setup new user with globus preferred username as username. site will prompt user to change this.
        user, _ = User.objects.get_or_create(username=globus_preferred_username)
        user.globus_subject = globus_subject
        user.globus_preferred_username = globus_preferred_username
        user.name = userinfo.get("name", "")
        user.email = userinfo.get("email", "")
        user.organization = userinfo.get("organization", "")
        user.save()

    login(request, user)

    return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL, status=status.HTTP_302_FOUND)


def oidc_logout(request: HttpRequest) -> HttpResponse:
    logout(request)
    return HttpResponseRedirect(settings.LOGOUT_REDIRECT_URL, status=status.HTTP_302_FOUND)


def exchange_code_for_access_token(code: str) -> str:
    uri = get_oidc_token_uri(code)
    r = requests.post(uri,
        headers={
            "Accept": "application/json",
        },
        timeout=5,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def get_oidc_userinfo(access_token: str):
    r = requests.get(settings.OAUTH2_USERINFO_ENDPOINT,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        timeout=5,
    )
    r.raise_for_status()
    return r.json()


def get_oidc_authorize_uri(state: str) -> str:
    return settings.OAUTH2_AUTHORIZATION_ENDPOINT + "?" + urlencode({
        "client_id": settings.OIDC_CLIENT_ID,
        "redirect_uri": settings.OIDC_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
    })


def get_oidc_token_uri(code: str) -> str:
    return settings.OAUTH2_TOKEN_ENDPOINT + "?" + urlencode({
        "client_id": settings.OIDC_CLIENT_ID,
        "client_secret": settings.OIDC_CLIENT_SECRET,
        "redirect_uri": settings.OIDC_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": code,
    })


class UpdateSSHPublicKeysForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["ssh_public_keys"]


class UpdateSSHPublicKeysView(FormView):
    form_class = UpdateSSHPublicKeysForm
    template_name="update-my-keys.html"
    success_url = "/"
    
    def get_initial(self):
        data = super().get_initial()
        data["ssh_public_keys"] = self.request.user.ssh_public_keys
        return data

    def form_valid(self, form) -> HttpResponse:
        cleaned_data = form.cleaned_data
        user = self.request.user
        user.ssh_public_keys = cleaned_data["ssh_public_keys"]
        user.save()
        return HttpResponseRedirect("/")


class UpdateUsernameForm(forms.ModelForm):
    confirm_username = forms.CharField(max_length=255)

    class Meta:
        model = User
        fields = ["username", "confirm_username"]

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        confirm_username = cleaned_data.get("confirm_username")
        if username != confirm_username:
            raise forms.ValidationError("usernames don't match")


class UpdateUsernameView(FormView):
    form_class = UpdateUsernameForm
    template_name="update-username.html"
    success_url = "/"

    def form_valid(self, form) -> HttpResponse:
        cleaned_data = form.cleaned_data
        user = self.request.user
        user.username = cleaned_data["username"]
        user.save()
        return HttpResponseRedirect("/")
