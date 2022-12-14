from .base import *

DEBUG = True

SECRET_KEY = "django-insecure-$!4^oa&ws#nes5lo@y#7ljtsj_l+sau34a(8qb&cy-&8%gd-fp"
ALLOWED_HOSTS = ["*"]
SESSION_COOKIE_SECURE = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CORS_ALLOW_ALL_ORIGINS = True

# Slack messaging configuration
SLACK_TOKEN = "xoxb-debug"
SLACK_BACKEND = "django_slack.backends.DisabledBackend"
