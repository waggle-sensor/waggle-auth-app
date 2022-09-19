from .base import *

SECRET_KEY = "django-insecure-$!4^oa&ws#nes5lo@y#7ljtsj_l+sau34a(8qb&cy-&8%gd-fp"
DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
