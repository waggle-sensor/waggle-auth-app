from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import status
from .models import Project, Node, UserMembership, NodeMembership


User = get_user_model()


class TestApp(TestCase):

    def testUserListPermissions(self):
        admin_token = self.setUpToken("admin", is_admin=True)
        user_token = self.setUpToken("user", is_admin=False)

        r = self.client.get("/users/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
        
        r = self.client.get("/users/", HTTP_AUTHORIZATION=f"Sage {user_token}")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

        r = self.client.get("/users/", HTTP_AUTHORIZATION=f"Sage {admin_token}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def testUserDetailPermissions(self):
        admin_token = self.setUpToken("admin", is_admin=True)
        user_token = self.setUpToken("user", is_admin=False)

        r = self.client.get("/users/user")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
        
        r = self.client.get("/users/user", HTTP_AUTHORIZATION=f"Sage {user_token}")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

        r = self.client.get("/users/user", HTTP_AUTHORIZATION=f"Sage {admin_token}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def testUserSelfDetail(self):
        admin_token = self.setUpToken("admin", is_admin=True)
        user_token = self.setUpToken("user", is_admin=False)

        r = self.client.get("/users/~self")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        r = self.client.get("/users/~self", HTTP_AUTHORIZATION=f"Sage {admin_token}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertDictContainsSubset({
            "username": "admin",
        }, r.json())

        r = self.client.get("/users/~self", HTTP_AUTHORIZATION=f"Sage {user_token}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertDictContainsSubset({
            "username": "user",
        }, r.json())

    def testListAccess(self):
        admin_token = self.setUpToken("admin", is_admin=True)
        user_token = self.setUpToken("user", is_admin=False)

        self.setUpMembershipData(
            profile_membership=[
                ("ada", "sage", {"can_develop": True}),
                ("ada", "dawn", {"can_develop": True, "can_schedule": True}),

                ("jed", "sage", {"can_schedule": True, "can_develop": True}),

                ("tom", "sage", {"can_develop": True, "can_schedule": True}),
                ("tom", "dawn", {"can_develop": True, "can_schedule": True, "can_access_files": True}),
            ],
            node_membership = [
                ("sage", "W000", {}),
                ("sage", "W001", {"can_schedule": True}),
                ("sage", "W002", {"can_develop": True}),
                ("sage", "W003", {"can_schedule": True, "can_develop": True}),

                ("dawn", "W000", {}),
                ("dawn", "W001", {"can_schedule": True, "can_develop": True, "can_access_files": True}),
            ],
        )

        # require auth for this endpoint
        r = self.client.get("/profiles/ada/access")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # require admin permissions for this endpoint
        r = self.client.get("/profiles/ada/access", HTTP_AUTHORIZATION=f"Sage {user_token}")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

        # check responses
        r = self.client.get("/profiles/ada/access", HTTP_AUTHORIZATION=f"Sage {admin_token}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json(), [
            {"vsn": "W001", "access": ["develop", "schedule"]},
            {"vsn": "W002", "access": ["develop"]},
            {"vsn": "W003", "access": ["develop"]},
        ])

        r = self.client.get("/profiles/jed/access", HTTP_AUTHORIZATION=f"Sage {admin_token}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json(), [
            {"vsn": "W001", "access": ["schedule"]},
            {"vsn": "W002", "access": ["develop"]},
            {"vsn": "W003", "access": ["develop", "schedule"]},
        ])

        r = self.client.get("/profiles/tom/access", HTTP_AUTHORIZATION=f"Sage {admin_token}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json(), [
            {"vsn": "W001", "access": ["access_files", "develop", "schedule"]},
            {"vsn": "W002", "access": ["develop"]},
            {"vsn": "W003", "access": ["develop", "schedule"]},
        ])
    
    def testAccessNotExist(self):
        user = User.objects.create(username="admin", is_staff=True)
        token = Token.objects.create(user=user)

        r = self.client.get("/profiles/nothere/access", HTTP_AUTHORIZATION=f"Sage {token}")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def setUpMembershipData(self, profile_membership, node_membership):
        for username, projectname, access in profile_membership:
            user, _ = User.objects.get_or_create(username=username)
            project, _ = Project.objects.get_or_create(name=projectname)
            UserMembership.objects.get_or_create(user=user, project=project, **access)

        for projectname, vsn, access in node_membership:
            node, _ = Node.objects.get_or_create(vsn=vsn)
            project, _ = Project.objects.get_or_create(name=projectname)
            NodeMembership.objects.get_or_create(node=node, project=project, **access)

    def setUpToken(self, username, is_admin):
        user = User.objects.create(username=username, is_staff=is_admin)
        return Token.objects.create(user=user)
