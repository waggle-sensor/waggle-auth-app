from django.urls import path
from . import views

urlpatterns = [
    path('manifests/', views.NodeList.as_view(), name="manifest-list"),
    path('manifests/<str:VSN>/', views.NodeFilterList.as_view(), name="manifest-detail"),
]
