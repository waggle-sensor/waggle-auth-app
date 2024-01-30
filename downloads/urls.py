from django.urls import path
from .views import DownloadsView

urlpatterns = [
    path(
        "<str:job_id>/<str:task_id>/<str:node_id>/<str:timestamp_and_filename>",
        DownloadsView.as_view(),
    ),
]
