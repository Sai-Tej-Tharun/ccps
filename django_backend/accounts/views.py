from django.contrib.auth import get_user_model
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(APIView):
    """POST /api/auth/register/ — create an account. Publicly accessible."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    The client sends `email`; internally it's copied into Django's actual
    USERNAME_FIELD ("username" on the default User model) before calling
    authenticate(), since registration stores username == email (see
    RegisterSerializer). Deliberately does NOT override `username_field`
    itself — that attribute is what ModelBackend.authenticate() keys off
    of, and it must stay "username" to match the real User model; only
    the client-facing schema changes here.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"] = serializers.EmailField()
        self.fields.pop("username", None)  # clients send `email`, never `username`

    def validate(self, attrs):
        attrs["username"] = self.initial_data.get("email", "")
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["is_staff"] = user.is_staff
        return token


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — body: {"email": "...", "password": "..."}."""

    permission_classes = [AllowAny]
    serializer_class = EmailTokenObtainPairSerializer


class LogoutView(APIView):
    """
    POST /api/auth/logout/ — body: {"refresh": "..."}.
    Blacklists the refresh token so it can no longer be used to mint new
    access tokens. The (already short-lived) access token itself remains
    valid until it naturally expires, same as any standard JWT logout.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Token is invalid or already blacklisted."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    """GET /api/auth/me/ — the authenticated user's own profile. Protected route example."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
