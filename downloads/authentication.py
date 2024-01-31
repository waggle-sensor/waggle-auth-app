from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework import exceptions


# BasicTokenPasswordAuthentication allows a user's token to be used as their password during HTTP Basic Auth.
#
# Before using this, you MUST read the VERY IMPORTANT security note below:
#
# This authenticators MUST only be used for the downloads view and NEVER as a default authenticator. Tokens are
# intended to be scoped to specific views and not intended to grant a full user session. In the case a token is
# leaked, that would essentially allow someone to hijack and entire user's account.
class BasicTokenPasswordAuthentication(BasicAuthentication):
    def authenticate_credentials(self, userid, password, request=None):
        user, auth = TokenAuthentication().authenticate_credentials(password)
        if user.username != userid:
            raise exceptions.AuthenticationFailed("username does not match token user")
        return user, auth
