from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User


def profile_access(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponse(f"no user with username {username!r}", status=404)

    profile = user.profile

    access_by_vsn = {}

    for access in ["develop", "schedule", "access_files"]:
        vsns = profile.get_nodes_with_access(access).values_list("vsn", flat=True)

        for vsn in vsns:
            if vsn not in access_by_vsn:
                access_by_vsn[vsn] = set()
            access_by_vsn[vsn].add(access)

    items = [{"vsn": vsn, "access": sorted(access)} for vsn, access in sorted(access_by_vsn.items())]
    return JsonResponse({"items": items})
