from typing import Any
from django.http import (
    HttpRequest,
    HttpResponseRedirect,
)
from django.http.response import HttpResponseBase
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from app.models import Node, Project
from minio import Minio
from datetime import timedelta
from django.conf import settings


def get_presigned_url_for_download(
    method: str, job_id: str, task_id: str, node_id: str, timestamp_and_filename: str
):
    object_name = "/".join(
        ["node-data", job_id, task_id, node_id, timestamp_and_filename]
    )

    client = Minio(
        endpoint=settings.S3_ENDPOINT,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        region=settings.S3_REGION,
        secure=True,
    )

    return client.get_presigned_url(
        method=method,
        bucket_name=settings.S3_BUCKET_NAME,
        object_name=object_name,
        expires=timedelta(seconds=60),
    )


class DownloadsView(APIView):
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        try:
            self.node = Node.objects.get(mac__iexact=kwargs["node_id"])
        except Node.DoesNotExist:
            return Response("Download not found", status=status.HTTP_404_NOT_FOUND)
        return super().dispatch(request, *args, **kwargs)

    def get_permissions(self):
        if self.request.method == "HEAD" or self.node.files_public:
            return [AllowAny()]
        return [IsAuthenticated()]

    def head(
        self,
        request: HttpRequest,
        job_id: str,
        task_id: str,
        node_id: str,
        timestamp_and_filename: str,
        format=None,
    ):
        return HttpResponseRedirect(
            get_presigned_url_for_download(
                "HEAD",
                job_id,
                task_id,
                node_id,
                timestamp_and_filename,
            )
        )

    def get(
        self,
        request: HttpRequest,
        job_id: str,
        task_id: str,
        node_id: str,
        timestamp_and_filename: str,
        format=None,
    ):
        if self.node.files_public:
            return HttpResponseRedirect(
                get_presigned_url_for_download(
                    "GET",
                    job_id,
                    task_id,
                    node_id,
                    timestamp_and_filename,
                )
            )

        has_object_permission = Project.objects.filter(
            usermembership__user=request.user,
            usermembership__can_access_files=True,
            nodemembership__node=self.node,
        ).exists()
        if not has_object_permission:
            return Response("Permission denied", status=status.HTTP_403_FORBIDDEN)

        return HttpResponseRedirect(
            get_presigned_url_for_download(
                "GET",
                job_id,
                task_id,
                node_id,
                timestamp_and_filename,
            )
        )
