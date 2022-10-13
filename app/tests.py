from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import status
from .models import Project, Node, UserMembership, NodeMembership

User = get_user_model()


class TestApp(TestCase):

    def testToken(self):
        admin_token = self.setUpToken("admin", is_admin=True)
        user_token = self.setUpToken("user", is_admin=False)

        r = self.client.get("/token")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        r = self.client.get("/token", HTTP_AUTHORIZATION=f"Sage {admin_token}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertDictContainsSubset({
            "token": admin_token.key,
        }, r.json())

        r = self.client.get("/token", HTTP_AUTHORIZATION=f"Sage {user_token}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertDictContainsSubset({
            "token": user_token.key,
        }, r.json())

        # NOTE sage-auth responds with:
        # {"token": "...", "user_uuid": "...", "expires": "1/1/2023"}

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
            "is_staff": True,
            "is_superuser": True,
        }, r.json())

        r = self.client.get("/users/~self", HTTP_AUTHORIZATION=f"Sage {user_token}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertDictContainsSubset({
            "username": "user",
            "is_staff": False,
            "is_superuser": False,
        }, r.json())

    def testListUserAccess(self):
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
        r = self.client.get("/users/ada/access")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        # require admin permissions for this endpoint
        r = self.client.get("/users/ada/access", HTTP_AUTHORIZATION=f"Sage {user_token}")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

        # check responses
        r = self.client.get("/users/ada/access", HTTP_AUTHORIZATION=f"Sage {admin_token}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json(), [
            {"vsn": "W001", "access": ["develop", "schedule"]},
            {"vsn": "W002", "access": ["develop"]},
            {"vsn": "W003", "access": ["develop"]},
        ])

        r = self.client.get("/users/jed/access", HTTP_AUTHORIZATION=f"Sage {admin_token}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json(), [
            {"vsn": "W001", "access": ["schedule"]},
            {"vsn": "W002", "access": ["develop"]},
            {"vsn": "W003", "access": ["develop", "schedule"]},
        ])

        r = self.client.get("/users/tom/access", HTTP_AUTHORIZATION=f"Sage {admin_token}")
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

    def testListProfileAccess(self):
        # NOTE this is a regression test to ensure /profiles/ is left open to avoid breaking current scheduler behavior
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

        # check responses
        r = self.client.get("/profiles/ada/access")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json(), [
            {"vsn": "W001", "access": ["develop", "schedule"]},
            {"vsn": "W002", "access": ["develop"]},
            {"vsn": "W003", "access": ["develop"]},
        ])

        r = self.client.get("/profiles/jed/access")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json(), [
            {"vsn": "W001", "access": ["schedule"]},
            {"vsn": "W002", "access": ["develop"]},
            {"vsn": "W003", "access": ["develop", "schedule"]},
        ])

        r = self.client.get("/profiles/tom/access")
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
    
    def testHomeMissingGlobusInfo(self):
        user = User.objects.create(username="user")
        self.client.force_login(user)
        
        User.objects.update(username="user", globus_subject=None, globus_preferred_username=None)
        r = self.client.get("/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        text = r.content.decode()
        self.assertEqual("Your account requires some additional setup!" in text)

        User.objects.update(username="user", globus_subject="1234-4567", globus_preferred_username=None)
        r = self.client.get("/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        text = r.content.decode()
        self.assertEqual("Your account requires some additional setup!" in text)

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
        user = User.objects.create(username=username, is_staff=is_admin, is_superuser=is_admin)
        return Token.objects.create(user=user)
