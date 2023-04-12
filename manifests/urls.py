from django.urls import path
from . import views

app_name = "manifests"

urlpatterns = [
    path(
        "manifests/",
        views.NodeList.as_view(),
        name="manifest-list",
    ),
    path(
        "manifests/<str:vsn>/",
        views.NodeFilterList.as_view(),
        name="manifest-detail",
    ),
    path(
        "sensors/",
        views.SensorHardwareListView.as_view(),
        name="sensor-list",
    ),
    path(
        "sensors/<str:hardware>/",
        views.SensorHardwareDetailView.as_view(),
        name="sensor-detail",
    ),
]
