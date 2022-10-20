from .base import *
import os

DEBUG = False

SECRET_KEY = os.environ["SECRET_KEY"]
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split()
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "").split()
SESSION_COOKIE_SECURE = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": os.environ["MYSQL_HOST"],
        "USER" : os.environ["MYSQL_USER"],
        "PASSWORD"  : os.environ["MYSQL_PASSWORD"],
        "NAME" : os.environ["MYSQL_DATABASE"],
    }
}

STATIC_ROOT = "/var/www/static"

CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split()
CORS_ALLOWED_ORIGIN_REGEXES = os.environ.get("CORS_ALLOWED_ORIGIN_REGEXES", "").split()

# Important! We have made these configuration choices assuming that our app will be behind
# a reverse proxy like an nginx ingress controller.
#
# If this is not the case, please pause and read up on the correct settings to use for this.
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Slack messaging configuration
# TODO(sean) see if we need to put any kind of timeout on this in case slack is unresponsive
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL")
SLACK_USERNAME = os.environ.get("SLACK_USERNAME")
if SLACK_TOKEN is None:
    SLACK_BACKEND = "django_slack.backends.DisabledBackend"

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
