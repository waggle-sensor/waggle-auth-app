from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Node



def list_access(request, username):
    perms = []

    user = User.objects.get(username=username)
    projects = user.profile.projects.filter(profilemembership__can_develop=True)
    nodes = Node.objects.filter(projects__in=projects, nodemembership__can_develop=True).values_list("vsn", flat=True)

    for vsn in nodes:
        perms.append((vsn, "develop"))

    user = User.objects.get(username=username)
    projects = user.profile.projects.filter(profilemembership__can_schedule=True)
    nodes = Node.objects.filter(projects__in=projects, nodemembership__can_schedule=True).values_list("vsn", flat=True)

    for vsn in nodes:
        perms.append((vsn, "schedule"))

    user = User.objects.get(username=username)
    projects = user.profile.projects.filter(profilemembership__can_access_files=True)
    nodes = Node.objects.filter(projects__in=projects, nodemembership__can_access_files=True).values_list("vsn", flat=True)

    for vsn in nodes:
        perms.append((vsn, "access_files"))

    results = {}

    for vsn, perm in perms:
        if vsn not in results:
            results[vsn] = set()
        results[vsn].add(perm)

    return JsonResponse({"nodes": {vsn: list(perms) for vsn, perms in results.items()}})



def list_develop_access(request, username):
    user = User.objects.get(username=username)
    projects = user.profile.projects.filter(profilemembership__can_develop=True)
    nodes = Node.objects.filter(projects__in=projects, nodemembership__can_develop=True).values_list("vsn", flat=True)
    return JsonResponse({"nodes": list(nodes)})
