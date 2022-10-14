from secrets import token_urlsafe, compare_digest
from django.conf import settings
from django.contrib.auth import login, get_user_model
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils.http import urlencode
from django.views import View
from django.views.generic import FormView
from rest_framework import status
import requests
from .forms import CreateUserForm
from .models import Identity
# TODO csrf protect these views!!!

NEXT_SESSION_KEY = "oidc_auth_next"

User = get_user_model()


class LoginView(View):

    def get(self, request: HttpRequest) -> HttpResponse:
        next_url = request.session.get("next", settings.LOGIN_REDIRECT_URL)

        if request.user.is_authenticated:
            return redirect(next_url)

        state = token_urlsafe(32)
        request.session["oidc_auth_state"] = state
        request.session["oidc_auth_next"] = next_url
        return redirect(get_oidc_authorize_uri(state))


class RedirectView(View):

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            code = request.GET["code"]
        except KeyError:
            return JsonResponse({"error": "missing code from authorization server"}, status=status.HTTP_502_BAD_GATEWAY)

        try:
            state = request.GET["state"]
        except KeyError:
            return JsonResponse({"error": "missing state from authorization server"}, status=status.HTTP_502_BAD_GATEWAY)

        try:
            state_token = request.session["oidc_auth_state"]
        except KeyError:
            return JsonResponse({"error": "missing state token from client"}, status=status.HTTP_400_BAD_REQUEST)

        if not compare_digest(state, state_token):
            return JsonResponse({"error": f"state doesn't match state cookie: {state!r} - {state_token!r}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            access_token = exchange_code_for_access_token(code)
        except Exception:
            return JsonResponse({"error": "failed to exchange code for access token"}, status=status.HTTP_502_BAD_GATEWAY)

        try:
            user_info = get_oidc_user_info(access_token)
        except Exception:
            return JsonResponse({"error": "failed to get user info from authorization server"}, status=status.HTTP_502_BAD_GATEWAY)

        if "sub" not in user_info:
            return JsonResponse({"error": "missing user info subject from authorization server"}, status=status.HTTP_502_BAD_GATEWAY)

        request.session["oidc_auth_user_info"] = user_info
        return redirect("complete-login")


class CompleteLoginView(View):
    create_user_url = None

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            user_info = request.session["oidc_auth_user_info"]
        except KeyError:
            return HttpResponseBadRequest("missing oidc_auth_user_info session key")

        try:
            sub = user_info["sub"]
        except KeyError:
            return HttpResponseBadRequest("missing oidc user info subject from session data")

        # create or update globus account using subject
        identity, _ = Identity.objects.get_or_create(sub=sub)
        identity.preferred_username = user_info.get("preferred_username")
        identity.name = user_info.get("name")
        identity.email = user_info.get("email")
        identity.organization = user_info.get("organization")
        identity.save()

        set_request_identity(request, identity)

        if identity.user is not None:
            login(request, identity.user)
            return redirect(request.session.get(NEXT_SESSION_KEY, settings.LOGIN_REDIRECT_URL))

        return redirect(self.create_user_url)


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


def get_oidc_user_info(access_token: str):
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


def get_request_identity(request: HttpRequest) -> Identity:
    return Identity.objects.get(sub=request.session["oidc_auth_sub"])


def set_request_identity(request: HttpRequest, identity: Identity):
    request.session["oidc_auth_sub"] = str(identity.sub)


class CreateUserView(FormView):
    form_class = CreateUserForm
    template_name = None

    def form_valid(self, form):
        cleaned_data = form.cleaned_data

        identity = get_request_identity(self.request)
        user = User.objects.create(username=cleaned_data["username"])
        user.name = identity.name
        user.email = identity.email
        user.organization = identity.organization
        user.save()

        identity.user = user
        identity.save()

        login(self.request, user)
        return redirect(self.request.session.get("oidc_auth_next", settings.LOGIN_REDIRECT_URL))
