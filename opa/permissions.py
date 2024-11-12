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

    def has_permission(self, request, view):
        # data sent to OPA
        input_data = {"input": {
            "request": request, 
            "view": view,}}

        # Use the policy_name and rule_name defined on the view class
        # if not set use default
        policy_name = getattr(view, "opa_policy", self._policy)
        rule_name = getattr(view, "opa_rule", self._rule)

        try:
            response = self._client.check_permission(
                input_data={"input": input_data},
                policy_name=policy_name,
                rule_name=rule_name,
            )
        except Exception as err:
            return JsonResponse(data={"message": "[OPA] Internal Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        allowed = response["result"]
        if not allowed:
            return JsonResponse(data={"message": "[OPA] User not allowed"}, status=status.HTTP_403_FORBIDDEN)

        return allowed
