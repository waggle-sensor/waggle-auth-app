from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

def get_user_token_keyword():
    """
    Return the Token keyword for Users that is active in this project.
    """
    try:
        return settings.AUTH_USER_KEYWORD
    except AttributeError:
        raise ImproperlyConfigured(
            "AUTH_USER_KEYWORD needs to be configured in settings"
        )