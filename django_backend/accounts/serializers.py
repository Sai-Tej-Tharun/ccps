from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .rbac import get_role, permissions_for

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "is_staff", "date_joined", "role", "permissions"]
        read_only_fields = fields

    def get_role(self, user):
        return get_role(user)

    def get_permissions(self, user):
        return sorted(permissions_for(user))


class RegisterSerializer(serializers.ModelSerializer):
    """
    Registers a user by email + password. Internally we store the email as
    Django's `username` too (kept equal to email) so the entire built-in
    auth/admin/permissions machinery works unmodified — callers only ever
    see `email`, never `username`.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        email = validated_data["email"]
        user = User(
            username=email,
            email=email,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        user.set_password(validated_data["password"])  # hashed via Django's PBKDF2 hasher
        user.save()
        return user
