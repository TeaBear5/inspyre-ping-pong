"""
Services for Firebase authentication, notifications, and other business logic
"""
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth


class FirebaseService:
    """Service for Firebase Authentication"""
    _initialized = False

    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK"""
        if cls._initialized:
            return True

        try:
            # Try different methods to get credentials
            if settings.FIREBASE_CREDENTIALS_PATH:
                # Use credentials file path
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
                cls._initialized = True
            elif settings.FIREBASE_CREDENTIALS_JSON:
                # Use credentials from JSON string (useful for Docker/env vars)
                cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                cls._initialized = True
            elif settings.FIREBASE_PROJECT_ID:
                # Use default credentials (works on Google Cloud)
                firebase_admin.initialize_app(options={
                    'projectId': settings.FIREBASE_PROJECT_ID
                })
                cls._initialized = True
            else:
                # Development mode - Firebase not configured
                print("[DEV] Firebase not configured - running in development mode")
                return False

            return True
        except Exception as e:
            print(f"[DEV] Firebase initialization error: {e}")
            return False

    @classmethod
    def verify_id_token(cls, id_token):
        """
        Verify a Firebase ID token and return the decoded token
        Returns None if invalid or Firebase not configured
        """
        if not cls.initialize():
            # Development mode - return mock verification
            print(f"[DEV] Mock token verification for: {id_token[:20]}...")
            return None

        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            return decoded_token
        except firebase_auth.InvalidIdTokenError:
            return None
        except firebase_auth.ExpiredIdTokenError:
            return None
        except Exception as e:
            print(f"Firebase token verification error: {e}")
            return None

    @classmethod
    def get_user_by_email(cls, email):
        """Get Firebase user by email"""
        if not cls.initialize():
            return None

        try:
            return firebase_auth.get_user_by_email(email)
        except firebase_auth.UserNotFoundError:
            return None
        except Exception as e:
            print(f"Firebase get user error: {e}")
            return None

    @classmethod
    def get_user_by_phone(cls, phone_number):
        """Get Firebase user by phone number"""
        if not cls.initialize():
            return None

        try:
            return firebase_auth.get_user_by_phone_number(phone_number)
        except firebase_auth.UserNotFoundError:
            return None
        except Exception as e:
            print(f"Firebase get user error: {e}")
            return None

    @classmethod
    def create_custom_token(cls, uid, claims=None):
        """Create a custom token for a user"""
        if not cls.initialize():
            return None

        try:
            return firebase_auth.create_custom_token(uid, claims)
        except Exception as e:
            print(f"Firebase create token error: {e}")
            return None

    @classmethod
    def send_email_verification(cls, email):
        """
        Generate email verification link
        Note: In production, Firebase handles sending the email automatically
        when using Firebase Auth on the frontend
        """
        if not cls.initialize():
            # Development mode - print to console
            print(f"[DEV] Email verification would be sent to: {email}")
            return True

        try:
            # Generate the verification link
            link = firebase_auth.generate_email_verification_link(email)
            print(f"[INFO] Verification link for {email}: {link}")
            return True
        except Exception as e:
            print(f"Firebase email verification error: {e}")
            return False


class VerificationService:
    """
    Service for handling verification
    With Firebase, verification happens on the frontend and backend just verifies tokens
    """

    @staticmethod
    def verify_firebase_token(id_token):
        """
        Verify a Firebase ID token
        Returns the decoded token data or None if invalid
        """
        return FirebaseService.verify_id_token(id_token)

    @staticmethod
    def is_user_verified_in_firebase(id_token):
        """
        Check if the user's email/phone is verified in Firebase
        """
        decoded = FirebaseService.verify_id_token(id_token)
        if not decoded:
            return False, None

        # Check verification status from Firebase token
        email_verified = decoded.get('email_verified', False)
        phone_number = decoded.get('phone_number')  # If present, phone is verified

        return True, {
            'uid': decoded.get('uid'),
            'email': decoded.get('email'),
            'email_verified': email_verified,
            'phone_number': phone_number,
            'phone_verified': phone_number is not None
        }


class NotificationService:
    """Service for handling notifications"""

    @staticmethod
    def notify_admin(subject, message, related_object=None):
        """Send notification to admin via email"""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,  # Don't crash if email fails
            )
            return True
        except Exception as e:
            print(f"Error sending admin notification: {e}")
            return False

    @staticmethod
    def create_game_verification_notification(game):
        """Create notification for game verification"""
        from .models import Notification

        # Determine who needs to verify
        if game.game_type == 'singles':
            if game.reported_by == game.player1:
                recipient = game.player2
            else:
                recipient = game.player1

            Notification.objects.create(
                recipient=recipient,
                notification_type='game_verification',
                title='Game Verification Required',
                message=f'{game.reported_by.display_name} reported a game result. Please verify.',
                related_game=game
            )
        else:
            # For doubles, notify all players on the opposing team
            reporting_team = game.get_reporting_team()
            if reporting_team == 'team1':
                recipients = [game.team2_player1, game.team2_player2]
            else:
                recipients = [game.team1_player1, game.team1_player2]

            for recipient in recipients:
                if recipient:
                    Notification.objects.create(
                        recipient=recipient,
                        notification_type='game_verification',
                        title='Doubles Game Verification Required',
                        message=f'{game.reported_by.display_name} reported a doubles game result. Please verify.',
                        related_game=game
                    )

    @staticmethod
    def create_game_disputed_notification(game, disputed_by, reason):
        """Create notifications when a game is disputed"""
        from .models import Notification

        # Notify admin
        NotificationService.notify_admin(
            subject='Game Disputed - Admin Action Required',
            message=f'A game has been disputed by {disputed_by.display_name}.\nReason: {reason}\nGame ID: {game.id}'
        )

        # Notify the reporter
        Notification.objects.create(
            recipient=game.reported_by,
            notification_type='game_disputed',
            title='Game Result Disputed',
            message=f'{disputed_by.display_name} has disputed your game report. An admin will review.',
            related_game=game
        )

        # Create admin notification in database
        from .models import User, Notification
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                notification_type='admin_alert',
                title='Game Dispute Requires Resolution',
                message=f'Game disputed by {disputed_by.display_name}. Reason: {reason}',
                related_game=game,
                related_user=disputed_by
            )

    @staticmethod
    def create_account_approval_notification(user):
        """Notify admin when a new account needs approval"""
        NotificationService.notify_admin(
            subject='New Account Pending Approval',
            message=f'New user registration:\nName: {user.display_name}\nUsername: {user.username}'
        )

        # Create admin notification in database
        from .models import User, Notification
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                notification_type='admin_alert',
                title='New Account Approval Required',
                message=f'{user.display_name} ({user.username}) has registered and needs approval.',
                related_user=user
            )


class GameService:
    """Service for game-related operations"""

    @staticmethod
    def process_verified_game(game):
        """
        Process a game after it's been verified
        Updates ELO ratings, statistics, and points
        """
        from .models import PlayerProfile, WeeklyLeaderboard
        from .elo import ELOCalculator, PointsCalculator

        if game.status != 'verified':
            return False

        if game.game_type == 'singles':
            # Get player profiles
            profile1 = game.player1.profile
            profile2 = game.player2.profile

            # Store current ratings
            game.player1_elo_before = profile1.singles_elo
            game.player2_elo_before = profile2.singles_elo

            # Determine winner
            if game.winner == 'player1':
                score1 = 1
                score2 = 0
                winner_profile = profile1
                loser_profile = profile2
            else:
                score1 = 0
                score2 = 1
                winner_profile = profile2
                loser_profile = profile1

            # Calculate new ratings
            new_rating1, new_rating2, elo_change = ELOCalculator.calculate_new_ratings(
                profile1.singles_elo,
                profile2.singles_elo,
                score1,
                profile1.singles_games_played,
                profile2.singles_games_played
            )

            # Update ratings
            profile1.singles_elo = new_rating1
            profile2.singles_elo = new_rating2
            game.player1_elo_after = new_rating1
            game.player2_elo_after = new_rating2
            game.elo_change = elo_change

            # Update peak ratings if necessary
            if profile1.singles_elo > profile1.peak_singles_elo:
                profile1.peak_singles_elo = profile1.singles_elo
                profile1.peak_singles_date = timezone.now()

            if profile2.singles_elo > profile2.peak_singles_elo:
                profile2.peak_singles_elo = profile2.singles_elo
                profile2.peak_singles_date = timezone.now()

            # Update game statistics
            profile1.singles_games_played += 1
            profile2.singles_games_played += 1

            if score1 == 1:
                profile1.singles_wins += 1
                profile2.singles_losses += 1
            else:
                profile1.singles_losses += 1
                profile2.singles_wins += 1

            # Calculate and award points
            winner_elo = winner_profile.singles_elo - elo_change  # Use pre-game ELO
            loser_elo = loser_profile.singles_elo + elo_change
            winner_points, loser_points = PointsCalculator.calculate_game_points(
                winner_elo, loser_elo, winner_profile.current_streak
            )

            # Update weekly points
            week_number = game.played_at.isocalendar()[1]
            year = game.played_at.year

            for profile, points in [(winner_profile, winner_points), (loser_profile, loser_points)]:
                weekly, created = WeeklyLeaderboard.objects.get_or_create(
                    player=profile.user,
                    week_number=week_number,
                    year=year,
                    defaults={'points': 0, 'games_played': 0, 'games_won': 0}
                )
                weekly.points += points
                weekly.games_played += 1
                if profile == winner_profile:
                    weekly.games_won += 1
                weekly.save()

                # Update total points
                profile.weekly_points += points
                profile.total_points += points

            # Update streaks
            GameService.update_streaks(winner_profile.user)
            GameService.update_streaks(loser_profile.user)

            # Save profiles
            profile1.save()
            profile2.save()

        # TODO: Handle doubles games similarly

        game.save()
        return True

    @staticmethod
    def update_streaks(user):
        """Update playing streaks for a user"""
        from .models import Game
        from datetime import timedelta
        from django.db import models

        profile = user.profile
        today = timezone.now().date()

        # Get last game before today
        last_game = Game.objects.filter(
            status='verified'
        ).filter(
            models.Q(player1=user) | models.Q(player2=user) |
            models.Q(team1_player1=user) | models.Q(team1_player2=user) |
            models.Q(team2_player1=user) | models.Q(team2_player2=user)
        ).filter(
            played_at__date__lt=today
        ).order_by('-played_at').first()

        # Get today's games
        todays_games = Game.objects.filter(
            status='verified'
        ).filter(
            models.Q(player1=user) | models.Q(player2=user) |
            models.Q(team1_player1=user) | models.Q(team1_player2=user) |
            models.Q(team2_player1=user) | models.Q(team2_player2=user)
        ).filter(
            played_at__date=today
        ).exists()

        if todays_games:
            if last_game:
                yesterday = today - timedelta(days=1)
                if last_game.played_at.date() == yesterday:
                    # Continuing streak
                    profile.current_streak += 1
                else:
                    # Broken streak, restart
                    profile.current_streak = 1
            else:
                # First game ever
                profile.current_streak = 1

            # Update longest streak if necessary
            if profile.current_streak > profile.longest_streak:
                profile.longest_streak = profile.current_streak

            profile.save()


class TrophyService:
    """Service for awarding trophies and achievements"""

    @staticmethod
    def check_and_award_trophies(user):
        """Check and award any earned trophies for a user"""
        from .models import Trophy, Game
        profile = user.profile

        # Check ELO milestones
        elo_milestones = [1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2200, 2500]
        for milestone in elo_milestones:
            if profile.singles_elo >= milestone:
                Trophy.objects.get_or_create(
                    player=user,
                    trophy_type='elo_milestone',
                    value=milestone,
                    defaults={
                        'name': f'{milestone} ELO Club',
                        'description': f'Reached {milestone} ELO rating in singles',
                        'icon': '🏆'
                    }
                )

        # Check games played milestones
        games_milestones = [10, 25, 50, 100, 250, 500, 1000]
        total_games = profile.singles_games_played + profile.doubles_games_played
        for milestone in games_milestones:
            if total_games >= milestone:
                Trophy.objects.get_or_create(
                    player=user,
                    trophy_type='games_played',
                    value=milestone,
                    defaults={
                        'name': f'{milestone} Games Veteran',
                        'description': f'Played {milestone} total games',
                        'icon': '🎮'
                    }
                )

        # Check streak achievements
        streak_milestones = [3, 7, 14, 30]
        for milestone in streak_milestones:
            if profile.longest_streak >= milestone:
                Trophy.objects.get_or_create(
                    player=user,
                    trophy_type='streak',
                    value=milestone,
                    defaults={
                        'name': f'{milestone}-Day Streak',
                        'description': f'Played games {milestone} days in a row',
                        'icon': '🔥'
                    }
                )
