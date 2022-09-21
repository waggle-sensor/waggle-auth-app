from django.urls import path
from .views import ProfileAccessView

app_name = "app"

urlpatterns = [
    path("profiles/<str:username>/access", ProfileAccessView.as_view(), name="profile_access"),
]
