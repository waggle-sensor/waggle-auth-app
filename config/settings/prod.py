from .base import *

DEBUG = env("DEBUG", bool, False)
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("ALLOWED_HOSTS", list, [])
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS", list, [])
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS", list, [])
CORS_ALLOWED_ORIGIN_REGEXES = env("CORS_ALLOWED_ORIGIN_REGEXES", list, [])
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE", bool, True)
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE", bool, True)

DATABASES = {"default": env.db()}

STATIC_ROOT = "/var/www/static"

# Important! We have made these configuration choices assuming that our app will be behind
# a reverse proxy like an nginx ingress controller.
#
# If this is not the case, please pause and read up on the correct settings to use for this.
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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
