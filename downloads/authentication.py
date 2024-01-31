from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework import exceptions


# BasicTokenPasswordAuthentication allows a user's token to be used as their password during HTTP Basic Auth.
#
# Before using this, you MUST read the VERY IMPORTANT security note below:
#
# This authenticators MUST only be used for the downloads view and NEVER as a default authenticator. Tokens are
# intended to be scoped to specific views and not intended to grant a full user session. In the case a token is
# leaked, that would essentially allow someone to hijack and entire user's account.
#
# Some context on why this is here:
#
# This was added because the way wget forwards Authentication headers is incompatible with S3. Specifically,
# after getting the presigned URL, wget forwards the header to S3, unlike curl or Python's requests which
# drop it for security purposes. Once S3 receives this header, it returns 400 Bad Request...
#
# By sheer luck, the way wget handles HTTP Basic Auth is to hit the endpoint and only sends auth if if a
# WWW-Authenticate header is returned. This means, the presigned URL works!
#
# It also happens to be compatible to examples we showed users in our docs before, which is a nice side effect.
class BasicTokenPasswordAuthentication(BasicAuthentication):
    def authenticate_credentials(self, userid, password, request=None):
        user, auth = TokenAuthentication().authenticate_credentials(password)
        if user.username != userid:
            raise exceptions.AuthenticationFailed("username does not match token user")
        return user, auth
