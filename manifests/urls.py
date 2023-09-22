from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ManifestViewSet, SensorHardwareViewSet, NodeBuildViewSet

app_name = "manifests"

router = DefaultRouter()
router.register("manifests", ManifestViewSet)
router.register("sensors", SensorHardwareViewSet)
router.register("node-builds", NodeBuildViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
