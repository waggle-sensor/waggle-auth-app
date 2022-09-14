from django.urls import path
from . import views


urlpatterns = [
    # path("profile-allow-list/<str:username>", views.allow_list),
    path("profile-node-allow-list/<str:username>", views.profile_node_allow_list),
    # path("node-allow-list/<str:username>/develop", views.list_develop_access),
]

# maybe we just have nodes belong to a single project. that