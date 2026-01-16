from django.test import TestCase, override_settings
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import status
import uuid
from .models import Project, Node, UserMembership, NodeMembership
from test_utils import assertDictContainsSubset
import pytest

User = get_user_model()

# TODO(sean) refactor and clean up some of the tests. these work but are a little repetitive


class TestHomeView(TestCase):
    """
    TestHomeView tests that the home page renders its templates without error for anonymous, regular and admin users.
    """

    def testAsAnon(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertContains(r, "Log in")
        self.assertNotContains(r, "Log out")
        self.assertNotContains(r, "View admin site")

    def testAsUser(self):
        user = create_random_user()
        self.client.force_login(user)
        r = self.client.get("/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertNotContains(r, "Log in")
        self.assertContains(r, "Log out")
        self.assertNotContains(r, "View admin site")

    def testAsAdmin(self):
        user = create_random_admin_user()
        self.client.force_login(user)
        r = self.client.get("/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertNotContains(r, "Log in")
        self.assertContains(r, "Log out")
        self.assertContains(r, "View admin site")


class TestNodeUsersView(TestCase):
    """
    TestNodeUsersView tests that the update ssh public keys renders.
    """

    def testResponse(self):
        project = Project.objects.create(name="Test")

        node = Node.objects.create(vsn="W123")
        NodeMembership.objects.create(project=project, node=node, can_develop=True)

        # create user with dev access to this node
        user = User.objects.create(
            username="someuser",
            ssh_public_keys="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN0QZW4toqXPDOKToSeSpaax2ISgzlEA+C0ANphhbHAk",
        )
        UserMembership.objects.create(project=project, user=user, can_develop=True)

        # create user without dev access to this node
        User.objects.create_user(
            username="anotheruser",
            ssh_public_keys="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN0QZW4toqXPDOKToSeSpaax2ISgzlEA+C0ANphhZAZA",
        )

        r = self.client.get("/nodes/W123/users")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(
            r.json(),
            [
                {
                    "user": "someuser",
                    "ssh_public_keys": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN0QZW4toqXPDOKToSeSpaax2ISgzlEA+C0ANphhbHAk\n",
                }
            ],
        )


class TestUpdateSSHPublicKeysView(TestCase):
    """
    TestUpdateSSHPublicKeysView tests that the update ssh public keys renders.
    """

    def testLoginRequired(self):
        r = self.client.get("/update-my-keys")
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, f"{settings.LOGIN_URL}?next=/update-my-keys")


class TestTokenView(TestCase):
    """
    TestTokenView tests that tokens can be gotten and automatically created if they don't exist.
    """

    def testNeedsAuth(self):
        r = self.client.get("/token")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        r = self.client.delete("/token")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def testGetTokenExists(self):
        user = create_random_user()
        token = Token.objects.create(user=user)
        self.client.force_login(user)

        r = self.client.get("/token")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertDictEqual({"token": token.key, "user_uuid": str(user.id)}, r.json())

    def testGetTokenNotExists(self):
        user = create_random_user()
        self.client.force_login(user)

        r = self.client.get("/token")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        token = Token.objects.get(user=user)
        self.assertDictEqual({"token": token.key, "user_uuid": str(user.id)}, r.json())

    def testRefreshToken(self):
        user = create_random_user()
        self.client.force_login(user)

        r = self.client.get("/token")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        token1 = r.json()["token"]

        r = self.client.delete("/token")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        r = self.client.get("/token")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        token2 = r.json()["token"]

        self.assertNotEqual(token1, token2)

    def testRefreshTokenOnlyAffectsSelf(self):
        user1 = create_random_user()
        user2 = create_random_user()

        # user 1 creates token
        self.client.force_login(user1)
        r = self.client.get("/token")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        token1 = r.json()["token"]

        # user 2 creates token
        self.client.force_login(user2)
        r = self.client.get("/token")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        token2 = r.json()["token"]

        # user 1 refreshes token
        self.client.force_login(user1)
        r = self.client.delete("/token")

        # user 1 should have new token
        self.client.force_login(user1)
        r = self.client.get("/token")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertNotEqual(token1, r.json()["token"])

        # user 2 should have same token
        self.client.force_login(user2)
        r = self.client.get("/token")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(token2, r.json()["token"])


class TestTokenInfoView(TestCase):
    """
    TestTokenInfoView tests that token info is provided correctly

    TODO Simplify this a lot. Auth isn't *really* required, as if you have a real token,
    then you can just authenticate as that user and view their token info.
    """

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
        def post_json(data):
            return self.client.post(
                "/token_info/", data, content_type="application/json"
            )

        # endpoint should deny unauthorized request
        r = post_json({"token": token.key})
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

        # logging in should allow access
        self.client.force_login(admin)

        # should show token info
        r = post_json({"token": token.key})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            {
                "active": True,
                "scope": "default",
                "client_id": "some-client-id",
                "username": user.username,
                "exp": 0,
            },
            r.json(),
        )

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
    def setUp(self):
        self.admin = create_random_admin_user()
        self.users = [create_random_user() for _ in range(3)] + [self.admin]
        self.url = "/users/"

    def testGetAsAnon(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def testGetAsAdmin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.json()), len(self.users))
        # TODO actually check the content

    def testGetAsUser(self):
        self.client.force_login(create_random_user())
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


class TestUserDetailView(TestCase):
    def setUp(self):
        self.user = create_random_user()
        self.url = f"/users/{self.user.username}"
        self.want = {
            "username": self.user.username,
            "name": self.user.name,
        }

    def testGetAsAnon(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def testGetAsAdmin(self):
        self.client.force_login(create_random_admin_user())
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        assertDictContainsSubset(self.want, r.json())

    def testGetAsSelf(self):
        self.client.force_login(self.user)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        assertDictContainsSubset(self.want, r.json())

    def testGetAsOther(self):
        self.client.force_login(create_random_user())
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


class TestUserSelfDetailView(TestCase):
    def testGetAsAnon(self):
        r = self.client.get("/users/~self")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def testGetAsUser(self):
        user = create_random_user()
        self.client.force_login(user)
        r = self.client.get("/users/~self")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        assertDictContainsSubset(
            {
                "username": user.username,
                "name": user.name,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "is_approved": user.is_approved,
            },
            r.json(),
        )


class TestUserProfileView(TestCase):
    """
    TestUserProfile tests user profile permissions, get and update behavior.
    """

    def setUp(self):
        self.user = create_random_user()
        self.url = f"/user_profile/{self.user.username}"
        self.want = {
            "username": self.user.username,
            "organization": self.user.organization,
            "department": self.user.department,
            "bio": self.user.bio,
            "ssh_public_keys": "",
        }

    def testGetAsAnon(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def testGetAsAdmin(self):
        self.client.force_login(create_random_admin_user())
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        assertDictContainsSubset(self.want, r.json())

    def testGetAsSelf(self):
        self.client.force_login(self.user)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        assertDictContainsSubset(self.want, r.json())

    def testGetAsOther(self):
        self.client.force_login(create_random_user())
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def testUserProfileUpdate(self):
        # TODO(sean) what's the right way to test this pattern
        self.client.force_login(self.user)

        data = {
            "organization": "wow",
            "bio": "changed bio",
            "username": "this field should be ignored",
            "ssh_public_keys": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK0LT3jNyfUtkJwxiv/7YfPU4PIOsQzeCVKlLCAfwlg3\n",
        }

        r = self.client.put(self.url, data, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        user = User.objects.get(username=self.user.username)
        self.assertEqual(user.organization, data["organization"])
        self.assertEqual(user.bio, data["bio"])

        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {
                "username": self.user.username,
                "organization": user.organization,
                "department": user.department,
                "bio": user.bio,
                "ssh_public_keys": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK0LT3jNyfUtkJwxiv/7YfPU4PIOsQzeCVKlLCAfwlg3",
            },
            r.json(),
        )


class TestAccessView(TestCase):
    def setUp(self):
        profile_membership = [
            ("ada", "sage", {"can_develop": True}),
            ("ada", "dawn", {"can_develop": True, "can_schedule": True}),
            ("jed", "sage", {"can_schedule": True, "can_develop": True}),
            ("tom", "sage", {"can_develop": True, "can_schedule": True}),
            (
                "tom",
                "dawn",
                {"can_develop": True, "can_schedule": True},
            ),
            ("notapproved", "sage", {"can_develop": True, "can_schedule": True}),
            (
                "notapproved",
                "dawn",
                {"can_develop": True, "can_schedule": True},
            ),
        ]

        node_membership = [
            ("sage", "W000", {}),
            ("sage", "W001", {"can_schedule": True}),
            ("sage", "W002", {"can_develop": True}),
            ("sage", "W003", {"can_schedule": True, "can_develop": True}),
            ("dawn", "W000", {}),
            (
                "dawn",
                "W001",
                {"can_schedule": True, "can_develop": True},
            ),
        ]

        # create all user memberships
        for username, projectname, access in profile_membership:
            user, _ = User.objects.get_or_create(username=username)
            project, _ = Project.objects.get_or_create(name=projectname)
            UserMembership.objects.get_or_create(user=user, project=project, **access)

        # create all project memberships
        for projectname, vsn, access in node_membership:
            node, _ = Node.objects.get_or_create(vsn=vsn)
            project, _ = Project.objects.get_or_create(name=projectname)
            NodeMembership.objects.get_or_create(node=node, project=project, **access)

        # approve some of our users
        for username in ["ada", "jed", "tom"]:
            user = User.objects.get(username=username)
            user.is_approved = True
            user.save()

    def testAnonymousNotAllowed(self):
        for username in ["ada", "jed", "tom"]:
            r = self.client.get(f"/users/{username}/access")
            self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def testSelfAllowed(self):
        for username in ["ada", "jed", "tom"]:
            self.client.force_login(User.objects.get(username=username))
            r = self.client.get(f"/users/{username}/access")
            self.assertEqual(r.status_code, status.HTTP_200_OK)

    def testOtherNotAllowed(self):
        self.client.force_login(User.objects.get(username="ada"))

        for username in ["jed", "tom"]:
            r = self.client.get(f"/users/{username}/access")
            self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def testAdminAllowed(self):
        self.client.force_login(create_random_admin_user())

        for username in ["ada", "jed", "tom"]:
            r = self.client.get(f"/users/{username}/access")
            self.assertEqual(r.status_code, status.HTTP_200_OK)

    def testAccessNotExist(self):
        self.client.force_login(create_random_admin_user())
        r = self.client.get("/profiles/nothere/access")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def testListUserAccess(self):
        self.client.force_login(create_random_admin_user())

        # check responses
        r = self.client.get("/users/ada/access")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(
            r.json(),
            [
                {"vsn": "W001", "access": ["develop", "schedule"]},
                {"vsn": "W002", "access": ["develop"]},
                {"vsn": "W003", "access": ["develop"]},
            ],
        )

        r = self.client.get("/users/jed/access")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(
            r.json(),
            [
                {"vsn": "W001", "access": ["schedule"]},
                {"vsn": "W002", "access": ["develop"]},
                {"vsn": "W003", "access": ["develop", "schedule"]},
            ],
        )

        r = self.client.get("/users/tom/access")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(
            r.json(),
            [
                {"vsn": "W001", "access": ["develop", "schedule"]},
                {"vsn": "W002", "access": ["develop"]},
                {"vsn": "W003", "access": ["develop", "schedule"]},
            ],
        )

        r = self.client.get("/users/notapproved/access")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json(), [])

    def testProfilesListProfileAccess(self):
        # regression test to make sure /profiles/ is backwards compatible with schedule auth requirements. (deprecate this!)
        r = self.client.get("/profiles/ada/access")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(
            r.json(),
            [
                {"vsn": "W001", "access": ["develop", "schedule"]},
                {"vsn": "W002", "access": ["develop"]},
                {"vsn": "W003", "access": ["develop"]},
            ],
        )

        r = self.client.get("/profiles/jed/access")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(
            r.json(),
            [
                {"vsn": "W001", "access": ["schedule"]},
                {"vsn": "W002", "access": ["develop"]},
                {"vsn": "W003", "access": ["develop", "schedule"]},
            ],
        )

        r = self.client.get("/profiles/tom/access")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(
            r.json(),
            [
                {"vsn": "W001", "access": ["develop", "schedule"]},
                {"vsn": "W002", "access": ["develop"]},
                {"vsn": "W003", "access": ["develop", "schedule"]},
            ],
        )

        r = self.client.get("/profiles/notapproved/access")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.json(), [])

    def testProfilesAccessNotExist(self):
        # regression test to make sure /profiles/ is backwards compatible with schedule auth requirements. (deprecate this!)
        r = self.client.get("/profiles/nothere/access")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

@pytest.mark.skip(reason="disable when using allauth")
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
        r = self.client.post(
            "/complete-login/",
            {
                "username": "someuser",
                "confirm_username": "nomatch",
            },
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertFalse(r.wsgi_request.user.is_authenticated)

        # upon successfully logging, we should be logged in as our user with
        # fields initially populated from the oidc data
        r = self.client.post(
            "/complete-login/",
            {
                "username": "someuser",
                "confirm_username": "someuser",
            },
        )
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

        # logging out must tell client to delete user cookies and performs globus logout flow
        r = self.client.post("/logout/")
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            r.url,
            "https://auth.globus.org/v2/web/logout?redirect_uri=http://testserver/",
        )
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
        self.assertEqual(r.cookies["sage_uuid"].get("samesite"), "Strict")
        self.assertEqual(r.cookies["sage_username"].value, user.username)
        self.assertEqual(r.cookies["sage_username"].get("samesite"), "Strict")
        self.assertEqual(r.cookies["sage_token"].value, token.key)
        self.assertEqual(r.cookies["sage_token"].get("samesite"), "Strict")

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
        r = self.client.post(
            "/complete-login/",
            {
                "username": "someuser",
                "confirm_username": "someuser",
            },
        )
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, "https://app-portal.org/")
        self.assertTrue(r.wsgi_request.user.is_authenticated)

    @override_settings(SUCCESS_URL_ALLOWED_HOSTS=["portal.sagecontinuum.org"])
    def testLogoutNext(self):
        r = self.client.get("/logout/?next=https://portal.sagecontinuum.org")
        self.assertEqual(r.cookies.get("sage_uuid").value, "")
        self.assertEqual(r.cookies.get("sage_username").value, "")
        self.assertEqual(r.cookies.get("sage_token").value, "")
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            r.url,
            "https://auth.globus.org/v2/web/logout?redirect_uri=https://portal.sagecontinuum.org",
        )

    # TODO(sean) fix /admin/ redirect
    # def testAdminLoginRedirect(self):
    #     r = self.client.get("/admin/")
    #     self.assertEqual(r.status_code, status.HTTP_302_FOUND)
    #     self.assertEqual(r.url, "/login/")

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
        self.client.force_login(create_random_user())
        r = self.client.get(self.endpoint)
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def testTokenAuthEnabled(self):
        token = Token.objects.create(user=create_random_user())
        r = self.client.get(self.endpoint, HTTP_AUTHORIZATION=f"Sage {token.key}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)


class TestNodeAuthorizedKeysView(TestCase):
    def setUp(self):
        allowed = create_random_user()
        allowed.ssh_public_keys = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIDpsV/R93C5TfTO2kXdjOxwXNLbsowpztcUnkLH9T/4\n"
        allowed.save()

        member = create_random_user()
        member.ssh_public_keys = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF8DWBuwUiNbw1OzPWQCmSQFvwVRdU29joY4YKkzvljV\n"
        member.save()

        not_allowed = create_random_user()
        not_allowed.ssh_public_keys = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINjaz/l4due6Z+WzbV/YyjO8RVKuO7ThTa19QvcLfgif\n"
        not_allowed.save()

        project = Project.objects.create(name="DEV")

        node = Node.objects.create(vsn="W123")

        UserMembership.objects.create(user=allowed, project=project, can_develop=True)
        UserMembership.objects.create(user=member, project=project, can_develop=False)
        NodeMembership.objects.create(project=project, node=node, can_develop=True)

    def testAnonymousNotAllowed(self):
        r = self.client.get("/nodes/W123/authorized_keys")
        text = r.content.decode()

        self.assertCountEqual(
            text.splitlines(),
            [
                "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIDpsV/R93C5TfTO2kXdjOxwXNLbsowpztcUnkLH9T/4",
            ],
        )


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

    @override_settings(SUCCESS_URL_ALLOWED_HOSTS=["portal.sagecontinuum.org"])
    def testLogoutCallback(self):
        # TODO migrate portal to using /logout/?next=...
        r = self.client.get("/portal-logout/?callback=https://portal.sagecontinuum.org")
        self.assertEqual(r.cookies.get("sage_uuid").value, "")
        self.assertEqual(r.cookies.get("sage_username").value, "")
        self.assertEqual(r.cookies.get("sage_token").value, "")
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            r.url,
            "https://auth.globus.org/v2/web/logout?redirect_uri=https://portal.sagecontinuum.org",
        )

    @override_settings(SUCCESS_URL_ALLOWED_HOSTS=["portal.sagecontinuum.org"])
    def testLogoutCallbackAllowedHosts(self):
        r = self.client.get("/logout/?next=https://danger.org")
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        # note that the non-allowed next url is ignored and we should be redirected to http://testserver/
        self.assertEqual(
            r.url,
            "https://auth.globus.org/v2/web/logout?redirect_uri=http://testserver/",
        )


def create_random_user(**kwargs) -> User:
    from random import choice, randint
    from string import ascii_letters, printable

    return User.objects.create_user(
        username="".join(choice(ascii_letters) for _ in range(randint(43, 64))),
        name="".join(choice(printable) for _ in range(randint(4, 24))),
        **kwargs,
    )


def create_random_admin_user(**kwargs):
    return create_random_user(is_staff=True, is_superuser=True, **kwargs)
