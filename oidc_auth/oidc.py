from django.conf import settings
from django.utils.http import urlencode
import requests


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
