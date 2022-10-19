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
