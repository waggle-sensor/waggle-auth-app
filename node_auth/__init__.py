import django
from django.apps import apps as django_apps
from django.conf import settings

if django.VERSION < (3, 2):
    default_app_config = "rest_framework.authtoken.apps.AuthTokenConfig"

def get_node_model():
    """
    Return the Node model that is active in this project.
    """
    try:
        return django_apps.get_model(settings.AUTH_NODE_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            "AUTH_NODE_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "AUTH_NODE_MODEL refers to model '%s' that has not been installed"
            % settings.AUTH_NODE_MODEL
        )

def get_token_model():
    """
    Return the Token model that is active in this project.
    """
    try:
        return django_apps.get_model(settings.AUTH_NODE_TOKEN_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            "AUTH_NODE_TOKEN_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "AUTH_NODE_TOKEN_MODEL refers to model '%s' that has not been installed"
            % settings.AUTH_NODE_TOKEN_MODEL
        )

def get_token_keyword():
    """
    Return the Token keyword that is active in this project.
    """
    try:
        return settings.AUTH_NODE_KEYWORD
    except AttributeError:
        raise ImproperlyConfigured(
            "AUTH_NODE_KEYWORD needs to be configured in settings"
        )
