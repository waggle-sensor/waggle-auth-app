from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ManifestViewSet,
    SensorHardwareViewSet,
    NodeBuildViewSet,
    ComputeViewSet,
)

app_name = "manifests"

router = DefaultRouter()
router.register(r"manifests", ManifestViewSet)
router.register(r"computes", ComputeViewSet)
router.register(r"sensors", SensorHardwareViewSet)
router.register(r"node-builds", NodeBuildViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        'lorawandevices/create/', 
        views.CreateLoRaWANDevice.as_view(), 
        name='create_lorawan_device')
]
