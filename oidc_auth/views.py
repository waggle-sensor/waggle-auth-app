from secrets import token_urlsafe, compare_digest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.views import View
from rest_framework import status
from django.utils.http import urlencode
import requests

User = get_user_model()


# maybe call this authenticate or something?
class LoginView(View):

    def get(self, request: HttpRequest) -> HttpResponse:
        next_url = request.session.get("next", settings.LOGIN_REDIRECT_URL)

        if request.user.is_authenticated:
            return redirect(next_url)

        state = token_urlsafe(32)
        request.session["oidc_auth_state"] = state
        request.session["oidc_auth_next"] = next_url
        return redirect(get_authorize_uri(state))


# TODO csrf protect these views where needed!!!
# TODO clean up config and make more modular wrt the rest of the site
# TODO implement this to logout *and* wipe session info
# TODO maybe add a couple tests for check session and protection

# class LogoutView(View):

#     def get(self):
#         pass


class RedirectView(View):

    complete_login_url = None

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            code = request.GET["code"]
            state = request.GET["state"]
        except KeyError as key:
            return JsonResponse({"error": f"missing {key} param from authorization server"}, status=status.HTTP_502_BAD_GATEWAY)

        try:
            state_token = request.session["oidc_auth_state"]
        except KeyError as key:
            return HttpResponseBadRequest(f"missing {key} from client session")

        if not compare_digest(state, state_token):
            return HttpResponseBadRequest("oauth2 state and session state differ")

        try:
            access_token = exchange_code_for_access_token(code)
        except Exception:
            return JsonResponse({"error": "failed to exchange code for access token"}, status=status.HTTP_502_BAD_GATEWAY)

        try:
            user_info = get_user_info(access_token)
        except Exception:
            return JsonResponse({"error": "failed to get user info from authorization server"}, status=status.HTTP_502_BAD_GATEWAY)

        if "sub" not in user_info:
            return JsonResponse({"error": "missing user info subject from authorization server"}, status=status.HTTP_502_BAD_GATEWAY)

        request.session["oidc_auth_user_info"] = user_info
        return redirect(self.complete_login_url)


def exchange_code_for_access_token(code: str) -> str:
    uri = get_token_uri(code)
    r = requests.post(uri,
        headers={
            "Accept": "application/json",
        },
        timeout=5,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def get_user_info(access_token: str):
    r = requests.get(settings.OAUTH2_USERINFO_ENDPOINT,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        timeout=5,
    )
    r.raise_for_status()
    return r.json()


def get_authorize_uri(state: str) -> str:
    return settings.OAUTH2_AUTHORIZATION_ENDPOINT + "?" + urlencode({
        "client_id": settings.OIDC_CLIENT_ID,
        "redirect_uri": settings.OIDC_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
    })


def get_token_uri(code: str) -> str:
    return settings.OAUTH2_TOKEN_ENDPOINT + "?" + urlencode({
        "client_id": settings.OIDC_CLIENT_ID,
        "client_secret": settings.OIDC_CLIENT_SECRET,
        "redirect_uri": settings.OIDC_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": code,
    })
