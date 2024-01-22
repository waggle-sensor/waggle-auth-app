from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TokenViewSet

app_name = "node_auth"

router = DefaultRouter()
router.register(r"node-tokens", TokenViewSet, basename="node-tokens")

urlpatterns = [
    path("", include(router.urls)),
]