from .base import *
import os

SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = os.environ["ALLOWED_HOSTS"].split()
CSRF_TRUSTED_ORIGINS = os.environ["CSRF_TRUSTED_ORIGINS"].split()

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
