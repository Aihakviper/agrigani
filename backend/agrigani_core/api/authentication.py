"""Minimal JWT authentication for AgriGani API."""

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions


class JWTAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).decode("utf-8")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            raise exceptions.AuthenticationFailed("Invalid authorization header")

        try:
            payload = jwt.decode(parts[1], settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError as exc:
            raise exceptions.AuthenticationFailed("Token has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise exceptions.AuthenticationFailed("Invalid token") from exc

        user = get_user_model().objects.filter(id=payload.get("user_id"), is_active=True).first()
        if not user:
            raise exceptions.AuthenticationFailed("User not found")

        return user, payload
