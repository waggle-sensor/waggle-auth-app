"""
DRF ViewSets backed by ChirpStack gRPC calls.  Each ViewSet supports:
  • list           → GET    /<vsn>/<resource>/
  • retrieve       → GET    /<vsn>/<resource>/<pk>/
  • create         → POST   /<vsn>/<resource>/
  • update         → PUT    /<vsn>/<resource>/<pk>/ #TODO: not implemented
  • destroy        → DELETE /<vsn>/<resource>/<pk>/
  • partial_update → PATCH  /<vsn>/<resource>/<pk>/ #TODO: not implemented

Authentication:
  • SessionAuthentication  (browser sessions)
  • UserTokenAuthentication (header token)

---------------------------------------------------------------------------
"""
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from chirpstack_orchestrator.mixins import ChirpstackMixin
from chirpstack_orchestrator.serializers import (
    ApplicationSerializer,
    DeviceSerializer,
    GatewaySerializer,
    DeviceProfileSerializer,
)

from chirpstack_api_wrapper.objects import (
    Application,
    Device,
    Gateway,
    DeviceProfile,
)
from google.protobuf.json_format import MessageToDict

# ---------------------------------------------------------------------------
#  APPLICATIONS
# ---------------------------------------------------------------------------

class ApplicationViewSet(ChirpstackMixin, viewsets.GenericViewSet):
    """
    url:  /<vsn>/apps/   and  /<vsn>/apps/<app_id>/
    """
    lookup_field = "app_id"
    serializer_class = ApplicationSerializer
    queryset = [] # Not used, we fetch data from ChirpStack directly

    def list(self, request, vsn=None):
        try:
            c        = self._client(vsn)
            tenants  = c.list_tenants()
            apps     = c.list_all_apps(tenants)
            return Response(self._todict(apps))
        except Exception as e:
            raise APIException(f"Application list error: {e}")

    def retrieve(self, request, vsn=None, app_id=None):
        try:
            app = self._client(vsn).get_app(app_id)
            return Response(self._todict(app))
        except Exception as e:
            raise APIException(f"Application detail error: {e}")

    def create(self, request, vsn=None):
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            app = Application.from_dict(ser.validated_data)
            self._client(vsn).create_app(app)
            return Response({"id": app.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            raise APIException(f"Application creation error: {e}")

    def destroy(self, request, vsn=None, app_id=None):
        try:
            self._client(vsn).delete_app(app_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            raise APIException(f"Application deletion error: {e}")


# ---------------------------------------------------------------------------
#  DEVICES
# ---------------------------------------------------------------------------

class DeviceViewSet(ChirpstackMixin, viewsets.GenericViewSet):
    """
    url:  /<vsn>/devices/   and  /<vsn>/devices/<dev_eui>/
    """
    lookup_field = "dev_eui"
    serializer_class = DeviceSerializer
    queryset = [] # Not used, we fetch data from ChirpStack directly

    def list(self, request, vsn=None):
        try:
            c        = self._client(vsn)
            tenants  = c.list_tenants()
            apps     = c.list_all_apps(tenants)
            devices  = c.list_all_devices(apps)
            return Response(self._todict(devices))
        except Exception as e:
            raise APIException(f"Device list error: {e}")

    def retrieve(self, request, vsn=None, dev_eui=None):
        try:
            device = self._client(vsn).get_device(dev_eui)
            return Response(self._todict(device))
        except Exception as e:
            raise APIException(f"Device detail error: {e}")

    def create(self, request, vsn=None):
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            device = Device.from_dict(ser.validated_data)
            self._client(vsn).create_device(device)
            return Response({"id": device.dev_eui}, status=status.HTTP_201_CREATED)
        except Exception as e:
            raise APIException(f"Device creation error: {e}")

    def destroy(self, request, vsn=None, dev_eui=None):
        try:
            self._client(vsn).delete_device(dev_eui)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            raise APIException(f"Device deletion error: {e}")


# ---------------------------------------------------------------------------
#  GATEWAYS
# ---------------------------------------------------------------------------

class GatewayViewSet(ChirpstackMixin, viewsets.GenericViewSet):
    """
    url:  /<vsn>/gateways/   and  /<vsn>/gateways/<gateway_id>/
    """
    lookup_field = "gateway_id"
    serializer_class = GatewaySerializer
    queryset = [] # Not used, we fetch data from ChirpStack directly

    def list(self, request, vsn=None):
        try:
            # ChirpStack has no "list all gateways" by tenant, so you might need
            # a custom implementation — placeholder response here.
            return Response([])
        except Exception as e:
            raise APIException(f"Gateway list error: {e}")

    def retrieve(self, request, vsn=None, gateway_id=None):
        try:
            gw = self._client(vsn).get_gateway(gateway_id)
            return Response(self._todict(gw))
        except Exception as e:
            raise APIException(f"Gateway detail error: {e}")

    def create(self, request, vsn=None):
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            gw = Gateway.from_dict(ser.validated_data)
            self._client(vsn).create_gateway(gw)
            return Response({"id": gw.gateway_id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            raise APIException(f"Gateway creation error: {e}")

    def destroy(self, request, vsn=None, gateway_id=None):
        try:
            self._client(vsn).delete_gateway(gateway_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            raise APIException(f"Gateway deletion error: {e}")


# ---------------------------------------------------------------------------
#  DEVICE PROFILES
# ---------------------------------------------------------------------------

class DeviceProfileViewSet(ChirpstackMixin, viewsets.GenericViewSet):
    """
    url:  /<vsn>/device-profiles/   and  /<vsn>/device-profiles/<profile_id>/
    """
    lookup_field = "profile_id"
    serializer_class = DeviceProfileSerializer
    queryset = [] # Not used, we fetch data from ChirpStack directly

    def list(self, request, vsn=None):
        try:
            # ChirpStack lacks a simple "list device profiles" RPC; implement if needed.
            return Response([])
        except Exception as e:
            raise APIException(f"DeviceProfile list error: {e}")

    def retrieve(self, request, vsn=None, profile_id=None):
        try:
            profile = self._client(vsn).get_device_profile(profile_id)
            return Response(self._todict(profile))
        except Exception as e:
            raise APIException(f"DeviceProfile detail error: {e}")

    def create(self, request, vsn=None):
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            profile = DeviceProfile.from_dict(ser.validated_data)
            self._client(vsn).create_device_profile(profile)
            return Response({"id": profile.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            raise APIException(f"DeviceProfile creation error: {e}")

    def destroy(self, request, vsn=None, profile_id=None):
        try:
            self._client(vsn).delete_device_profile(profile_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            raise APIException(f"DeviceProfile deletion error: {e}")
