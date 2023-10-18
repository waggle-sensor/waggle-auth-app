from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ManifestViewSet,
    SensorHardwareViewSet,
    NodeBuildViewSet,
    ComputeViewSet
)
from . import views

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
        views.LorawanDeviceView.as_view(), 
        name='create_lorawan_device'),
    path(
        'lorawandevices/update/<str:deveui>/',
        views.LorawanDeviceView.as_view(),
        name='update_lorawan_device'),
    path(
        'lorawanconnections/create/', 
        views.LorawanConnectionView.as_view(), 
        name='create_lorawan_connection'),
    path(
        'lorawanconnections/update/<str:node_vsn>/<str:lorawan_deveui>/',
        views.LorawanConnectionView.as_view(),
        name='update_lorawan_connection')
]
