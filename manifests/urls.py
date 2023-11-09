from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ManifestViewSet,
    SensorHardwareViewSet,
    NodeBuildViewSet,
    ComputeViewSet,
    LorawanDeviceView,
    LorawanConnectionView, NodesViewSet,
)

app_name = "manifests"

router = DefaultRouter()
router.register(r"manifests", ManifestViewSet, basename="manifest")
router.register(r"computes", ComputeViewSet)
router.register(r"sensors", SensorHardwareViewSet)
router.register(r"node-builds", NodeBuildViewSet)
router.register(r"nodes", NodesViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "lorawandevices/create/",
        LorawanDeviceView.as_view(),
        name="create_lorawan_device",
    ),
    path(
        "lorawandevices/update/<str:deveui>/",
        LorawanDeviceView.as_view(),
        name="update_lorawan_device",
    ),
    path(
        "lorawandevices/<str:deveui>/",
        LorawanDeviceView.as_view(),
        name="retrieve_lorawan_device",
    ),
    path(
        "lorawanconnections/create/",
        LorawanConnectionView.as_view(),
        name="create_lorawan_connection",
    ),
    path(
        "lorawanconnections/update/<str:node_vsn>/<str:lorawan_deveui>/",
        LorawanConnectionView.as_view(),
        name="update_lorawan_connection",
    ),
    path(
        "lorawanconnections/<str:node_vsn>/<str:lorawan_deveui>/",
        LorawanConnectionView.as_view(),
        name="retrieve_lorawan_connection",
    ),
]
