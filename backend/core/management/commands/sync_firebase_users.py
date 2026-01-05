"""
Management command to sync Firebase users with Django backend
Useful for recovering from registration failures where user exists in Firebase but not Django
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, PlayerProfile
from core.services import FirebaseService
from rest_framework.authtoken.models import Token
import firebase_admin.auth as firebase_auth


class Command(BaseCommand):
    help = 'Sync Firebase users with Django backend and fix any mismatched accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Sync a specific user by email'
        )
        parser.add_argument(
            '--phone',
            type=str,
            help='Sync a specific user by phone number'
        )
        parser.add_argument(
            '--uid',
            type=str,
            help='Sync a specific user by Firebase UID'
        )
        parser.add_argument(
            '--auto-create',
            action='store_true',
            help='Automatically create Django users for Firebase users that don\'t exist'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        if not FirebaseService.initialize():
            self.stdout.write(self.style.ERROR('Firebase not configured. Cannot sync users.'))
            return

        email = options.get('email')
        phone = options.get('phone')
        uid = options.get('uid')
        auto_create = options.get('auto_create')
        dry_run = options.get('dry_run')

        if email or phone or uid:
            # Sync specific user
            self.sync_single_user(email, phone, uid, auto_create, dry_run)
        else:
            # Sync all Firebase users
            self.sync_all_users(auto_create, dry_run)

    def sync_single_user(self, email, phone, uid, auto_create, dry_run):
        """Sync a single user from Firebase to Django"""
        firebase_user = None
        
        try:
            if uid:
                firebase_user = firebase_auth.get_user(uid)
            elif email:
                firebase_user = firebase_auth.get_user_by_email(email)
            elif phone:
                firebase_user = firebase_auth.get_user_by_phone_number(phone)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Firebase user not found: {e}'))
            return

        if not firebase_user:
            self.stdout.write(self.style.ERROR('No Firebase user found with given criteria'))
            return

        self.stdout.write(f'Found Firebase user: {firebase_user.email or firebase_user.phone_number} (UID: {firebase_user.uid})')
        
        # Check if Django user exists
        django_user = None
        
        # Try to find by Firebase UID
        if firebase_user.uid:
            django_user = User.objects.filter(firebase_uid=firebase_user.uid).first()
        
        # Try to find by email
        if not django_user and firebase_user.email:
            django_user = User.objects.filter(email=firebase_user.email).first()
        
        # Try to find by phone
        if not django_user and firebase_user.phone_number:
            django_user = User.objects.filter(phone_number=firebase_user.phone_number).first()

        if django_user:
            self.stdout.write(self.style.SUCCESS(f'Found existing Django user: {django_user.username}'))
            
            if not dry_run:
                # Update Django user with Firebase info
                updated = False
                if not django_user.firebase_uid:
                    django_user.firebase_uid = firebase_user.uid
                    updated = True
                    self.stdout.write('  - Linked Firebase UID')
                
                if firebase_user.email and not django_user.email:
                    django_user.email = firebase_user.email
                    updated = True
                    self.stdout.write(f'  - Set email: {firebase_user.email}')
                
                if firebase_user.phone_number and not django_user.phone_number:
                    django_user.phone_number = firebase_user.phone_number
                    updated = True
                    self.stdout.write(f'  - Set phone: {firebase_user.phone_number}')
                
                if firebase_user.email_verified and not django_user.email_verified:
                    django_user.email_verified = True
                    updated = True
                    self.stdout.write('  - Marked email as verified')
                
                if firebase_user.phone_number and not django_user.phone_verified:
                    django_user.phone_verified = True
                    updated = True
                    self.stdout.write('  - Marked phone as verified')
                
                # Auto-approve verified users
                if not django_user.is_approved and (django_user.email_verified or django_user.phone_verified):
                    django_user.is_approved = True
                    django_user.approved_at = timezone.now()
                    updated = True
                    self.stdout.write('  - Auto-approved user')
                
                if updated:
                    django_user.save()
                    self.stdout.write(self.style.SUCCESS('  - User updated successfully'))
                else:
                    self.stdout.write('  - User already in sync')
                
                # Ensure token exists
                Token.objects.get_or_create(user=django_user)
                
                # Ensure player profile exists
                PlayerProfile.objects.get_or_create(user=django_user)
            else:
                self.stdout.write(self.style.WARNING('[DRY RUN] Would update user'))

        elif auto_create:
            self.stdout.write(self.style.WARNING('Django user not found'))
            
            if not dry_run:
                # Create new Django user from Firebase user
                username = None
                if firebase_user.email:
                    username = firebase_user.email.split('@')[0]
                elif firebase_user.phone_number:
                    username = f'user_{firebase_user.phone_number[-4:]}'
                else:
                    username = f'firebase_{firebase_user.uid[:8]}'
                
                # Ensure unique username
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f'{base_username}{counter}'
                    counter += 1
                
                user_data = {
                    'username': username,
                    'display_name': firebase_user.display_name or username,
                    'email': firebase_user.email or '',
                    'phone_number': firebase_user.phone_number or '',
                    'firebase_uid': firebase_user.uid,
                    'email_verified': firebase_user.email_verified if firebase_user.email else False,
                    'phone_verified': True if firebase_user.phone_number else False,
                    'is_approved': True,  # Auto-approve Firebase verified users
                    'approved_at': timezone.now(),
                    'verification_method': 'email' if firebase_user.email else 'phone'
                }
                
                user = User.objects.create(**user_data)
                # Set a random password since they'll auth through Firebase
                user.set_unusable_password()
                user.save()
                
                # Create token and profile
                Token.objects.create(user=user)
                PlayerProfile.objects.create(user=user)
                
                self.stdout.write(self.style.SUCCESS(f'Created new Django user: {user.username}'))
            else:
                self.stdout.write(self.style.WARNING('[DRY RUN] Would create new Django user'))
        else:
            self.stdout.write(self.style.ERROR('Django user not found. Use --auto-create to create it.'))

