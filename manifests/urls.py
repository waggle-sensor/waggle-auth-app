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
)

app_name = "manifests"

router = DefaultRouter()
router.register(r"manifests", ManifestViewSet, basename="manifest")
router.register(r"computes", ComputeViewSet)
router.register(r"sensors", SensorHardwareViewSet)
router.register(r"node-builds", NodeBuildViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "lorawandevices/",
        LorawanDeviceView.as_view(),
        name="create_lorawan_device",
    ),
    path(
        "lorawandevices/<str:deveui>/",
        LorawanDeviceView.as_view(),
        name="update_lorawan_device",
    ),
    path(
        "lorawandevices/<str:deveui>/",
        LorawanDeviceView.as_view(),
        name="retrieve_lorawan_device",
    ),
    path(
        "lorawanconnections/",
        LorawanConnectionView.as_view(),
        name="create_lorawan_connection",
    ),
    path(
        "lorawanconnections/<str:node_vsn>/<str:lorawan_deveui>/",
        LorawanConnectionView.as_view(),
        name="update_lorawan_connection",
    ),
    path(
        "lorawanconnections/<str:node_vsn>/<str:lorawan_deveui>/",
        LorawanConnectionView.as_view(),
        name="retrieve_lorawan_connection",
    ),
    path(
        "lorawankeys/",
        LorawanKeysView.as_view(),
        name="create_lorawan_key",
    ),
    path(
        "lorawankeys/<str:node_vsn>/<str:lorawan_deveui>/",
        LorawanKeysView.as_view(),
        name="update_lorawan_key",
    ),
    path(
        "lorawankeys/<str:node_vsn>/<str:lorawan_deveui>/",
        LorawanKeysView.as_view(),
        name="retrieve_lorawan_key",
    ),
]
