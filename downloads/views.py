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
from pathlib import Path
from scitokens import SciToken
from dataclasses import dataclass
import os.path
from app.models import User
import requests
from .authentication import BasicTokenPasswordAuthentication
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
    TokenAuthentication,
)
from app.authentication import TokenAuthentication as SageTokenAuthentication
import time
from unittest.mock import patch


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
    return os.path.join(
        settings.PELICAN_ROOT_FOLDER,
        item.job_id,
        item.task_id,
        item.node_id,
        item.timestamp_and_filename,
    )


def get_pelican_authz_url(item: Item):
    path = get_pelican_path(item)

    key = Path(settings.PELICAN_KEY_PATH).read_bytes()

    token = SciToken(
        key=key,
        algorithm=settings.PELICAN_ALGORITHM,
        key_id=settings.PELICAN_KEY_ID,
    )
    # See the Scitoken reference for more info on these fields:
    # https://scitokens.org/technical_docs/Claims
    token["sub"] = "test"
    token["aud"] = "ANY"
    token["ver"] = "scitoken:2.0"
    token["scope"] = f"read:{path}"

    authz = serialize_scitoken_with_lag(
        token,
        issuer=settings.PELICAN_ISSUER,
        lifetime=settings.PELICAN_LIFETIME,
        lag=60,
    ).decode()

    return f"{settings.PELICAN_ROOT_URL}{path}?authz={authz}"


# serialize_scitoken_with_lag is a **hack** to get around not being able to override the "not before"
# claim in the scitokens library. The details of this claim can be found here:
# https://scitokens.org/technical_docs/Claims
#
# As a reference, the scitokens library simply uses time.time to set the "not before" claim:
# https://github.com/scitokens/scitokens/blob/3f6400e87a76c7c25cbb4e4e6bc35f6b120c22f1/src/scitokens/scitokens.py#L142
#
# The reason we want this is that our use case redirects users to Pelican immediately and we suspect that slight
# time differences between our machines and the Pelican machines may cause some tokens to be flagged as invalid.
#
# Adding a slight buffer should allow more tolerence between these machines.
def serialize_scitoken_with_lag(token, issuer, lifetime, lag):
    current_time = time.time()

    def lag_time():
        return current_time - lag

    with patch("time.time", lag_time):
        return token.serialize(
            issuer=issuer,
            lifetime=lifetime + lag,
        )


def get_redirect_url(item: Item):
    if object_exists_in_osn(item):
        return get_osn_presigned_url(item)
    return get_pelican_authz_url(item)


def has_object_permission(user: User, node: Node) -> bool:
    return Project.objects.filter(
        usermembership__user=user,
        usermembership__can_access_files=True,
        nodemembership__node=node,
    ).exists()


class DownloadsView(APIView):

    def get_authenticators(self):
        # This is a hack to disable prompting users for basic auth when previewing protected
        # downloads from the browser.
        user_agent = self.request.headers.get("User-Agent", "").lower()

        # If user agent is any major browser, we only want to use session and token auth.
        if any(
            browser in user_agent
            for browser in ["chrome", "firefox", "safari", "edge", "opera"]
        ):
            # If it's a browser, disable Basic Auth
            return [SessionAuthentication(), TokenAuthentication()]

        # Otherwise, use all auth classes.
        return [
            BasicTokenPasswordAuthentication(),
            BasicAuthentication(),
            SessionAuthentication(),
            TokenAuthentication(),
            SageTokenAuthentication(),
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

        # TODO(sean) See if there's a cleaner way to do this. We currently compute here as we use this both in the
        # method handler and in get_permissions to allow DRF to dynamically turn on / off authentication checks for
        # public files.
        self.file_is_public = (
            self.node.files_public
            and self.node.commissioning_date is not None
            and item.timestamp() >= self.node.commissioning_date
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

        # Attempt to stat and return metadata from OSN.
        client = get_minio_client()
        object_name = get_osn_object_name(item)

        try:
            obj = client.stat_object(
                bucket_name=settings.S3_BUCKET_NAME,
                object_name=object_name,
            )
            headers = {
                "X-Object-Content-Length": str(obj.size),
                "X-Object-Content-Type": obj.content_type,
            }
            return HttpResponse(headers=headers)
        except S3Error:
            pass

        # Otherwise, fallback to Pelican.
        try:
            r = requests.head(get_pelican_authz_url(item))
            r.raise_for_status()
            headers = {}
            if "Content-Length" in r.headers:
                headers["X-Object-Content-Length"] = r.headers["Content-Length"]
            if "Content-Type" in r.headers:
                headers["X-Object-Content-Type"] = r.headers["Content-Type"]
            return HttpResponse(headers=headers)
        # TODO(sean) Narrow the scope of the exception we handle here.
        except Exception:
            pass

        return HttpResponseNotFound("File not found")

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
        if self.file_is_public or has_object_permission(request.user, self.node):
            return HttpResponseRedirect(get_redirect_url(item))
        return HttpResponse("Permission denied", status=status.HTTP_403_FORBIDDEN)
