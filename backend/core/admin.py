"""
Django Admin configuration for Ping Pong Tracker
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    User, PlayerProfile, Game, GameComment,
    Trophy, WeeklyLeaderboard, Tournament, TournamentMatch, Notification
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin interface for User model"""
    list_display = [
        'username', 'display_name', 'phone_number',
        'verification_status', 'approval_status', 'date_joined',
        'last_active', 'is_staff', 'quick_actions'
    ]
    list_filter = [
        'is_approved', 'phone_verified', 'is_staff',
        'is_superuser', 'is_active', 'date_joined'
    ]
    search_fields = ['username', 'display_name', 'phone_number', 'email']
    ordering = ['-date_joined']

    readonly_fields = ['date_joined', 'last_active', 'verification_code_created']

    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'display_name', 'email', 'phone_number', 'bio', 'avatar')
        }),
        ('Status', {
            'fields': ('is_active', 'phone_verified', 'is_approved', 'approved_by', 'approved_at'),
            'description': 'Control user access and verification status'
        }),
        ('Verification', {
            'fields': ('verification_code', 'verification_code_created'),
            'description': 'Phone verification details'
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_active', 'last_login'),
            'classes': ('collapse',)
        })
    )

    def verification_status(self, obj):
        """Display verification status with color coding"""
        if obj.phone_verified:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Verified</span>'
            )
        return format_html(
            '<span style="color: orange; font-weight: bold;">⚠ Unverified</span>'
        )
    verification_status.short_description = 'Phone Status'

    def approval_status(self, obj):
        """Display approval status with color coding"""
        if obj.is_approved:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Approved</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Pending</span>'
        )
    approval_status.short_description = 'Approval Status'

    def quick_actions(self, obj):
        """Quick action buttons for user management"""
        buttons = []

        if not obj.phone_verified:
            buttons.append(
                format_html(
                    '<a class="button" href="/admin/core/user/{}/change/" '
                    'onclick="document.getElementById(\'id_phone_verified\').checked=true; '
                    'document.querySelector(\'input[name=_save]\').click(); return false;"'
                    'style="padding: 3px 5px; background: #417690; color: white; border-radius: 3px; text-decoration: none; margin-right: 5px;">'
                    'Verify Phone</a>',
                    obj.pk
                )
            )

        if not obj.is_approved:
            buttons.append(
                format_html(
                    '<a class="button" href="/admin/core/user/{}/change/" '
                    'style="padding: 3px 5px; background: #35a93a; color: white; border-radius: 3px; text-decoration: none;">'
                    'Approve User</a>',
                    obj.pk
                )
            )

        return format_html(''.join(buttons)) if buttons else '-'
    quick_actions.short_description = 'Actions'

    actions = ['approve_users', 'verify_phones', 'approve_and_verify']

    def approve_users(self, request, queryset):
        """Bulk approve users"""
        count = queryset.update(
            is_approved=True,
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{count} users approved.')
    approve_users.short_description = 'Approve selected users'

    def verify_phones(self, request, queryset):
        """Bulk verify phone numbers"""
        count = queryset.update(phone_verified=True)
        self.message_user(request, f'{count} phone numbers verified.')
    verify_phones.short_description = 'Verify phone numbers for selected users'

    def approve_and_verify(self, request, queryset):
        """Bulk approve and verify users"""
        count = queryset.update(
            is_approved=True,
            approved_by=request.user,
            approved_at=timezone.now(),
            phone_verified=True
        )
        self.message_user(request, f'{count} users approved and verified.')
    approve_and_verify.short_description = 'Approve AND verify selected users'


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    """Admin interface for PlayerProfile"""
    list_display = [
        'user', 'singles_elo', 'doubles_elo', 'singles_games_played',
        'doubles_games_played', 'weekly_points', 'current_streak'
    ]
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__display_name']
    ordering = ['-singles_elo']

    readonly_fields = [
        'singles_win_rate', 'doubles_win_rate', 'created_at', 'updated_at'
    ]


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Admin interface for Games"""
    list_display = [
        'id_short', 'game_type', 'get_players', 'score', 'status_badge',
        'played_at', 'elo_change', 'quick_actions'
    ]
    list_filter = ['status', 'game_type', 'played_at', 'tournament']
    search_fields = [
        'player1__username', 'player2__username',
        'player1__display_name', 'player2__display_name'
    ]
    ordering = ['-played_at']
    date_hierarchy = 'played_at'

    readonly_fields = [
        'id', 'reported_at', 'verified_at', 'disputed_at', 'resolved_at',
        'player1_elo_before', 'player2_elo_before', 'player1_elo_after',
        'player2_elo_after', 'elo_change'
    ]

    fieldsets = (
        ('Game Information', {
            'fields': ('game_type', 'played_at', 'tournament', 'notes')
        }),
        ('Players & Score', {
            'fields': ('player1', 'player2', 'player1_score', 'player2_score', 'winner')
        }),
        ('Status & Verification', {
            'fields': (
                'status', 'reported_by', 'reported_at',
                'verified_by', 'verified_at',
                'disputed_by', 'disputed_at', 'dispute_reason',
                'resolved_by', 'resolved_at', 'resolution_notes'
            )
        }),
        ('ELO Changes', {
            'fields': (
                'player1_elo_before', 'player2_elo_before',
                'player1_elo_after', 'player2_elo_after', 'elo_change'
            ),
            'classes': ('collapse',)
        })
    )

    def id_short(self, obj):
        """Display shortened ID"""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'

    def get_players(self, obj):
        """Display players in the game"""
        if obj.game_type == 'singles':
            return f"{obj.player1.display_name} vs {obj.player2.display_name}"
        return "Doubles Game"
    get_players.short_description = 'Players'

    def score(self, obj):
        """Display game score"""
        return f"{obj.player1_score} - {obj.player2_score}"
    score.short_description = 'Score'

    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': 'orange',
            'verified': 'green',
            'disputed': 'red',
            'resolved': 'blue',
            'cancelled': 'gray'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def quick_actions(self, obj):
        """Quick action buttons for game management"""
        buttons = []

        if obj.status == 'pending':
            buttons.append(
                format_html(
                    '<a class="button" href="/admin/core/game/{}/change/" '
                    'style="padding: 3px 5px; background: #35a93a; color: white; '
                    'border-radius: 3px; text-decoration: none; margin-right: 5px;">'
                    'Verify</a>',
                    obj.pk
                )
            )
        elif obj.status == 'disputed':
            buttons.append(
                format_html(
                    '<a class="button" href="/admin/core/game/{}/change/" '
                    'style="padding: 3px 5px; background: #417690; color: white; '
                    'border-radius: 3px; text-decoration: none;">'
                    'Resolve</a>',
                    obj.pk
                )
            )

        return format_html(''.join(buttons)) if buttons else '-'
    quick_actions.short_description = 'Actions'

    actions = ['verify_games', 'mark_as_resolved']

    def verify_games(self, request, queryset):
        """Bulk verify games"""
        count = queryset.filter(status='pending').update(
            status='verified',
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(request, f'{count} games verified.')
    verify_games.short_description = 'Verify selected games'

    def mark_as_resolved(self, request, queryset):
        """Mark disputed games as resolved"""
        count = queryset.filter(status='disputed').update(
            status='resolved',
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{count} games marked as resolved.')
    mark_as_resolved.short_description = 'Resolve selected disputed games'


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    """Admin interface for Tournaments"""
    list_display = [
        'name', 'tournament_type', 'game_type', 'status',
        'participant_count', 'tournament_start', 'created_by'
    ]
    list_filter = ['status', 'tournament_type', 'game_type', 'tournament_start']
    search_fields = ['name', 'description']
    ordering = ['-tournament_start']
    date_hierarchy = 'tournament_start'

    filter_horizontal = ['participants']

    def participant_count(self, obj):
        return f"{obj.participants.count()}/{obj.max_participants}"
    participant_count.short_description = 'Participants'

    actions = ['approve_tournaments']

    def approve_tournaments(self, request, queryset):
        """Approve pending tournaments"""
        count = queryset.filter(status='pending_approval').update(
            status='approved',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{count} tournaments approved.')
    approve_tournaments.short_description = 'Approve selected tournaments'


@admin.register(Trophy)
class TrophyAdmin(admin.ModelAdmin):
    """Admin interface for Trophies"""
    list_display = ['player', 'name', 'trophy_type', 'earned_at']
    list_filter = ['trophy_type', 'earned_at']
    search_fields = ['player__username', 'player__display_name', 'name']
    ordering = ['-earned_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notifications"""
    list_display = [
        'recipient', 'notification_type', 'title',
        'is_read', 'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'title', 'message']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'


@admin.register(WeeklyLeaderboard)
class WeeklyLeaderboardAdmin(admin.ModelAdmin):
    """Admin interface for Weekly Leaderboards"""
    list_display = [
        'player', 'week_number', 'year', 'points',
        'games_played', 'games_won', 'rank'
    ]
    list_filter = ['year', 'week_number']
    search_fields = ['player__username', 'player__display_name']
    ordering = ['-year', '-week_number', '-points']


# Register remaining models
admin.site.register(GameComment)
admin.site.register(TournamentMatch)

# Customize admin site headers
admin.site.site_header = "Ping Pong Tracker Admin"
admin.site.site_title = "Ping Pong Tracker"
admin.site.index_title = "Dashboard"