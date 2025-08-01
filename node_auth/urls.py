from django.urls import path, include
from rest_framework.routers import DefaultRouter
from node_auth.views import WireGuardView

app_name = "node_auth"

router = DefaultRouter()
router.register(r"wireguard", WireGuardView, basename="wireguard")

urlpatterns = [
    path("", include(router.urls)),
]