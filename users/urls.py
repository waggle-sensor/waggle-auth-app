from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = format_suffix_patterns([
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("users/~self", views.UserSelfDetailView.as_view(), name="user-detail-self"),
    path("users/<str:username>", views.UserDetailView.as_view(), name="user-detail"),
])
