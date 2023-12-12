from rest_framework import authentication
from app import get_user_token_keyword


class TokenAuthentication(authentication.TokenAuthentication):
    keyword = get_user_token_keyword()
