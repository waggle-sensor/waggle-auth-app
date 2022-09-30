from django.conf import settings
from django.contrib.auth import login, logout, get_user_model
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from secrets import compare_digest, token_urlsafe
import requests
from .models import Profile


User = get_user_model()


class ProfileAccessView(APIView):

    def get(self, request, username, format=None):
        try:
            user = User.objects.get(username=username)
            profile = user.profile
        except (User.DoesNotExist, Profile.DoesNotExist):
            raise Http404

        access_by_vsn = {}

        for access in ["develop", "schedule", "access_files"]:
            vsns = profile.projects.filter(**{
                f"profilemembership__can_{access}": True,
                f"nodemembership__can_{access}": True,
            }).values_list("node__vsn", flat=True)

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

    username = userinfo.get("preferred_username")
    if username is None:
        return JsonResponse({"error": "missing username from authorization server"}, status=status.HTTP_502_BAD_GATEWAY)

    user, _ = User.objects.update_or_create(
        username=username,
        email=userinfo.get("email", ""),
    )

    Profile.objects.update_or_create(
        user=user,
        name=userinfo.get("name", ""),
        organization=userinfo.get("organization", ""),
    )

    login(request, user)

    return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL, status=status.HTTP_302_FOUND)


def oidc_logout(request: HttpRequest) -> HttpResponse:
    logout(request)
    return HttpResponseRedirect(settings.LOGOUT_REDIRECT_URL, status=status.HTTP_302_FOUND)


def exchange_code_for_access_token(code: str) -> str:
    uri = get_oidc_token_uri(code)
    r = requests.post(uri, headers={
        "Accept": "application/json",
    })
    r.raise_for_status()
    return r.json()["access_token"]


def get_oidc_userinfo(access_token: str):
    r = requests.get(settings.OAUTH2_USERINFO_ENDPOINT, headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
    })
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
