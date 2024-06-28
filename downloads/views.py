from typing import Any
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseNotFound,
)
from django.http.response import HttpResponseBase
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from app.models import Node, Project
from minio import Minio
from minio.error import S3Error
from datetime import datetime, timedelta, timezone
from django.conf import settings
import rest_framework.authentication
import app.authentication
from .authentication import BasicTokenPasswordAuthentication
from pathlib import Path
from scitokens import SciToken
from dataclasses import dataclass


@dataclass
class Item:
    job_id: str
    task_id: str
    node_id: str
    timestamp_and_filename: str

    def timestamp(self):
        s = self.timestamp_and_filename.split("-", maxsplit=1)[0]
        nanos = float(s)
        timestamp = nanos / 1e9
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def get_minio_client():
    return Minio(
        endpoint=settings.S3_ENDPOINT,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        region=settings.S3_REGION,
        secure=True,
    )


def get_osn_object_name(item: Item):
    return "/".join(
        [
            "node-data",
            item.job_id,
            item.task_id,
            item.node_id,
            item.timestamp_and_filename,
        ]
    )


def get_osn_presigned_url(item: Item):
    client = get_minio_client()
    object_name = get_osn_object_name(item)
    return client.get_presigned_url(
        method="GET",
        bucket_name=settings.S3_BUCKET_NAME,
        object_name=object_name,
        expires=timedelta(seconds=60),
    )


def stat_osn_object(item: Item):
    client = get_minio_client()
    object_name = get_osn_object_name(item)
    return client.stat_object(
        bucket_name=settings.S3_BUCKET_NAME,
        object_name=object_name,
    )


def object_exists_in_osn(item: Item):
    client = get_minio_client()
    object_name = get_osn_object_name(item)

    try:
        client.stat_object(
            bucket_name=settings.S3_BUCKET_NAME,
            object_name=object_name,
        )
        return True
    except S3Error:
        return False


def get_pelican_path(item: Item):
    return f"/node-data/{item.job_id}/{item.task_id}/{item.node_id}/{item.timestamp_and_filename}"


def get_pelican_authz_url(item: Item):
    path = get_pelican_path(item)

    key = Path(settings.PELICAN_KEY).read_bytes()

    token = SciToken(
        key=key,
        algorithm=settings.PELICAN_ALGORITHM,
        key_id=settings.PELICAN_KEY_ID,
    )
    token["sub"] = "test"
    token["aud"] = "ANY"
    token["ver"] = "scitoken:2.0"
    token["scope"] = f"read:{path}"

    authz = token.serialize(
        issuer=settings.PELICAN_ISSUER,
        lifetime=settings.PELICAN_LIFETIME,
    ).decode()

    return f"{settings.PELICAN_BASE_URL}{path}?authz={authz}"


def get_redirect_url(item: Item):
    if object_exists_in_osn(item):
        return get_osn_presigned_url(item)
    return get_pelican_authz_url(item)


class DownloadsView(APIView):
    authentication_classes = [
        BasicTokenPasswordAuthentication,
        rest_framework.authentication.BasicAuthentication,
        rest_framework.authentication.SessionAuthentication,
        rest_framework.authentication.TokenAuthentication,
        app.authentication.TokenAuthentication,
    ]

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        try:
            self.node = Node.objects.get(mac__iexact=kwargs["node_id"])
        except Node.DoesNotExist:
            return HttpResponseNotFound("File not found")

        item = Item(
            kwargs["job_id"],
            kwargs["task_id"],
            kwargs["node_id"],
            kwargs["timestamp_and_filename"],
        )

        # TODO check ValueError here
        file_timestamp = item.timestamp()

        self.file_is_public = (
            self.node.files_public
            and self.node.commissioning_date is not None
            and file_timestamp >= self.node.commissioning_date
        )

        return super().dispatch(request, *args, **kwargs)

    def get_permissions(self):
        if self.request.method in ["OPTIONS", "HEAD"]:
            return [AllowAny()]
        if self.file_is_public:
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
        item = Item(
            job_id,
            task_id,
            node_id,
            timestamp_and_filename,
        )
        client = get_minio_client()
        object_name = get_osn_object_name(item)

        try:
            obj = client.stat_object(
                bucket_name=settings.S3_BUCKET_NAME,
                object_name=object_name,
            )
        except S3Error:
            return HttpResponseNotFound("File not found")

        headers = {
            "X-Object-Content-Length": str(obj.size),
            "X-Object-Content-Type": obj.content_type,
        }

        return HttpResponse(headers=headers)

    def get(
        self,
        request: HttpRequest,
        job_id: str,
        task_id: str,
        node_id: str,
        timestamp_and_filename: str,
        format=None,
    ):
        item = Item(
            job_id,
            task_id,
            node_id,
            timestamp_and_filename,
        )
        if self.file_is_public:
            return HttpResponseRedirect(get_redirect_url(item))

        has_object_permission = Project.objects.filter(
            usermembership__user=request.user,
            usermembership__can_access_files=True,
            nodemembership__node=self.node,
        ).exists()

        if not has_object_permission:
            return HttpResponse("Permission denied", status=status.HTTP_403_FORBIDDEN)
        return HttpResponseRedirect(get_redirect_url(item))
