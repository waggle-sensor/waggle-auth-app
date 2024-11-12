from rest_framework.permissions import BasePermission
from django.http import JsonResponse
from rest_framework import status
from opa_client import OpaClient
from opa import get_opa_host, get_opa_port, get_opa_default_policy, get_opa_default_rule

class OpaPermission(BasePermission):
    """
    Allows access Based on Open Policy Agent policies.
    """

    def __init__(self):
        self._client = OpaClient(host=get_opa_host(), port=get_opa_port())
        self._policy = get_opa_default_policy()
        self._rule = get_opa_default_rule

    def _check_opa_permission(self, request, view, obj=None):
        """
        Helper function to send request data and object data (if available) to OPA.
        """
        # Use the policy_name, rule_name, & extra_attrs defined on the view class
        # If not set, use default
        extra_attrs = getattr(view, "opa_extra_input_attrs", {})
        policy_name = getattr(view, "opa_policy", self._policy)
        rule_name = getattr(view, "opa_rule", self._rule)

        # Default data sent to OPA
        input_data = {
            "user": {
                "username": request.user.username if request.user.is_authenticated else "AnonymousUser",
                "groups": list(request.user.groups.values_list("name", flat=True))
            },
            "method": request.method,
            "path": request.path,
            "query_params": request.query_params.dict(),
            "view_name": view.__class__.__name__,
            "extra_attrs": extra_attrs,
        }

        # If object data is provided, include it in the input to OPA
        if obj:
            input_data["record_data"] = obj

        try:
            response = self._client.check_permission(
                input_data={"input": input_data},
                policy_name=policy_name,
                rule_name=rule_name,
            )
        except Exception as err:
            return JsonResponse(data={"message": f"[OPA] Internal Error, {err}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        allowed = response.get("result", False)
        if not allowed:
            return JsonResponse(data={"message": "[OPA] User not allowed"}, status=status.HTTP_403_FORBIDDEN)

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

