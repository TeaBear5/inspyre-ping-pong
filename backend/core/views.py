"""
API Views for the Ping Pong Tracker
"""
from rest_framework import generics, status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    User, PlayerProfile, Game, GameComment,
    Trophy, WeeklyLeaderboard, Tournament, TournamentMatch, Notification
)
from .serializers import (
    UserRegistrationSerializer, PhoneVerificationSerializer, UserSerializer,
    PlayerProfileSerializer, GameReportSerializer, GameSerializer,
    GameVerificationSerializer, GameCommentSerializer, TrophySerializer,
    WeeklyLeaderboardSerializer, TournamentSerializer, TournamentMatchSerializer,
    NotificationSerializer, RankingsSerializer
)
from .services import PhoneVerificationService, NotificationService, GameService, TrophyService


class IsApprovedUser(permissions.BasePermission):
    """Custom permission to only allow approved users to access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_approved


class UserRegistrationView(generics.CreateAPIView):
    """Register a new user"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        print(f"Registration data: {request.data}")  # Debug logging
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            print(f"Validation errors: {serializer.errors}")  # Debug logging
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        # Create token for the user
        token, created = Token.objects.get_or_create(user=user)

        # Request verification code
        PhoneVerificationService.request_verification(user)

        # Notify admin for approval
        NotificationService.create_account_approval_notification(user)

        return Response({
            'message': 'Registration successful. Please verify your phone number and wait for admin approval.',
            'user_id': str(user.id),
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Login with phone number and password"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')

        if not phone_number or not password:
            return Response(
                {'error': 'Phone number and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate using phone number
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Check password
        if not user.check_password(password):
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Create or get token
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })


class PhoneVerificationView(APIView):
    """Verify phone number with code"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PhoneVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']
        if PhoneVerificationService.verify_code(request.user, code):
            return Response({'message': 'Phone number verified successfully'})
        else:
            return Response(
                {'error': 'Invalid or expired verification code'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ResendVerificationView(APIView):
    """Resend verification code"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.phone_verified:
            return Response(
                {'error': 'Phone number already verified'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if PhoneVerificationService.request_verification(request.user):
            return Response({'message': 'Verification code sent'})
        else:
            return Response(
                {'error': 'Failed to send verification code'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class PlayerProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """View player profiles and statistics"""
    queryset = PlayerProfile.objects.all()
    serializer_class = PlayerProfileSerializer
    permission_classes = [IsApprovedUser]

    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get or update current user's player profile"""
        try:
            profile = request.user.profile
        except PlayerProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = PlayerProfile.objects.create(user=request.user)

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            # Only allow updating theme_preference
            if 'theme_preference' in request.data:
                profile.theme_preference = request.data['theme_preference']
                profile.save()
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-username/(?P<username>[^/.]+)')
    def by_username(self, request, username=None):
        """Get player profile by username"""
        try:
            user = User.objects.get(username=username)
            try:
                profile = user.profile
            except PlayerProfile.DoesNotExist:
                # Create profile if it doesn't exist
                profile = PlayerProfile.objects.create(user=user)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def games(self, request, pk=None):
        """Get games for a specific player"""
        profile = self.get_object()
        user = profile.user

        games = Game.objects.filter(
            Q(player1=user) | Q(player2=user) |
            Q(team1_player1=user) | Q(team1_player2=user) |
            Q(team2_player1=user) | Q(team2_player2=user)
        ).filter(status='verified').order_by('-played_at')[:50]

        serializer = GameSerializer(games, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def trophies(self, request, pk=None):
        """Get trophies for a specific player"""
        profile = self.get_object()
        trophies = Trophy.objects.filter(player=profile.user)
        serializer = TrophySerializer(trophies, many=True)
        return Response(serializer.data)


class GameViewSet(viewsets.ModelViewSet):
    """CRUD operations for games"""
    queryset = Game.objects.all()
    permission_classes = [IsApprovedUser]

    def get_serializer_class(self):
        if self.action == 'create':
            return GameReportSerializer
        elif self.action in ['verify', 'dispute']:
            return GameVerificationSerializer
        return GameSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by game type
        game_type = self.request.query_params.get('game_type')
        if game_type:
            queryset = queryset.filter(game_type=game_type)

        # Filter by player
        player_id = self.request.query_params.get('player')
        if player_id:
            queryset = queryset.filter(
                Q(player1_id=player_id) | Q(player2_id=player_id) |
                Q(team1_player1_id=player_id) | Q(team1_player2_id=player_id) |
                Q(team2_player1_id=player_id) | Q(team2_player2_id=player_id)
            )

        # Filter games needing my verification
        needs_verification = self.request.query_params.get('needs_my_verification')
        if needs_verification == 'true':
            user = self.request.user
            # This is a simple filter - we'll check in the serializer for exact logic
            queryset = queryset.filter(status='pending').exclude(reported_by=user)

        return queryset.order_by('-played_at')

    def create(self, request, *args, **kwargs):
        """Report a new game"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        game = serializer.save()

        # Create notification for verification
        NotificationService.create_game_verification_notification(game)

        response_serializer = GameSerializer(game, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify or dispute a game"""
        game = self.get_object()

        if game.status != 'pending':
            return Response(
                {'error': 'Game is not pending verification'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not game.needs_verification_from(request.user):
            return Response(
                {'error': 'You cannot verify this game'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']

        if action == 'verify':
            game.status = 'verified'
            game.verified_by = request.user
            game.verified_at = timezone.now()
            game.save()

            # Process the game (update ELO, stats, etc.)
            GameService.process_verified_game(game)

            # Check for trophies
            for player in [game.player1, game.player2]:
                if player:
                    TrophyService.check_and_award_trophies(player)

            return Response({'message': 'Game verified successfully'})

        else:  # dispute
            game.status = 'disputed'
            game.disputed_by = request.user
            game.disputed_at = timezone.now()
            game.dispute_reason = serializer.validated_data.get('reason', '')
            game.save()

            # Create notifications
            NotificationService.create_game_disputed_notification(
                game, request.user, game.dispute_reason
            )

            return Response({'message': 'Game disputed. Admin will review.'})

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """Get or add comments to a game"""
        game = self.get_object()

        if request.method == 'GET':
            comments = game.comments.all()
            serializer = GameCommentSerializer(comments, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            serializer = GameCommentSerializer(
                data={'game': game.id, 'content': request.data.get('content')},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent games"""
        games = self.get_queryset()[:20]
        serializer = self.get_serializer(games, many=True, context={'request': request})
        return Response(serializer.data)


class TournamentViewSet(viewsets.ModelViewSet):
    """CRUD operations for tournaments"""
    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer
    permission_classes = [IsApprovedUser]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by game type
        game_type = self.request.query_params.get('game_type')
        if game_type:
            queryset = queryset.filter(game_type=game_type)

        return queryset

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a tournament"""
        tournament = self.get_object()

        if tournament.status != 'approved':
            return Response(
                {'error': 'Tournament is not open for registration'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if timezone.now() > tournament.registration_end:
            return Response(
                {'error': 'Registration period has ended'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if tournament.participants.count() >= tournament.max_participants:
            return Response(
                {'error': 'Tournament is full'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tournament.participants.add(request.user)
        return Response({'message': 'Successfully joined tournament'})

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a tournament"""
        tournament = self.get_object()

        if tournament.status != 'approved':
            return Response(
                {'error': 'Cannot leave tournament at this stage'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tournament.participants.remove(request.user)
        return Response({'message': 'Successfully left tournament'})

    @action(detail=True, methods=['get'])
    def matches(self, request, pk=None):
        """Get tournament matches"""
        tournament = self.get_object()
        matches = tournament.matches.all()
        serializer = TournamentMatchSerializer(matches, many=True)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    """Handle user notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        notifications = self.get_queryset().filter(is_read=False)
        notifications.update(is_read=True, read_at=timezone.now())
        return Response({'message': f'{notifications.count()} notifications marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count})


class RankingsView(APIView):
    """Get rankings and leaderboard data"""
    permission_classes = [IsApprovedUser]

    def get(self, request):
        # Get singles rankings (top 20)
        singles_rankings = PlayerProfile.objects.filter(
            singles_games_played__gte=1  # Minimum games to appear in rankings
        ).order_by('-singles_elo')[:20]

        # Get doubles rankings (top 20)
        doubles_rankings = PlayerProfile.objects.filter(
            doubles_games_played__gte=1
        ).order_by('-doubles_elo')[:20]

        # Get recent verified games
        recent_games = Game.objects.filter(
            status='verified'
        ).order_by('-played_at')[:10]

        # Get current week's leaderboard - use PlayerProfile weekly_points instead
        weekly_leaderboard = PlayerProfile.objects.filter(
            weekly_points__gt=0
        ).order_by('-weekly_points')[:10]

        # Also get all players (including those with 0 games)
        all_players = PlayerProfile.objects.all().order_by('-singles_elo')

        data = {
            'singles_rankings': PlayerProfileSerializer(singles_rankings, many=True).data,
            'doubles_rankings': PlayerProfileSerializer(doubles_rankings, many=True).data,
            'recent_games': GameSerializer(recent_games, many=True, context={'request': request}).data,
            'weekly_leaderboard': PlayerProfileSerializer(weekly_leaderboard, many=True).data,
            'all_players': PlayerProfileSerializer(all_players, many=True).data
        }

        return Response(data)


class StatsView(APIView):
    """Get overall statistics"""
    permission_classes = [IsApprovedUser]

    def get(self, request):
        total_games = Game.objects.filter(status='verified').count()
        total_players = User.objects.filter(is_approved=True).count()
        active_tournaments = Tournament.objects.filter(status='in_progress').count()

        # Games this week
        start_of_week = timezone.now() - timedelta(days=timezone.now().weekday())
        games_this_week = Game.objects.filter(
            status='verified',
            played_at__gte=start_of_week
        ).count()

        # Highest rated players
        top_singles = PlayerProfile.objects.filter(
            singles_games_played__gte=5
        ).order_by('-singles_elo').first()

        top_doubles = PlayerProfile.objects.filter(
            doubles_games_played__gte=5
        ).order_by('-doubles_elo').first()

        data = {
            'total_games': total_games,
            'total_players': total_players,
            'active_tournaments': active_tournaments,
            'games_this_week': games_this_week,
            'top_singles_player': UserSerializer(top_singles.user).data if top_singles else None,
            'top_singles_elo': top_singles.singles_elo if top_singles else None,
            'top_doubles_player': UserSerializer(top_doubles.user).data if top_doubles else None,
            'top_doubles_elo': top_doubles.doubles_elo if top_doubles else None,
        }

        return Response(data)


class AdminUserViewSet(viewsets.ModelViewSet):
    """Admin interface for user management"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        """Return all users with additional info"""
        return User.objects.all().order_by('-date_joined')

    def list(self, request):
        """List all users with full details"""
        queryset = self.get_queryset()
        data = []
        for user in queryset:
            user_data = UserSerializer(user).data
            user_data['is_staff'] = user.is_staff
            user_data['is_superuser'] = user.is_superuser
            user_data['date_joined'] = user.date_joined
            user_data['phone_number'] = str(user.phone_number)
            data.append(user_data)
        return Response(data)

    def partial_update(self, request, pk=None):
        """Update user status fields"""
        user = self.get_object()

        # Only allow updating certain fields
        allowed_fields = ['phone_verified', 'is_approved', 'is_active']
        update_data = {}

        for field in allowed_fields:
            if field in request.data:
                update_data[field] = request.data[field]

        # Track approval
        if 'is_approved' in update_data and update_data['is_approved']:
            update_data['approved_by'] = request.user
            update_data['approved_at'] = timezone.now()

        # Update the user
        for field, value in update_data.items():
            setattr(user, field, value)
        user.save()

        # Return updated user data
        user_data = UserSerializer(user).data
        user_data['is_staff'] = user.is_staff
        user_data['is_superuser'] = user.is_superuser
        user_data['date_joined'] = user.date_joined
        user_data['phone_number'] = str(user.phone_number)

        return Response(user_data)


class ApprovedPlayersView(generics.ListAPIView):
    """Get list of approved players - available to all authenticated users"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only approved and phone verified users"""
        return User.objects.filter(
            is_approved=True,
            phone_verified=True
        ).order_by('display_name', 'username')