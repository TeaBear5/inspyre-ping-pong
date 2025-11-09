"""
Services for phone authentication, notifications, and other business logic
"""
import random
import string
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from django.core.mail import send_mail
from django.template.loader import render_to_string


class PhoneVerificationService:
    """Service for handling phone number verification"""

    @staticmethod
    def generate_verification_code():
        """Generate a 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))

    @staticmethod
    def send_verification_code(phone_number, code):
        """
        Send verification code via SMS using Twilio
        Returns True if successful, False otherwise
        """
        if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
            # If Twilio not configured, print to console (development)
            print(f"[DEV] Verification code for {phone_number}: {code}")
            return True

        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=f"Your Ping Pong Tracker verification code is: {code}",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=str(phone_number)
            )
            return message.sid is not None
        except TwilioRestException as e:
            print(f"Error sending SMS: {e}")
            return False

    @staticmethod
    def verify_code(user, code):
        """
        Verify the code for a user
        Returns True if valid, False otherwise
        """
        if not user.verification_code:
            return False

        if user.verification_code != code:
            return False

        if not user.is_verification_code_valid():
            return False

        # Mark as verified
        user.phone_verified = True
        user.verification_code = ''
        user.verification_code_created = None
        user.save()

        return True

    @staticmethod
    def request_verification(user):
        """
        Generate and send a new verification code for a user
        """
        code = PhoneVerificationService.generate_verification_code()
        user.verification_code = code
        user.verification_code_created = timezone.now()
        user.save()

        return PhoneVerificationService.send_verification_code(user.phone_number, code)


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
                fail_silently=False,
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
            message=f'New user registration:\nName: {user.display_name}\nUsername: {user.username}\nPhone: {user.phone_number}'
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