from secrets import token_urlsafe, compare_digest
from django.conf import settings
from django.contrib.auth import login, get_user_model
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.views import View
from django.views.generic import FormView
from rest_framework import status
from .forms import CreateUserForm
from .models import Identity
from . import oidc

# TODO csrf protect these views where needed!!!
# TODO clean up config and make more modular wrt the rest of the site

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
        return redirect(oidc.get_authorize_uri(state))


class RedirectView(View):

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
            access_token = oidc.exchange_code_for_access_token(code)
        except Exception:
            return JsonResponse({"error": "failed to exchange code for access token"}, status=status.HTTP_502_BAD_GATEWAY)

        try:
            user_info = oidc.get_user_info(access_token)
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


def get_request_identity(request: HttpRequest) -> Identity:
    return Identity.objects.get(sub=request.session["oidc_auth_sub"])


def set_request_identity(request: HttpRequest, identity: Identity):
    request.session["oidc_auth_sub"] = str(identity.sub)
