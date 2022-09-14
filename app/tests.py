from django.test import TestCase
from django.contrib.auth.models import User
from .models import Profile, Project, Node, ProfileMembership, NodeMembership


class TestApp(TestCase):
    # fixtures = ["testdata.json"]

    def testListAccess(self):
        profile_membership = [
            ("ada", "dawn", {"can_develop": True}),
            ("ada", "sage", {"can_develop": True}),
            ("jed", "sage", {"can_schedule": True}),
            ("tom", "dawn", {"can_develop": True, "can_schedule": True}),
            ("tom", "waggle", {"can_develop": True, "can_schedule": True}),
        ]

        node_membership = [
            ("dawn", "W001", {"can_develop": True})
        ]

        for username, projectname, access in profile_membership:
            user, _ = User.objects.get_or_create(username=username)
            profile, _ = Profile.objects.get_or_create(user=user)
            project, _ = Project.objects.get_or_create(name=projectname)
            ProfileMembership.objects.get_or_create(profile=profile, project=project, **access)

        for projectname, vsn, access in node_membership:
            node, _ = Node.objects.get_or_create(vsn=vsn)
            project, _ = Project.objects.get_or_create(name=projectname)
            NodeMembership.objects.get_or_create(node=node, project=project, **access)

        r = self.client.get("/app/profile-node-allow-list/ada")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {
            "items": [
                {"vsn": "W001", "access": ["develop"]},
            ]
        })
