from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import ProfileAccessView

app_name = "app"

urlpatterns = []

# add rest_framework endpoints
urlpatterns += format_suffix_patterns([
    path("profiles/<str:username>/access", ProfileAccessView.as_view(), name="profile_access"),
])
