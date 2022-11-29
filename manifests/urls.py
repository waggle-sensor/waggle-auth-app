from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.index, name="homepage"),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('manifests/', views.NodeList.as_view(), name="nodes"),
    path('manifests/<str:vsn>/', views.NodeFilterList.as_view(), name="node-filter"),
]
