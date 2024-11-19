import decimal
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.forms.models import model_to_dict
from datetime import datetime, timezone
import uuid

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

def serialize_model(obj, top_level=True, get_related=False) -> dict:
    """
    Serializes a Django model instance into a JSON-compatible dictionary.
    Handles datetime fields by converting them to ISO strings.
    This function only checks fields of the top-level model (obj), not the related models of child relationships.
    get_related determines if the related records should be included in the dictionary.
    """
    # Check if obj is a Django model instance
    if isinstance(obj, models.Model):

        # Serialize main fields of the model instance
        record_data = model_to_dict(obj)

        # Convert fields
        for field, value in list(record_data.items()):
            if isinstance(value, datetime):
                # Convert datetime to RFC3339 format (UTC)
                record_data[field] = value.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            elif isinstance(value, decimal.Decimal):  # Handle Decimal fields
                record_data[field] = float(value)  # Convert Decimal to float
            elif isinstance(value, uuid.UUID):  # Handle UUID fields
                record_data[field] = str(value)  # Convert UUID to string
            elif isinstance(value, list) and all(isinstance(item, models.Model) for item in value):  # Handle list of models
                if get_related:
                    record_data[field] = [serialize_model(item, top_level=False, get_related=get_related) for item in value]
                else:
                    record_data.pop(field)


        # Handle related fields at the top level
        if top_level and get_related:
            for related_obj in obj._meta.get_fields():
                if isinstance(related_obj, (models.OneToOneRel, models.ForeignKey)):
                    # Single related instance (OneToOneRel, ForeignKey)
                    related_instance = getattr(obj, related_obj.name, None)
                    if related_instance:
                        record_data[related_obj.name] = serialize_model(related_instance, top_level=False, get_related=get_related)

                elif isinstance(related_obj, (models.ManyToOneRel, models.ManyToManyRel)):
                    # Multiple related instances (Many-to-One, Many-to-Many)
                    related_manager = getattr(obj, related_obj.get_accessor_name(), None)
                    if related_manager:
                        record_data[related_obj.get_accessor_name()] = [
                            serialize_model(related_instance, top_level=False, get_related=get_related) for related_instance in related_manager.all()
                        ]

        return record_data

    # For non-Django model objects, return the object's __dict__ if it exists
    return obj.__dict__ if hasattr(obj, '__dict__') else {}