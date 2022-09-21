from django.contrib.auth.models import User
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Profile


class ProfileAccessView(APIView):

    def get(self, request, username, format=None):
        try:
            user = User.objects.get(username=username)
            profile = user.profile
        except (User.DoesNotExist, Profile.DoesNotExist):
            raise Http404

        access_by_vsn = {}

        for access in ["develop", "schedule", "access_files"]:
            vsns = profile.get_nodes_with_access(access).values_list("vsn", flat=True)

            for vsn in vsns:
                if vsn not in access_by_vsn:
                    access_by_vsn[vsn] = set()
                access_by_vsn[vsn].add(access)

        items = [{"vsn": vsn, "access": sorted(access)} for vsn, access in sorted(access_by_vsn.items())]
        return Response({"items": items})
