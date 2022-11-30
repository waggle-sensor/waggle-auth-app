from django.urls import include, path
from . import views

urlpatterns = [
    path('manifests/', views.NodeList.as_view(), name="nodes"),
    path('manifests/<str:vsn>/', views.NodeFilterList.as_view(), name="node-filter"),
]
