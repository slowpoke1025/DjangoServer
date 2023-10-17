from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# request.auth.payload
def create_jwt(user, payload):
    refresh = RefreshToken.for_user(user)
    refresh.payload.update(payload)
    tokens = {"access": str(refresh.access_token), "refresh": str(refresh)}

    return tokens


# JSON.parse(decodeURIComponent(escape(window.atob(token.split('.')[1])))) # js decode payload
