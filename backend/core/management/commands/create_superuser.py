"""
Management command to create a superuser non-interactively.
Used for initial setup in Cloud Run deployments.
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser if none exists, using environment variables'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Superuser username')
        parser.add_argument('--email', type=str, help='Superuser email')
        parser.add_argument('--password', type=str, help='Superuser password')

    def handle(self, *args, **options):
        username = options.get('username') or os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = options.get('email') or os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = options.get('password') or os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not password:
            self.stderr.write(self.style.ERROR(
                'Password required. Set DJANGO_SUPERUSER_PASSWORD env var or use --password'
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists. Skipping.'))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            display_name='Admin',
            is_approved=True,
            phone_verified=True,
            email_verified=True,
        )
        self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully!'))
