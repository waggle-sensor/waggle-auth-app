from .base import *

DEBUG = True
SECRET_KEY = "django-insecure-$!4^oa&ws#nes5lo@y#7ljtsj_l+sau34a(8qb&cy-&8%gd-fp"
ALLOWED_HOSTS = ["*"]
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CORS_ALLOW_ALL_ORIGINS = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

#debug toolbar requirements
INSTALLED_APPS.append("debug_toolbar")
INSTALLED_APPS.append("allauth")
INSTALLED_APPS.append("allauth.account")
INSTALLED_APPS.append("allauth.socialaccount")
INSTALLED_APPS.append("allauth.socialaccount.providers.globus")
MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
MIDDLEWARE.append("allauth.account.middleware.AccountMiddleware")
INTERNAL_IPS = [
    "127.0.0.1",
]

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    'globus': {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        'APP': {
            'client_id': env("OIDC_CLIENT_ID", str, ""),
            'secret': env("OIDC_CLIENT_SECRET", str, ""),
            'key': '',
        }
    }
}

ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
