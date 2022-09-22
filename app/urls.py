from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import (
    NodeListView,
    NodeDetailView,
    ProfileAccessView,
)

app_name = "app"

urlpatterns = format_suffix_patterns([
    path("nodes/", NodeListView.as_view(), name="node_list"),
    path("nodes/<str:vsn>", NodeDetailView.as_view(), name="node_detail"),
    path("profiles/<str:username>/access", ProfileAccessView.as_view(), name="profile_access"),
])
