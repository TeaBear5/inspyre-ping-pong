"""
URL configuration for the core app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserRegistrationView, LoginView, PhoneVerificationView, FirebaseVerificationView,
    ResendVerificationView, UserProfileView, PlayerProfileViewSet, GameViewSet,
    TournamentViewSet, NotificationViewSet, RankingsView, StatsView, AdminUserViewSet,
    ApprovedPlayersView
)

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'profiles', PlayerProfileViewSet, basename='playerprofile')
router.register(r'games', GameViewSet, basename='game')
router.register(r'tournaments', TournamentViewSet, basename='tournament')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'admin/users', AdminUserViewSet, basename='admin-users')

urlpatterns = [
    # Authentication and user management
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/verify-phone/', PhoneVerificationView.as_view(), name='verify-phone'),
    path('auth/firebase-verify/', FirebaseVerificationView.as_view(), name='firebase-verify'),
    path('auth/resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),

    # Rankings and statistics
    path('rankings/', RankingsView.as_view(), name='rankings'),
    path('stats/', StatsView.as_view(), name='stats'),

    # Approved players (for game reporting)
    path('players/approved/', ApprovedPlayersView.as_view(), name='approved-players'),

    # Include router URLs
    path('', include(router.urls)),
]