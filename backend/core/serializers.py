"""
Serializers for the Ping Pong Tracker API
"""
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from .models import (
    User, PlayerProfile, Game, GameComment,
    Trophy, WeeklyLeaderboard, Tournament, TournamentMatch, Notification
)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    phone_number = PhoneNumberField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['phone_number', 'username', 'display_name', 'password', 'password_confirm', 'email']

    def validate_username(self, value):
        """Check if username already exists"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_phone_number(self, value):
        """Check if phone number already exists"""
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("An account with this phone number already exists.")
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords don't match"})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # Create player profile
        PlayerProfile.objects.create(user=user)

        return user


class PhoneVerificationSerializer(serializers.Serializer):
    """Serializer for phone verification"""
    code = serializers.CharField(max_length=6, min_length=6)


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer"""
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'bio', 'avatar', 'is_approved', 'phone_verified', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'is_approved', 'phone_verified', 'is_staff', 'is_superuser']


class PlayerProfileSerializer(serializers.ModelSerializer):
    """Serializer for player profiles"""
    user = UserSerializer(read_only=True)
    singles_win_rate = serializers.ReadOnlyField()
    doubles_win_rate = serializers.ReadOnlyField()

    class Meta:
        model = PlayerProfile
        fields = [
            'id', 'user', 'singles_elo', 'doubles_elo', 'peak_singles_elo', 'peak_doubles_elo',
            'peak_singles_date', 'peak_doubles_date', 'singles_games_played', 'doubles_games_played',
            'singles_wins', 'singles_losses', 'doubles_wins', 'doubles_losses',
            'singles_win_rate', 'doubles_win_rate', 'weekly_points', 'total_points',
            'current_streak', 'longest_streak', 'theme_preference'
        ]
        read_only_fields = [
            'id', 'user', 'singles_elo', 'doubles_elo', 'peak_singles_elo', 'peak_doubles_elo',
            'peak_singles_date', 'peak_doubles_date', 'singles_games_played', 'doubles_games_played',
            'singles_wins', 'singles_losses', 'doubles_wins', 'doubles_losses',
            'singles_win_rate', 'doubles_win_rate', 'weekly_points', 'total_points',
            'current_streak', 'longest_streak'
        ]


class GameReportSerializer(serializers.ModelSerializer):
    """Serializer for reporting a game"""
    class Meta:
        model = Game
        fields = [
            'game_type', 'player1', 'player2', 'team1_player1', 'team1_player2',
            'team2_player1', 'team2_player2', 'player1_score', 'player2_score',
            'winner', 'played_at', 'notes'
        ]

    def validate(self, data):
        game_type = data.get('game_type')

        if game_type == 'singles':
            if not data.get('player1') or not data.get('player2'):
                raise serializers.ValidationError("Singles games require player1 and player2")
            if data.get('player1') == data.get('player2'):
                raise serializers.ValidationError("Players cannot play against themselves")
            if data.get('winner') not in ['player1', 'player2']:
                raise serializers.ValidationError("Winner must be 'player1' or 'player2' for singles")
        else:  # doubles
            required_fields = ['team1_player1', 'team1_player2', 'team2_player1', 'team2_player2']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError(f"Doubles games require {field}")
            if data.get('winner') not in ['team1', 'team2']:
                raise serializers.ValidationError("Winner must be 'team1' or 'team2' for doubles")

            # Check for duplicate players
            players = [data.get(f) for f in required_fields]
            if len(players) != len(set(players)):
                raise serializers.ValidationError("Same player cannot be on multiple teams")

        return data

    def create(self, validated_data):
        validated_data['reported_by'] = self.context['request'].user
        validated_data['status'] = 'pending'
        return super().create(validated_data)


class GameSerializer(serializers.ModelSerializer):
    """Full game serializer"""
    player1 = UserSerializer(read_only=True)
    player2 = UserSerializer(read_only=True)
    team1_player1 = UserSerializer(read_only=True)
    team1_player2 = UserSerializer(read_only=True)
    team2_player1 = UserSerializer(read_only=True)
    team2_player2 = UserSerializer(read_only=True)
    reported_by = UserSerializer(read_only=True)
    verified_by = UserSerializer(read_only=True)
    disputed_by = UserSerializer(read_only=True)
    resolved_by = UserSerializer(read_only=True)
    needs_my_verification = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = '__all__'
        read_only_fields = [
            'id', 'status', 'reported_by', 'verified_by', 'disputed_by', 'resolved_by',
            'reported_at', 'verified_at', 'disputed_at', 'resolved_at',
            'player1_elo_before', 'player2_elo_before', 'player1_elo_after',
            'player2_elo_after', 'elo_change'
        ]

    def get_needs_my_verification(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.needs_verification_from(request.user)
        return False


class GameVerificationSerializer(serializers.Serializer):
    """Serializer for game verification actions"""
    action = serializers.ChoiceField(choices=['verify', 'dispute'])
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'dispute' and not data.get('reason'):
            raise serializers.ValidationError("Reason is required when disputing a game")
        return data


class GameCommentSerializer(serializers.ModelSerializer):
    """Serializer for game comments"""
    author = UserSerializer(read_only=True)

    class Meta:
        model = GameComment
        fields = ['id', 'game', 'author', 'content', 'created_at', 'edited_at']
        read_only_fields = ['id', 'author', 'created_at', 'edited_at']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class TrophySerializer(serializers.ModelSerializer):
    """Serializer for trophies"""
    player = UserSerializer(read_only=True)

    class Meta:
        model = Trophy
        fields = '__all__'
        read_only_fields = fields


class WeeklyLeaderboardSerializer(serializers.ModelSerializer):
    """Serializer for weekly leaderboard"""
    player = UserSerializer(read_only=True)

    class Meta:
        model = WeeklyLeaderboard
        fields = '__all__'
        read_only_fields = fields


class TournamentSerializer(serializers.ModelSerializer):
    """Serializer for tournaments"""
    created_by = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    participants = UserSerializer(many=True, read_only=True)
    first_place = UserSerializer(read_only=True)
    second_place = UserSerializer(read_only=True)
    third_place = UserSerializer(read_only=True)
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Tournament
        fields = '__all__'
        read_only_fields = [
            'id', 'created_by', 'approved_by', 'created_at', 'updated_at',
            'approved_at', 'first_place', 'second_place', 'third_place'
        ]

    def get_participant_count(self, obj):
        return obj.participants.count()

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['status'] = 'pending_approval'
        return super().create(validated_data)


class TournamentMatchSerializer(serializers.ModelSerializer):
    """Serializer for tournament matches"""
    player1 = UserSerializer(read_only=True)
    player2 = UserSerializer(read_only=True)
    winner = UserSerializer(read_only=True)
    games = GameSerializer(many=True, read_only=True)

    class Meta:
        model = TournamentMatch
        fields = '__all__'
        read_only_fields = ['id', 'winner', 'completed_at']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    recipient = UserSerializer(read_only=True)
    related_user = UserSerializer(read_only=True)
    related_game = serializers.PrimaryKeyRelatedField(read_only=True)
    related_tournament = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['id', 'recipient', 'created_at', 'read_at']

    def update(self, instance, validated_data):
        # Only allow updating is_read field
        instance.is_read = validated_data.get('is_read', instance.is_read)
        if instance.is_read and not instance.read_at:
            from django.utils import timezone
            instance.read_at = timezone.now()
        instance.save()
        return instance


class RankingsSerializer(serializers.Serializer):
    """Serializer for rankings page data"""
    singles_rankings = PlayerProfileSerializer(many=True)
    doubles_rankings = PlayerProfileSerializer(many=True)
    recent_games = GameSerializer(many=True)
    weekly_leaderboard = WeeklyLeaderboardSerializer(many=True)