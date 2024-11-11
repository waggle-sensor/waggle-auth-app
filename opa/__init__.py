from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

def get_opa_host():
    """
    Return the host for Open Policy Agent.
    """
    try:
        return settings.AUTHZ_OPA_HOST
    except AttributeError:
        raise ImproperlyConfigured(
            "AUTHZ_OPA_HOST needs to be configured in settings"
        )

def get_opa_port():
    """
    Return the port used by Open Policy Agent.
    """
    try:
        return settings.AUTHZ_OPA_PORT
    except AttributeError:
        raise ImproperlyConfigured(
            "AUTHZ_OPA_PORT needs to be configured in settings"
        )