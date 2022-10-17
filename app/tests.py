from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import status
import uuid
from .models import Project, Node, UserMembership, NodeMembership

User = get_user_model()


class TestApp(TestCase):

    def testHome(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

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


class TestLogin(TestCase):

    def testCompleteLoginAndLogout(self):
        # generate user info and set as session data to match oidc data
        user_info = {
            "sub": str(uuid.uuid4()),
            "name": "Test User",
            "email": "test@test.com",
            "preferred_username": "testuser",
            "organization": "Test Organization",
        }
        session = self.client.session
        session["oidc_auth_user_info"] = user_info
        session.save()

        # visiting the page should just render the form
        r = self.client.get("/complete-login/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        # should not login if form data is invalid
        r = self.client.post("/complete-login/", {
            "username": "someuser",
            "confirm_username": "nomatch",
        })
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertFalse(r.wsgi_request.user.is_authenticated)

        # upon successfully logging, we should be logged in as our user with
        # fields initially populated from the oidc data
        r = self.client.post("/complete-login/", {
            "username": "someuser",
            "confirm_username": "someuser",
        })
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, settings.LOGIN_REDIRECT_URL)
        user = r.wsgi_request.user
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.id, user_info["sub"])
        self.assertEqual(user.username, "someuser")
        self.assertEqual(user.name, user_info["name"])
        self.assertEqual(user.email, user_info["email"])
        self.assertEqual(user.organization, user_info["organization"])

        token = Token.objects.get(user=user)

        # check that response cookies match user info
        self.assertEqual(r.cookies["sage_uuid"].value, str(user.id))
        self.assertEqual(r.cookies["sage_username"].value, user.username)
        self.assertEqual(r.cookies["sage_token"].value, token.key)

        # logging out must tell client to delete user cookies
        r = self.client.post("/logout/")
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, settings.LOGOUT_REDIRECT_URL)
        self.assertFalse(r.wsgi_request.user.is_authenticated)
        # TODO see if test client can clear expired / deleted cookies
        self.assertEqual(r.cookies.get("sage_uuid").value, "")
        self.assertEqual(r.cookies.get("sage_username").value, "")
        self.assertEqual(r.cookies.get("sage_token").value, "")

    def testCompleteLoginRedirectToNext(self):
        user_info = {
            "sub": str(uuid.uuid4()),
            "name": "Test User",
            "email": "test@test.com",
            "preferred_username": "testuser",
            "organization": "Test Organization",
        }

        session = self.client.session
        session["oidc_auth_user_info"] = user_info
        session["oidc_auth_next"] = "https://app-portal.org/"
        session.save()

        r = self.client.post("/complete-login/", {
            "username": "someuser",
            "confirm_username": "someuser",
        })
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, "https://app-portal.org/")
        self.assertTrue(r.wsgi_request.user.is_authenticated)

    def testMissingUserInfo(self):
        r = self.client.get("/complete-login/")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(r.wsgi_request.user.is_authenticated)

    def testBadUserInfo(self):
        session = self.client.session
        session["oidc_auth_user_info"] = {"random": "fields"}
        session.save()

        r = self.client.get("/complete-login/")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(r.wsgi_request.user.is_authenticated)
