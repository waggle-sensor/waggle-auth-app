from django.urls import path
from . import views

urlpatterns = [
    path('manifests/', views.NodeList.as_view(), name="nodes"),
    path('manifests/<str:vsn>/', views.NodeFilterList.as_view(), name="node-filter"),
    path('sensors/', views.SensorHardwareListView.as_view(), name="sensor_list"),
    path('sensors/<str:hardware>/', views.SensorHardwareDetailView.as_view(), name="sensor_detail"),
]
