from .base import *

DEBUG = env("DEBUG", bool, False)
SECRET_KEY = env("SECRET_KEY")

DATABASES = {"default": env.db()}

# Important! We have made these configuration choices assuming that our app will be behind
# a reverse proxy like an nginx ingress controller.
#
# If this is not the case, please pause and read up on the correct settings to use for this.
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
