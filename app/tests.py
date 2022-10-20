from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import status
import uuid
from .models import Project, Node, UserMembership, NodeMembership

User = get_user_model()


class TestHomeView(TestCase):
    """
    TestApp tests general app features such as landing pages and APIs.
    """

    def testAsAnon(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def testAsUser(self):
        user = User.objects.create_user(username="someuser")
        self.client.force_login(user)
        r = self.client.get("/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class TestTokenView(TestCase):

    def testNeedsAuth(self):
        r = self.client.get("/token")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def testGetExistingToken(self):
        user = User.objects.create_user(username="someuser")
        token = Token.objects.create(user=user)
        self.client.force_login(user)

        r = self.client.get("/token")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertDictEqual({"token": token.key, "user_uuid": str(user.id)}, r.json())

    def testCreateTokenIfNotExists(self):
        user = User.objects.create_user(username="someuser")
        self.client.force_login(user)

        r = self.client.get("/token")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        token = Token.objects.get(user=user)
        self.assertDictEqual({"token": token.key, "user_uuid": str(user.id)}, r.json())


class TestTokenInfoView(TestCase):

    # TODO simplify this. auth doesn't actually add any protection here... if you have a real token,
    # then you can just authenticate as that user and view their own data...

    def testNeedsAuth(self):
        r = self.client.post("/token_info/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    # keep this for compatibility as ecr depends on it
    def testTokenInfo(self):
        # generate test user and token
        admin = User.objects.create_user(username="sage-data-api")
        user = User.objects.create_user(username="coolperson")
        token = Token.objects.create(user=user)

        # define helper funcs
        def post_json(data): return self.client.post("/token_info/", data, content_type="application/json")

        # endpoint should deny unauthorized request
        r = post_json({"token": token.key})
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        # logging in should allow access
        self.client.force_login(admin)

        # should show token info
        r = post_json({"token": token.key})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertDictEqual({
            "active": True,
            "scope": "default",
            "client_id": "some-client-id",
            "username": user.username,
            "exp": 0,
        }, r.json())

        # should show 404 for nonexistant token
        r = post_json({"token": "notarealtoken"})
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

        # endpoint handle missing token field
        r = post_json({"nottoken": "..."})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

        # endpoint handle bad values
        for value in [123, None, True]:
            r = post_json({"token": value})
            self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class TestUserListView(TestCase):

    def testNeedsAuth(self):
        r = self.client.get("/users/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def testAdminPermissions(self):
        self.client.force_login(User.objects.create_user(username="admin", is_staff=True, is_superuser=True))
        r = self.client.get("/users/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def testUserPermissions(self):
        self.client.force_login(User.objects.create_user(username="user"))
        r = self.client.get("/users/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


class TestUserDetailView(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="user")

    def testAdminPermissions(self):
        self.client.force_login(User.objects.create_user(username="admin", is_staff=True, is_superuser=True))
        r = self.client.get(f"/users/{self.user.username}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def testSelfPermissions(self):
        self.client.force_login(self.user)
        r = self.client.get(f"/users/{self.user.username}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def testOtherPermissions(self):
        self.client.force_login(User.objects.create_user(username="other"))
        r = self.client.get(f"/users/{self.user.username}")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


class TestAccess(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(username="theadmin", is_staff=True, is_superuser=True)
        self.user = User.objects.create_user(username="theuser")

        self.admin_token = Token.objects.create(user=self.admin)
        self.user_token = Token.objects.create(user=self.user)

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
        user = User.objects.create_user(username="admin", is_staff=True)
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
        user = User.objects.create_user(username="admin", is_staff=True)
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
        user = User.objects.create_user(username=username, is_staff=is_admin, is_superuser=is_admin)
        return Token.objects.create(user=user)


class TestUserProfile(TestCase):
    """
    TestUserProfile tests user profile permissions, get and update behavior.
    """

    def testUserProfileGet(self):
        users = [
            User.objects.create_user(username="jed", organization="some place"),
            User.objects.create_user(username="mia", organization="some lab", department="sports"),
            User.objects.create_user(username="reina", bio="did some cool stuff"),
        ]

        for user in users:
            self.client.force_login(user)
            r = self.client.get(f"/user_profile/{user.username}")
            self.assertEqual(r.status_code, status.HTTP_200_OK)
            self.assertEqual({
                "username": user.username,
                "organization": user.organization,
                "department": user.department,
                "bio": user.bio,
            }, r.json())

    def testUserProfileUpdate(self):
        username = "jed"

        user = User.objects.create_user(username=username, organization="some place")

        self.client.force_login(user)

        data = {
            "organization": "wow",
            "bio": "changed bio",
            "username": "this field should be ignored",
        }

        r = self.client.put(f"/user_profile/{username}", data, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        user = User.objects.get(username=username)
        self.assertEqual(user.username, username)
        self.assertEqual(user.organization, data["organization"])
        self.assertEqual(user.bio, data["bio"])

        r = self.client.get(f"/user_profile/{username}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual({
            "username": username,
            "organization": user.organization,
            "department": user.department,
            "bio": user.bio,
        }, r.json())

    def testUserProfilePermissions(self):
        users = [
            User.objects.create_user(username="jed"),
            User.objects.create_user(username="mia"),
            User.objects.create_user(username="reina"),
        ]

        # check that all users require authorization
        for user in users:
            r = self.client.get(f"/user_profile/{user.username}")
            self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        # check that a user is only able to access their own profile
        for login_user in users:
            self.client.force_login(login_user)
            for user in users:
                r = self.client.get(f"/user_profile/{user.username}")
                self.assertEqual(r.status_code, status.HTTP_200_OK if user == login_user else status.HTTP_403_FORBIDDEN)
                r = self.client.get(f"/user_profile/{user.username}", {"bio": "changing bio"})
                self.assertEqual(r.status_code, status.HTTP_200_OK if user == login_user else status.HTTP_403_FORBIDDEN)


class TestAuth(TestCase):
    """
    TestAuth tests that our post Globus login, create user and logout flows work as expected.

    As a test boundary, we assume that the Globus login and callback works. Our starting point
    is oidc_auth_user_info session data has been the callback so we can perform any additional
    user creation and login.
    """

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
        # TODO figure out correct way to verify user is created with password login disabled. seems to be that it starts with !?
        self.assertTrue(user.password.startswith("!"))

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

    def testCompleteLoginWhenAlreadyLoggedIn(self):
        user = User.objects.create_user(username="someuser")
        self.client.force_login(user)

        r = self.client.get("/login/")
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, "/complete-login/")

        r = self.client.get(r.url)
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, settings.LOGIN_REDIRECT_URL)

        token = Token.objects.get(user=user)

        # check that response cookies match user info
        self.assertEqual(r.cookies["sage_uuid"].value, str(user.id))
        self.assertEqual(r.cookies["sage_username"].value, user.username)
        self.assertEqual(r.cookies["sage_token"].value, token.key)

    def testLoginRedirectToNext(self):
        # start login flow
        r = self.client.get("/login/?next=https://app-portal.org/")

        # assume redirect callback works and manually set user info session data
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

        # manually redirect to complete login, do valid login and then check redirect
        r = self.client.post("/complete-login/", {
            "username": "someuser",
            "confirm_username": "someuser",
        })
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, "https://app-portal.org/")
        self.assertTrue(r.wsgi_request.user.is_authenticated)

    def testLogoutNext(self):
        r = self.client.get("/logout/?next=https://portal.sagecontinuum.org")
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, "https://portal.sagecontinuum.org")

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


class TestAuthSettings(TestCase):
    """
    TestAuthSettings tests that all expected authentication methods are enabled.

    Note that we're using /token as an arbitrary authenticated endpoint to try auth methods on.
    """

    endpoint = "/token"

    def testEndpointRequiresAuth(self):
        r = self.client.get(self.endpoint)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def testBasicAuthEnabled(self):
        import base64
        user = User.objects.create_user(username="user", password="averygoodpassword")
        auth = base64.b64encode(b"user:averygoodpassword").decode()
        r = self.client.get(self.endpoint, HTTP_AUTHORIZATION=f"Basic {auth}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def testSessionAuthEnabled(self):
        user = User.objects.create_user(username="user")
        self.client.force_login(user)
        r = self.client.get(self.endpoint)
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def testTokenAuthEnabled(self):
        user = User.objects.create_user(username="user")
        token = Token.objects.create(user=user)
        self.client.force_login(user)
        r = self.client.get(self.endpoint, HTTP_AUTHORIZATION=f"Sage {token.key}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class TestPortalCompatibility(TestCase):
    """
    TestPortalCompatibility tests that all existing endpoints the portal depends on work as expected
    until we can migrate to the new endpoints.
    """

    def testLoginCallback(self):
        # TODO migrate portal to using /login/?next=...
        r = self.client.get("/?callback=https://my.site.org/")
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, "/login/?next=https://my.site.org/")

    def testLogoutCallback(self):
        # TODO migrate portal to using /logout/?next=...
        r = self.client.get("/portal-logout/?callback=https://portal.sagecontinuum.org")
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, "https://portal.sagecontinuum.org")
        self.assertEqual(r.cookies.get("sage_uuid").value, "")
        self.assertEqual(r.cookies.get("sage_username").value, "")
        self.assertEqual(r.cookies.get("sage_token").value, "")
