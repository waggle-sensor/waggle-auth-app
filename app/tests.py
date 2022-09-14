from django.test import TestCase
from django.contrib.auth.models import User
from .models import Profile, Project, Node, ProfileMembership, NodeMembership


class TestApp(TestCase):

    def testListAccess(self):
        self.setUpMembershipData(
            profile_membership=[
                ("ada", "sage", {"can_develop": True}),
                ("ada", "dawn", {"can_develop": True, "can_schedule": True}),

                ("jed", "sage", {"can_schedule": True, "can_develop": True}),

                ("tom", "sage", {"can_develop": True, "can_schedule": True}),
                ("tom", "dawn", {"can_develop": True, "can_schedule": True}),
            ],
            node_membership = [
                ("sage", "W000", {}),
                ("sage", "W001", {"can_schedule": True}),
                ("sage", "W002", {"can_develop": True}),
                ("sage", "W003", {"can_schedule": True, "can_develop": True}),

                ("dawn", "W000", {}),
                ("dawn", "W001", {"can_schedule": True, "can_develop": True}),
            ],
        )

        r = self.client.get("/app/ada/access")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {
            "items": [
                {"vsn": "W001", "access": ["develop", "schedule"]},
                {"vsn": "W002", "access": ["develop"]},
                {"vsn": "W003", "access": ["develop"]},
            ]
        })

        r = self.client.get("/app/jed/access")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {
            "items": [
                {"vsn": "W001", "access": ["schedule"]},
                {"vsn": "W002", "access": ["develop"]},
                {"vsn": "W003", "access": ["develop", "schedule"]},
            ]
        })

        r = self.client.get("/app/tom/access")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {
            "items": [
                {"vsn": "W001", "access": ["develop", "schedule"]},
                {"vsn": "W002", "access": ["develop"]},
                {"vsn": "W003", "access": ["develop", "schedule"]},
            ]
        })

    def setUpMembershipData(self, profile_membership, node_membership):
        for username, projectname, access in profile_membership:
            user, _ = User.objects.get_or_create(username=username)
            profile, _ = Profile.objects.get_or_create(user=user)
            project, _ = Project.objects.get_or_create(name=projectname)
            ProfileMembership.objects.get_or_create(profile=profile, project=project, **access)

        for projectname, vsn, access in node_membership:
            node, _ = Node.objects.get_or_create(vsn=vsn)
            project, _ = Project.objects.get_or_create(name=projectname)
            NodeMembership.objects.get_or_create(node=node, project=project, **access)
