from django.urls import path
from . import views


urlpatterns = [
    # path("profile-allow-list/<str:username>", views.allow_list),
    path("<str:username>/access", views.profile_access),
    # path("node-allow-list/<str:username>/develop", views.list_develop_access),
]

# maybe we just have nodes belong to a single project. that
