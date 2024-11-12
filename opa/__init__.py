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
    
def get_opa_default_policy():
    """
    Return the default Open Policy Agent policy name.
    Uses "policy" as the default if AUTHZ_OPA_DEFAULT_POLICY is not set in settings.
    """
    return getattr(settings, "AUTHZ_OPA_DEFAULT_POLICY", "policy")

def get_opa_default_rule():
    """
    Return the default Open Policy Agent rule name.
    Uses "allow" as the default if AUTHZ_OPA_DEFAULT_RULE is not set in settings.
    """
    return getattr(settings, "AUTHZ_OPA_DEFAULT_RULE", "allow")