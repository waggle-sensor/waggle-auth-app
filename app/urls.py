from django.urls import path
from . import views


urlpatterns = [
    path("access/<str:username>", views.list_access),
    path("develop_access/<str:username>", views.list_develop_access),
]
