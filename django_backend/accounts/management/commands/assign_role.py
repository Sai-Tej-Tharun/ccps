"""
Usage:
    python manage.py assign_role jane@example.com SUPPORT
    python manage.py assign_role jane@example.com NONE      (back to a normal customer)
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.models import UserRole
from accounts.rbac import Role

User = get_user_model()


class Command(BaseCommand):
    help = "Assign ADMIN, SUPPORT or READ_ONLY to a user (or NONE to remove the role)."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("role", choices=[*Role.ALL, "NONE"])

    def handle(self, *args, **options):
        try:
            user = User.objects.get(email__iexact=options["email"])
        except User.DoesNotExist:
            raise CommandError("No user with that e-mail address.")

        if options["role"] == "NONE":
            UserRole.objects.filter(user=user).delete()
            self.stdout.write(self.style.SUCCESS(f"{user.email} is now a regular customer."))
            return

        UserRole.objects.update_or_create(user=user, defaults={"role": options["role"]})
        self.stdout.write(self.style.SUCCESS(f"{user.email} is now {options['role']}."))