"""
Used django.contrib.auth.base_user as a Template

This module allows importing AbstractBaseNode even when django.contrib.auth is
not in INSTALLED_APPS.
"""
import unicodedata
from django.conf import settings
# from django.contrib.auth import password_validation #TODO: delete once you know its not used
# from django.contrib.auth.hashers import (
#     acheck_password, #TODO: delete once you know its not used
#     check_password, #TODO: delete once you know its not used
#     is_password_usable, #TODO: delete once you know its not used
#     make_password, #TODO: delete once you know its not used
# )
from django.db import models
from django.utils.crypto import salted_hmac
from django.utils.translation import gettext_lazy as _

class AbstractBaseNode(models.Model): #old class name = AbstractBaseUser
    #password = models.CharField(_("password"), max_length=128) #TODO: delete once you know its not used
    last_login = models.DateTimeField(_("last login"), blank=True, null=True)

    is_active = True
    REQUIRED_FIELDS = ["vsn"]

    # Stores the raw password if set_password() is called so that it can
    # be passed to password_changed() after the model is saved.
    #_password = None #TODO: delete once you know its not used

    class Meta:
        abstract = True

    def __str__(self):
        return self.get_vsn()

    # def save(self, *args, **kwargs): #TODO: delete once you know its not used
    #     super().save(*args, **kwargs)
    #     if self._password is not None: 
    #         password_validation.password_changed(self._password, self)
    #         self._password = None

    def get_vsn(self): #old function name = get_username
        """Return the vsn for this Node."""
        return getattr(self, self.VSN_FIELD) # old second parameter = self.USERNAME_FIELD

    def clean(self):
        setattr(self, self.VSN_FIELD, self.normalize_vsn(self.get_vsn())) # old = setattr(self, self.USERNAME_FIELD, self.normalize_username(self.get_username()))

    def natural_key(self):
        return (self.get_vsn(),) # old = return (self.get_username(),)

    @property
    def is_anonymous(self):
        """
        Always return False. This is a way of comparing Node objects to
        anonymous nodes.
        """
        return False

    @property
    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the node has been
        authenticated in templates.
        """
        return True

    # def set_password(self, raw_password): #TODO: delete once you know its not used
    #     self.password = make_password(raw_password)
    #     self._password = raw_password

    # def check_password(self, raw_password): #TODO: delete once you know its not used
    #     """
    #     Return a boolean of whether the raw_password was correct. Handles
    #     hashing formats behind the scenes.
    #     """

    #     def setter(raw_password):
    #         self.set_password(raw_password)
    #         # Password hash upgrades shouldn't be considered password changes.
    #         self._password = None
    #         self.save(update_fields=["password"])

    #     return check_password(raw_password, self.password, setter)

    # async def acheck_password(self, raw_password): #TODO: delete once you know its not used
    #     """See check_password()."""

    #     async def setter(raw_password):
    #         self.set_password(raw_password)
    #         # Password hash upgrades shouldn't be considered password changes.
    #         self._password = None
    #         await self.asave(update_fields=["password"])

    #     return await acheck_password(raw_password, self.password, setter)

    # def set_unusable_password(self): #TODO: delete once you know its not used
    #     # Set a value that will never be a valid hash
    #     self.password = make_password(None)

    # def has_usable_password(self): #TODO: delete once you know its not used
    #     """
    #     Return False if set_unusable_password() has been called for this node.
    #     """
    #     return is_password_usable(self.password)

    def get_session_auth_hash(self):
        """
        Return an HMAC of the password field.
        """
        return self._get_session_auth_hash()

    def get_session_auth_fallback_hash(self):
        for fallback_secret in settings.SECRET_KEY_FALLBACKS:
            yield self._get_session_auth_hash(secret=fallback_secret)

    def _get_session_auth_hash(self, secret=None):
        key_salt = "node_auth.contrib.auth.models.AbstractBaseNode.get_session_auth_hash" # old val = "django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"
        return salted_hmac(
            key_salt,
            #self.password, #TODO: delete once you know its not used
            secret=secret,
            algorithm="sha256",
        ).hexdigest()

    #TODO: delete once you know its not used
    # @classmethod
    # def get_email_field_name(cls):
    #     try:
    #         return cls.EMAIL_FIELD
    #     except AttributeError:
    #         return "email"

    @classmethod
    def normalize_vsn(cls, vsn): #old func name = normalize_username(cls, username)
        return (
            unicodedata.normalize("NFKC", vsn)
            if isinstance(vsn, str)
            else vsn
        )