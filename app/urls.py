from django.urls import path
from . import views

app_name = "app"

urlpatterns = [
    path("profiles/<str:username>/access", views.profile_access, name="profile_access"),
]
