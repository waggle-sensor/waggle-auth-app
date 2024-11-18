from rest_framework.permissions import BasePermission
from django.http import JsonResponse
from rest_framework import status
from opa_client import OpaClient
from opa import get_opa_host, get_opa_port, get_opa_default_policy, get_opa_default_rule
from django.forms.models import model_to_dict
from datetime import datetime
from django.db import models
from collections.abc import Iterable
import decimal

class OpaPermission(BasePermission):
    """
    Allows access Based on Open Policy Agent policies.
    """

    def __init__(self):
        self._client = OpaClient(host=get_opa_host(), port=get_opa_port())
        self._policy = get_opa_default_policy()
        self._rule = get_opa_default_rule()
    
    def _serialize_object(self, obj, top_level=True, get_related=False) -> dict:
        """
        Serializes a Django model instance into a JSON-compatible dictionary.
        Handles datetime fields by converting them to ISO strings.
        This function only checks fields of the top-level model (obj), not the related models of child relationships.
        """
        # Check if obj is a Django model instance
        if isinstance(obj, models.Model):

            # Serialize main fields of the model instance
            record_data = model_to_dict(obj)

            # Convert fields
            for field, value in list(record_data.items()):
                if isinstance(value, datetime):
                    record_data[field] = value.isoformat()
                elif isinstance(value, decimal.Decimal):  # Handle Decimal fields
                    record_data[field] = float(value)  # Convert Decimal to float
                elif isinstance(value, list) and all(isinstance(item, models.Model) for item in value):  # Handle list of models
                    if get_related:
                        record_data[field] = [self._serialize_object(item, top_level=False, get_related=get_related) for item in value]
                    else:
                        record_data.pop(field)


            # Handle related fields at the top level
            if top_level and get_related:
                for related_obj in obj._meta.get_fields():
                    if isinstance(related_obj, (models.OneToOneRel, models.ForeignKey)):
                        # Single related instance (OneToOneRel, ForeignKey)
                        related_instance = getattr(obj, related_obj.name, None)
                        if related_instance:
                            record_data[related_obj.name] = self._serialize_object(related_instance, top_level=False, get_related=get_related)

                    elif isinstance(related_obj, (models.ManyToOneRel, models.ManyToManyRel)):
                        # Multiple related instances (Many-to-One, Many-to-Many)
                        related_manager = getattr(obj, related_obj.get_accessor_name(), None)
                        if related_manager:
                            record_data[related_obj.get_accessor_name()] = [
                                self._serialize_object(related_instance, top_level=False, get_related=get_related) for related_instance in related_manager.all()
                            ]

            return record_data

        # For non-Django model objects, return the object's __dict__ if it exists
        return obj.__dict__ if hasattr(obj, '__dict__') else {}
    
    def _get_client_ip(self,request):
        """
        Get the IP address of the request origin
        """
        # First check the `HTTP_X_FORWARDED_FOR` header (for cases where there's a proxy or load balancer)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # The first IP in the list is the original client IP
            ip = x_forwarded_for.split(',')[0]
        else:
            # If no proxy, use the `REMOTE_ADDR` key which contains the direct IP
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _check_opa_permission(self, request, view, obj=None) -> bool:
        """
        Helper function to send request data and object data (if available) to OPA.
        Uses Attributes from View to determine what Policy, Rule, if to get related 
        records from model to send to OPA, and extra atrributes to send to OPA. If they are 
        not provided defaults are used.
        """
        # Use the policy_name, rule_name, & extra_attrs defined on the view class
        # If not set, use default
        extra_attrs = getattr(view, "opa_extra_input_attrs", {})
        policy_name = getattr(view, "opa_policy", self._policy)
        rule_name = getattr(view, "opa_rule", self._rule)
        get_related = getattr(view, "opa_get_related_models", False)

        # Default data sent to OPA
        input_data = {
            "request": {
                "node": request.node.vsn if request.node.vsn else "AnonymousNode",
                "user": {
                    "username": request.user.username if request.user.is_authenticated else "AnonymousUser",
                    "groups": list(request.user.groups.values_list("name", flat=True)),
                },
                "method": request.method,
                "path": request.path.rstrip("/").strip().split("/")[1:],
                "query_params": request.query_params.dict(),
                "client_ip_addr": self._get_client_ip(request)
            },
            "view_name": view.__class__.__name__,
            "extra_attrs": extra_attrs,
        }

        # If object data is provided, include it in the input to OPA
        if obj:
            input_data["record_data"] = self._serialize_object(obj,top_level=True, get_related=get_related)

        try:
            response = self._client.check_permission(
                input_data=input_data,
                policy_name=policy_name,
                rule_name=rule_name,
            )
        except Exception as err:
            raise Exception(f"[OPA] Internal Error, {err}")

        allowed = response.get("result", False)
        return allowed

    def has_permission(self, request, view) -> bool:
        """
        View-level permission check. This checks if the user has permission to access a view in general.
        """
        return self._check_opa_permission(request, view)

    def has_object_permission(self, request, view, obj) -> bool:
        """
        Object-level permission check. This checks if the user has permission to access a specific object.
        """
        return self._check_opa_permission(request, view, obj)

