"""
Creates (or updates) a single demo superuser for evaluation purposes, from
DEMO_ADMIN_USERNAME / DEMO_ADMIN_EMAIL / DEMO_ADMIN_PASSWORD in settings
(sourced from environment variables — see .env.example).

Usage:  python manage.py create_demo_admin

This is intentionally idempotent (safe to run every container start) and
intentionally loud about the password being a demo credential — swap it
before using this project as anything beyond a local evaluation.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Creates or updates the demo admin superuser used for evaluation."

    def handle(self, *args, **options):
        username = settings.DEMO_ADMIN_USERNAME
        email = settings.DEMO_ADMIN_EMAIL
        password = settings.DEMO_ADMIN_PASSWORD

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} demo admin '{username}' <{email}>."))
        self.stdout.write(
            self.style.WARNING(
                "This is a demo credential for local evaluation only — "
                "change DEMO_ADMIN_PASSWORD before using this anywhere else."
            )
        )
