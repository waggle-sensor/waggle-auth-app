"""
ChirpStack Orchestrator URL routing.
"""
from rest_framework.routers import DefaultRouter
from .views import (
    ApplicationViewSet, DeviceViewSet,
    GatewayViewSet, DeviceProfileViewSet,
)

router = DefaultRouter()
router.register(r'(?P<vsn>[^/]+)/apps',            ApplicationViewSet,   basename='app')
router.register(r'(?P<vsn>[^/]+)/devices',         DeviceViewSet,        basename='device')
router.register(r'(?P<vsn>[^/]+)/gateways',        GatewayViewSet,       basename='gateway')
router.register(r'(?P<vsn>[^/]+)/device-profiles', DeviceProfileViewSet, basename='profile')

urlpatterns = router.urls