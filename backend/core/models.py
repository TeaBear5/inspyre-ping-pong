from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
import uuid
from datetime import datetime, timedelta
from django.utils import timezone


class User(AbstractUser):
    """Custom user model with phone number authentication and admin approval"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = PhoneNumberField(unique=True, null=False, blank=False)
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(null=True, blank=True)

    # Profile fields
    display_name = models.CharField(max_length=100)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    # Admin approval system
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_users')
    approved_at = models.DateTimeField(null=True, blank=True)

    # Verification
    phone_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True)
    verification_code_created = models.DateTimeField(null=True, blank=True)

    # Stats tracking
    # date_joined already exists in AbstractUser
    last_active = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['username', 'display_name']

    def __str__(self):
        return f"{self.display_name} ({self.username})"

    def is_verification_code_valid(self):
        """Check if verification code is still valid (10 minutes)"""
        if not self.verification_code_created:
            return False
        return timezone.now() < self.verification_code_created + timedelta(minutes=10)


class PlayerProfile(models.Model):
    """Extended profile for ping pong players"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # ELO Ratings
    singles_elo = models.IntegerField(default=1200, validators=[MinValueValidator(0)])
    doubles_elo = models.IntegerField(default=1200, validators=[MinValueValidator(0)])

    # Peak ratings
    peak_singles_elo = models.IntegerField(default=1200, validators=[MinValueValidator(0)])
    peak_doubles_elo = models.IntegerField(default=1200, validators=[MinValueValidator(0)])
    peak_singles_date = models.DateTimeField(null=True, blank=True)
    peak_doubles_date = models.DateTimeField(null=True, blank=True)

    # Game counts
    singles_games_played = models.IntegerField(default=0)
    doubles_games_played = models.IntegerField(default=0)
    singles_wins = models.IntegerField(default=0)
    singles_losses = models.IntegerField(default=0)
    doubles_wins = models.IntegerField(default=0)
    doubles_losses = models.IntegerField(default=0)

    # Points system for regular play
    weekly_points = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)  # Days in a row played
    longest_streak = models.IntegerField(default=0)

    # User preferences
    theme_preference = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='light',
        help_text='User theme preference (light or dark mode)'
    )

    # Achievements/Trophies
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-singles_elo']

    def __str__(self):
        return f"{self.user.display_name}'s Profile"

    @property
    def singles_win_rate(self):
        total = self.singles_games_played
        if total == 0:
            return 0
        return (self.singles_wins / total) * 100

    @property
    def doubles_win_rate(self):
        total = self.doubles_games_played
        if total == 0:
            return 0
        return (self.doubles_wins / total) * 100


class Game(models.Model):
    """Model for individual ping pong games"""
    GAME_TYPES = [
        ('singles', 'Singles'),
        ('doubles', 'Doubles'),
    ]

    GAME_STATUS = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('disputed', 'Disputed'),
        ('resolved', 'Admin Resolved'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game_type = models.CharField(max_length=10, choices=GAME_TYPES)
    status = models.CharField(max_length=20, choices=GAME_STATUS, default='pending')

    # Singles players
    player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='games_as_player1', null=True, blank=True)
    player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='games_as_player2', null=True, blank=True)

    # Doubles teams (if applicable)
    team1_player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doubles_team1_p1', null=True, blank=True)
    team1_player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doubles_team1_p2', null=True, blank=True)
    team2_player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doubles_team2_p1', null=True, blank=True)
    team2_player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doubles_team2_p2', null=True, blank=True)

    # Scores
    player1_score = models.IntegerField(validators=[MinValueValidator(0)])
    player2_score = models.IntegerField(validators=[MinValueValidator(0)])

    # Winner tracking
    winner = models.CharField(max_length=10)  # 'player1' or 'player2' or 'team1' or 'team2'

    # Reporting and verification
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_games')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_games')
    disputed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='disputed_games')
    dispute_reason = models.TextField(blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_games')
    resolution_notes = models.TextField(blank=True)

    # Timestamps
    played_at = models.DateTimeField()
    reported_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    disputed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # ELO changes
    player1_elo_before = models.IntegerField(null=True, blank=True)
    player2_elo_before = models.IntegerField(null=True, blank=True)
    player1_elo_after = models.IntegerField(null=True, blank=True)
    player2_elo_after = models.IntegerField(null=True, blank=True)
    elo_change = models.IntegerField(null=True, blank=True)  # Absolute value of change

    # Additional metadata
    tournament = models.ForeignKey('Tournament', on_delete=models.SET_NULL, null=True, blank=True, related_name='games')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-played_at']

    def __str__(self):
        if self.game_type == 'singles':
            return f"{self.player1.display_name} vs {self.player2.display_name} - {self.played_at.date()}"
        else:
            return f"Doubles Game - {self.played_at.date()}"

    def get_opponent(self, user):
        """Get the opponent for a given user in singles games"""
        if self.game_type != 'singles':
            return None
        if self.player1 == user:
            return self.player2
        elif self.player2 == user:
            return self.player1
        return None

    def needs_verification_from(self, user):
        """Check if a specific user needs to verify this game"""
        if self.status != 'pending':
            return False

        if self.game_type == 'singles':
            # The non-reporter needs to verify
            if self.reported_by == self.player1:
                return user == self.player2
            else:
                return user == self.player1
        else:
            # In doubles, any player from the non-reporting team can verify
            reporting_team = self.get_reporting_team()
            if reporting_team == 'team1':
                return user in [self.team2_player1, self.team2_player2]
            else:
                return user in [self.team1_player1, self.team1_player2]

    def get_reporting_team(self):
        """For doubles games, determine which team reported the game"""
        if self.game_type != 'doubles':
            return None
        if self.reported_by in [self.team1_player1, self.team1_player2]:
            return 'team1'
        return 'team2'


class GameComment(models.Model):
    """Comments/chat for games"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.display_name} on {self.game}"


class Trophy(models.Model):
    """Trophies and achievements for players"""
    TROPHY_TYPES = [
        ('weekly_winner', 'Weekly Champion'),
        ('monthly_winner', 'Monthly Champion'),
        ('streak', 'Streak Master'),
        ('games_played', 'Games Milestone'),
        ('elo_milestone', 'ELO Milestone'),
        ('tournament', 'Tournament'),
        ('special', 'Special Achievement'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trophies')
    trophy_type = models.CharField(max_length=20, choices=TROPHY_TYPES)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True)  # Icon class or emoji

    # Metadata for specific achievements
    week_number = models.IntegerField(null=True, blank=True)  # For weekly trophies
    year = models.IntegerField(null=True, blank=True)
    value = models.IntegerField(null=True, blank=True)  # e.g., streak length, ELO reached

    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-earned_at']
        unique_together = [['player', 'trophy_type', 'week_number', 'year']]

    def __str__(self):
        return f"{self.name} - {self.player.display_name}"


class WeeklyLeaderboard(models.Model):
    """Track weekly points and rankings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_standings')
    week_number = models.IntegerField()
    year = models.IntegerField()

    points = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)

    rank = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', '-week_number', '-points']
        unique_together = [['player', 'week_number', 'year']]

    def __str__(self):
        return f"{self.player.display_name} - Week {self.week_number}/{self.year}"


class Tournament(models.Model):
    """Tournament model for bracket-style competitions"""
    TOURNAMENT_STATUS = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    TOURNAMENT_TYPES = [
        ('single_elimination', 'Single Elimination'),
        ('double_elimination', 'Double Elimination'),
        ('round_robin', 'Round Robin'),
        ('swiss', 'Swiss'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    tournament_type = models.CharField(max_length=20, choices=TOURNAMENT_TYPES, default='single_elimination')
    game_type = models.CharField(max_length=10, choices=[('singles', 'Singles'), ('doubles', 'Doubles')])

    status = models.CharField(max_length=20, choices=TOURNAMENT_STATUS, default='draft')

    # Participants
    max_participants = models.IntegerField(validators=[MinValueValidator(4)])
    participants = models.ManyToManyField(User, related_name='tournaments', blank=True)

    # Admin approval
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tournaments')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_tournaments')

    # Dates
    registration_start = models.DateTimeField()
    registration_end = models.DateTimeField()
    tournament_start = models.DateTimeField()
    tournament_end = models.DateTimeField(null=True, blank=True)

    # Winner tracking
    first_place = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='first_place_tournaments')
    second_place = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='second_place_tournaments')
    third_place = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='third_place_tournaments')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-tournament_start']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class TournamentMatch(models.Model):
    """Individual matches within a tournament"""
    MATCH_STATUS = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('bye', 'Bye'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    round_number = models.IntegerField()
    match_number = models.IntegerField()

    player1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tournament_matches_p1', null=True, blank=True)
    player2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tournament_matches_p2', null=True, blank=True)

    status = models.CharField(max_length=20, choices=MATCH_STATUS, default='pending')
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_matches')

    # Link to the actual game(s)
    games = models.ManyToManyField(Game, related_name='tournament_matches', blank=True)

    # For bracket positioning
    next_match = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_matches')

    scheduled_time = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['round_number', 'match_number']
        unique_together = [['tournament', 'round_number', 'match_number']]

    def __str__(self):
        return f"{self.tournament.name} - Round {self.round_number}, Match {self.match_number}"


class Notification(models.Model):
    """Notifications for users"""
    NOTIFICATION_TYPES = [
        ('game_verification', 'Game Needs Verification'),
        ('game_verified', 'Game Verified'),
        ('game_disputed', 'Game Disputed'),
        ('game_resolved', 'Game Resolved'),
        ('tournament_invite', 'Tournament Invitation'),
        ('tournament_start', 'Tournament Starting'),
        ('match_scheduled', 'Match Scheduled'),
        ('account_approved', 'Account Approved'),
        ('achievement', 'New Achievement'),
        ('admin_alert', 'Admin Alert'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)

    title = models.CharField(max_length=200)
    message = models.TextField()

    # Related objects
    related_game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True)
    related_tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True, blank=True)
    related_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='related_notifications')

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} - {self.recipient.display_name}"