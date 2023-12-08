from pathlib import Path
from environ import Env

env = Env()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "django_prometheus",
    "django_slack",
    "corsheaders",
    "app",
    "oidc_auth",
    "manifests",
    "nested_admin",
    "node_auth",
]

AUTH_USER_MODEL = "app.User"
AUTH_USER_KEYWORD = "Sage"
AUTH_NODE_MODEL = "app.Node"
AUTH_NODE_TOKEN_MODEL = "node_auth.Token"
AUTH_NODE_KEYWORD = "node_auth"

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "node_auth.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "app.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files
STATIC_ROOT = env("STATIC_ROOT", Path, BASE_DIR / "staticfiles")
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login configuration
LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Globus OAuth2 and OIDC login settings. See README about one time setup for local use.
# TODO(sean) eventually move towards using something like django-allauth instead of implementing this on our own
OAUTH2_AUTHORIZATION_ENDPOINT = "https://auth.globus.org/v2/oauth2/authorize"
OAUTH2_TOKEN_ENDPOINT = "https://auth.globus.org/v2/oauth2/token"
OAUTH2_USERINFO_ENDPOINT = "https://auth.globus.org/v2/oauth2/userinfo"
OIDC_CLIENT_ID = env("OIDC_CLIENT_ID", str, "")
OIDC_CLIENT_SECRET = env("OIDC_CLIENT_SECRET", str, "")
OIDC_REDIRECT_PATH = env("OIDC_REDIRECT_PATH", str, "globus-auth-redirect/")

# SAGE_COOKIE_DOMAIN should be set to allow cookies to be shared across subdomains. For example,
# if you'd use .sagecontinuum.org if you want to share cookies from access.sagecontinuum.org with
# portal.sagecontinuum.org.
SAGE_COOKIE_DOMAIN = env("SAGE_COOKIE_DOMAIN", None, None)

SUCCESS_URL_ALLOWED_HOSTS = env("SUCCESS_URL_ALLOWED_HOSTS", list, [])

# Slack messaging configuration
# TODO(sean) see if we need to put any kind of timeout on this in case slack is unresponsive
SLACK_TOKEN = env("SLACK_TOKEN", str, "")

if SLACK_TOKEN == "":
    SLACK_TOKEN = "xoxb-debug"
    SLACK_BACKEND = "django_slack.backends.DisabledBackend"
else:
    SLACK_CHANNEL = env("SLACK_CHANNEL")
    SLACK_USERNAME = env("SLACK_USERNAME")

# Logging configuration
LOGGING = {
    "version": 1,
    "handlers": {
        "slack_admins": {
            "level": "ERROR",
            "filters": [],
            "class": "django_slack.log.SlackExceptionHandler",
        },
    },
    "loggers": {
        "django": {
            "level": "ERROR",
            "handlers": ["slack_admins"],
        },
    },
}

# Security settings
ALLOWED_HOSTS = env("ALLOWED_HOSTS", list, [])
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS", list, [])
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS", list, [])
CORS_ALLOWED_ORIGIN_REGEXES = env("CORS_ALLOWED_ORIGIN_REGEXES", list, [])
CORS_ALLOW_ALL_ORIGINS = env("CORS_ALLOW_ALL_ORIGINS", bool, False)
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE", bool, True)
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE", bool, True)
