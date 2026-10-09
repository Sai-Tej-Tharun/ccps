"""
Role administration (Admin only).

GET /api/adminpanel/roles/              role -> permission matrix
GET /api/adminpanel/staff-users/        users that hold a role (?search=); add &all=true to search every user
PUT /api/adminpanel/users/<id>/role/    body {"role": "SUPPORT"}  (or "NONE" to remove)
"""

from django.contrib.auth import get_user_model
from django.db import transaction as db_transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserRole
from accounts.permissions import require
from accounts.rbac import ROLE_PERMISSIONS, Perm, Role, get_role

from .audit import log_admin_action

User = get_user_model()


class StaffUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "is_active", "role"]
        read_only_fields = fields

    def get_role(self, user):
        return get_role(user)


class RoleAssignmentSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[*Role.ALL, "NONE"])


class RoleMatrixView(APIView):
    permission_classes = [require(Perm.ROLES_MANAGE)]

    def get(self, request):
        return Response({role: sorted(perms) for role, perms in ROLE_PERMISSIONS.items()})


class StaffUserListView(ListAPIView):
    permission_classes = [require(Perm.ROLES_MANAGE)]
    serializer_class = StaffUserSerializer

    def get_queryset(self):
        params = self.request.query_params
        search = params.get("search", "").strip()[:100]
        if params.get("all") == "true":
            # Look up ANY user (to promote a customer); needs at least 3 characters so it can't dump the table.
            if len(search) < 3:
                return User.objects.none()
            qs = User.objects.all()
        else:
            qs = User.objects.filter(Q(is_staff=True) | Q(role_assignment__isnull=False)).distinct()
        if search:
            qs = qs.filter(Q(email__icontains=search) | Q(first_name__icontains=search))
        return qs.order_by("email")


class UserRoleView(APIView):
    permission_classes = [require(Perm.ROLES_MANAGE)]

    def put(self, request, pk):
        serializer = RoleAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_role = serializer.validated_data["role"]

        if pk == request.user.pk:
            return Response({"detail": "You cannot change your own role."}, status=400)

        with db_transaction.atomic():
            target = get_object_or_404(User.objects.select_for_update(), pk=pk)
            old_role = get_role(target)
            if new_role == "NONE":
                UserRole.objects.filter(user=target).delete()
                # A legacy staff account has no role row; clear the flag so it really loses access.
                User.objects.filter(pk=target.pk, is_superuser=False).update(is_staff=False)
            else:
                UserRole.objects.update_or_create(
                    user=target, defaults={"role": new_role, "assigned_by": request.user}
                )
            log_admin_action(
                request,
                "Changed user role",
                target_type="user",
                target_id=target.pk,
                changes={"role": {"old": old_role, "new": None if new_role == "NONE" else new_role}},
                details=f"user_id={target.pk}, email={target.email}",
            )
        target.refresh_from_db()
        return Response(StaffUserSerializer(target).data)