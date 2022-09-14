from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Node



def profile_access(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile

    access_by_vsn = {}

    for access in ["develop", "schedule", "access_files"]:
        projects = profile.projects.filter(**{f"profilemembership__can_{access}": True})
        nodes = Node.objects.filter(**{"projects__in": projects, f"nodemembership__can_{access}": True}).values_list("vsn", flat=True)

        for vsn in nodes:
            if vsn not in access_by_vsn:
                access_by_vsn[vsn] = set()
            access_by_vsn[vsn].add(access)

    items = [{"vsn": vsn, "access": sorted(access)} for vsn, access in sorted(access_by_vsn.items())]
    return JsonResponse({"items": items})
