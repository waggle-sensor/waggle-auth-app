from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

def get_opa_host() -> str:
    """
    Return the host for Open Policy Agent.
    """
    try:
        return settings.AUTHZ_OPA_HOST
    except AttributeError:
        raise ImproperlyConfigured(
            "AUTHZ_OPA_HOST str needs to be configured in settings"
        )

def get_opa_port()-> int:
    """
    Return the port used by Open Policy Agent.
    """
    try:
        return settings.AUTHZ_OPA_PORT
    except AttributeError:
        raise ImproperlyConfigured(
            "AUTHZ_OPA_PORT int needs to be configured in settings"
        )
    
def get_opa_default_policy() -> str:
    """
    Return the default Open Policy Agent policy name.
    Uses "policy" as the default if AUTHZ_OPA_DEFAULT_POLICY is not set in settings.
    """
    return getattr(settings, "AUTHZ_OPA_DEFAULT_POLICY", "policies/policy.rego")

def get_opa_default_rule() -> str:
    """
    Return the default Open Policy Agent rule name.
    Uses "allow" as the default if AUTHZ_OPA_DEFAULT_RULE is not set in settings.
    """
    return getattr(settings, "AUTHZ_OPA_DEFAULT_RULE", "allow")