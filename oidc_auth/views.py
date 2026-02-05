import logging
from secrets import token_urlsafe, compare_digest
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, login
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect, resolve_url
from django.views import View
from django.views.generic.edit import FormView
from rest_framework import status
import requests
import globus_sdk
from contextlib import ExitStack
from .forms import PasswordLoginForm

logger = logging.getLogger(__name__)
User = get_user_model()

# TODO don't need a whole view for this...just need a redirect url, so we can provide login via a button
# TODO clean up config and make more modular wrt the rest of the site
# TODO finish adding PKCE


def get_redirect_uri(request):
    return request.build_absolute_uri(resolve_url("oauth2-redirect"))


def get_auth_client():
    return globus_sdk.ConfidentialAppAuthClient(
        settings.OIDC_CLIENT_ID, settings.OIDC_CLIENT_SECRET
    )


class LoginView(View):
    complete_login_url = None

    def get(self, request: HttpRequest) -> HttpResponse:
        next_url = request.GET.get("next", settings.LOGIN_REDIRECT_URL)
        request.session["oidc_auth_next"] = next_url

        if request.user.is_authenticated:
            logger.info(
                "user %s attempted to login but was already logged in", request.user
            )
            return redirect(self.complete_login_url)

        state = token_urlsafe(32)
        request.session["oidc_auth_state"] = state

        client = get_auth_client()
        client.oauth2_start_flow(
            get_redirect_uri(request), "openid profile email", state=state
        )
        return redirect(client.oauth2_get_authorize_url())


class PasswordLoginView(FormView):
    template_name = 'password-login.html'
    form_class = PasswordLoginForm
    success_url = "/"

    def form_valid(self, form) -> HttpResponse:
        # Retrieve the cleaned username and password from the form
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        # Authenticate the user
        user = authenticate(self.request, username=username, password=password)

        if user is not None:
            # If authentication is successful, log the user in
            login(self.request, user)

        # Call the superclass method to handle the response (usually a redirect to success_url)
        return super().form_valid(form)


class RedirectView(View):
    complete_login_url = None

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            code = request.GET["code"]
            state = request.GET["state"]
        except KeyError as key:
            return JsonResponse(
                {"error": f"missing {key} param from authorization server"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            state_token = request.session["oidc_auth_state"]
        except KeyError as key:
            return HttpResponseBadRequest(f"missing {key} from client session")

        if not compare_digest(state, state_token):
            return HttpResponseBadRequest("oauth2 state and session state differ")

        with ExitStack() as es:
            client = get_auth_client()
            client.oauth2_start_flow(get_redirect_uri(request), "openid profile email")

            try:
                tokens = client.oauth2_exchange_code_for_tokens(code)
                access_token = tokens["access_token"]
            except Exception:
                return JsonResponse(
                    {"error": "failed to exchange code for access token"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            # since we only use the access token to lookup identity info for login, ensure we revoke it immediately afterwards
            # this should change in the future since we probably want to use globus access tokens everywhere instead of native tokens
            es.callback(lambda: client.oauth2_revoke_token(access_token))

            try:
                user_info = get_user_info(access_token)
            except Exception:
                return JsonResponse(
                    {"error": "failed to get user info from authorization server"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            if "sub" not in user_info:
                return JsonResponse(
                    {"error": "missing user info subject from authorization server"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            request.session["oidc_auth_user_info"] = user_info

            return redirect(self.complete_login_url)


def get_user_info(access_token: str):
    r = requests.get(
        settings.OAUTH2_USERINFO_ENDPOINT,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        timeout=5,
    )
    r.raise_for_status()
    return r.json()
