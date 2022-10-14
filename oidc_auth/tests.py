from uuid import uuid4
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from .models import Identity


User = get_user_model()

class TestOIDCAuth(TestCase):

    def testHandlerUserInfoScratch(self):
        user_info = generate_user_info()

        session = self.client.session
        session["oidc_auth_user_info"] = user_info
        session.save()

        r = self.client.get("/complete-login/")
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, "/create-user")
        self.assertFalse(r.wsgi_request.user.is_authenticated)

        identity = Identity.objects.get(sub=user_info["sub"])
        self.assertEqual(identity.name, user_info["name"])
        self.assertEqual(identity.email, user_info["email"])
        self.assertEqual(identity.preferred_username, user_info["preferred_username"])
        self.assertEqual(identity.organization, user_info["organization"])

    def testHandlerUserInfoExistingIdentity(self):
        user_info = generate_user_info()

        session = self.client.session
        session["oidc_auth_user_info"] = user_info
        session.save()

        Identity.objects.create(sub=user_info["sub"])
        
        r = self.client.get("/complete-login/")
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, "/create-user")
        self.assertFalse(r.wsgi_request.user.is_authenticated)

        identity = Identity.objects.get(sub=user_info["sub"])
        self.assertEqual(identity.name, user_info["name"])
        self.assertEqual(identity.email, user_info["email"])
        self.assertEqual(identity.preferred_username, user_info["preferred_username"])
        self.assertEqual(identity.organization, user_info["organization"])

    def testHandlerUserInfoExistingIdentityAndUser(self):
        user_info = generate_user_info()

        session = self.client.session
        session["oidc_auth_user_info"] = user_info
        session.save()

        Identity.objects.create(
            sub=user_info["sub"],
            user=User.objects.create(username="atestuser"),
        )

        r = self.client.get("/complete-login/")
        self.assertEqual(r.status_code, status.HTTP_302_FOUND)
        self.assertEqual(r.url, settings.LOGIN_REDIRECT_URL)
        self.assertTrue(r.wsgi_request.user.is_authenticated)

        identity = Identity.objects.get(sub=user_info["sub"])
        self.assertEqual(identity.name, user_info["name"])
        self.assertEqual(identity.email, user_info["email"])
        self.assertEqual(identity.preferred_username, user_info["preferred_username"])
        self.assertEqual(identity.organization, user_info["organization"])
        self.assertEqual(identity.user.username, "atestuser")
        self.assertEqual(r.wsgi_request.user, identity.user)

    def testHandlerUserInfoMissingUserInfo(self):
        r = self.client.get("/complete-login/")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(r.wsgi_request.user.is_authenticated)

    def testHandlerUserInfoMissingSub(self):
        session = self.client.session
        session["oidc_auth_user_info"] = {}
        session.save()

        r = self.client.get("/complete-login/")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(r.wsgi_request.user.is_authenticated)


def generate_user_info():
    return {
        "sub": str(uuid4()),
        "name": "Test User",
        "email": "test@test.com",
        "preferred_username": "testuser",
        "organization": "Test Organization",
    }
