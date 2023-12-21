from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ManifestViewSet,
    SensorHardwareViewSet,
    NodeBuildViewSet,
    ComputeViewSet,
    LorawanDeviceView,
    LorawanConnectionView,
    LorawanKeysView,
    SensorHardwareViewSet_CRUD
)

app_name = "manifests"

router = DefaultRouter()
router.register(r"manifests", ManifestViewSet, basename="manifest")
router.register(r"computes", ComputeViewSet)
router.register(r"sensors", SensorHardwareViewSet, basename="sensors")
router.register(r"node-builds", NodeBuildViewSet)
router.register(r"lorawandevices", LorawanDeviceView, basename="lorawandevices")
router.register(
    r"lorawanconnections", LorawanConnectionView, basename="lorawanconnections"
)
router.register(r"sensorhardwares", SensorHardwareViewSet_CRUD, basename="sensorhardwares")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "lorawanconnections/",
        LorawanConnectionView.as_view({"post": "create"}),
        name="C_lorawan_connection",
    ),
    path(
        "lorawanconnections/<str:node_vsn>/<str:lorawan_deveui>/",
        LorawanConnectionView.as_view(
            {
                "patch": "partial_update",
                "put": "update",
                "get": "retrieve",
                "delete": "destroy",
            }
        ),
        name="URD_lorawan_connection",
    ),
    path(
        "lorawankeys/",
        LorawanKeysView.as_view({"post": "create"}),
        name="C_lorawan_key",
    ),
    path(
        "lorawankeys/<str:node_vsn>/<str:lorawan_deveui>/",
        LorawanKeysView.as_view(
            {
                "patch": "partial_update",
                "put": "update",
                "get": "retrieve",
                "delete": "destroy",
            }
        ),
        name="URD_lorawan_key",
    ),
]
