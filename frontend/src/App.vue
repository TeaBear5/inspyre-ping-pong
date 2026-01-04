<template>
  <v-app>
    <!-- Navigation Bar -->
    <v-app-bar app color="primary" dark>
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title>
        <router-link to="/" class="white--text text-decoration-none">
          <span class="hidden-sm-and-down">Inspyre Ping Pong</span>
          <span class="hidden-md-and-up">Inspyre PP</span>
        </router-link>
      </v-toolbar-title>
      <v-spacer></v-spacer>

      <!-- Desktop Navigation -->
      <v-btn text to="/rankings" class="hidden-sm-and-down">
        <v-icon left>mdi-trophy</v-icon>
        Rankings
      </v-btn>
      <v-btn text to="/games" class="hidden-sm-and-down">
        <v-icon left>mdi-table-tennis</v-icon>
        Games
      </v-btn>
      <v-btn text to="/tournaments" class="hidden-sm-and-down">
        <v-icon left>mdi-tournament</v-icon>
        Tournaments
      </v-btn>
      <v-btn v-if="authStore.user?.is_staff" text to="/admin/users" class="hidden-sm-and-down">
        <v-icon left>mdi-account-group</v-icon>
        Users
      </v-btn>

      <!-- Theme Toggle -->
      <v-btn icon @click="toggleTheme" class="mr-2">
        <v-icon>{{ themeStore.isDark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>

      <!-- User Menu -->
      <v-menu v-if="authStore.isAuthenticated" offset-y>
        <template v-slot:activator="{ props }">
          <v-btn icon v-bind="props">
            <v-icon>mdi-account-circle</v-icon>
          </v-btn>
        </template>
        <v-list>
          <v-list-item :to="`/profile`">
            <v-list-item-title>My Profile</v-list-item-title>
          </v-list-item>
          <v-list-item @click="logout">
            <v-list-item-title>Logout</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>

      <div v-else>
        <v-btn text to="/login">Login</v-btn>
        <v-btn text to="/register">Register</v-btn>
      </div>

      <!-- Notifications -->
      <v-badge
        v-if="authStore.isAuthenticated"
        :content="unreadNotifications"
        :value="unreadNotifications > 0"
        color="error"
        class="mr-3"
      >
        <v-btn icon @click="showNotifications = !showNotifications">
          <v-icon>mdi-bell</v-icon>
        </v-btn>
      </v-badge>
    </v-app-bar>

    <!-- Navigation Drawer (Mobile) -->
    <v-navigation-drawer v-model="drawer" app temporary>
      <v-list nav dense>
        <v-list-item v-if="authStore.isAuthenticated" :to="`/profile`">
          <v-list-item-title>{{ authStore.user?.display_name }}</v-list-item-title>
          <v-list-item-subtitle>View Profile</v-list-item-subtitle>
        </v-list-item>

        <v-divider v-if="authStore.isAuthenticated"></v-divider>

        <v-list-item to="/rankings">
          <v-list-item-title>Rankings</v-list-item-title>
        </v-list-item>
        <v-list-item to="/games">
          <v-list-item-title>Games</v-list-item-title>
        </v-list-item>
        <v-list-item to="/report-game" v-if="authStore.canAccessApp">
          <v-list-item-title>Report Game</v-list-item-title>
        </v-list-item>
        <v-list-item to="/tournaments">
          <v-list-item-title>Tournaments</v-list-item-title>
        </v-list-item>

        <v-list-item v-if="authStore.user?.is_staff" to="/admin/users">
          <v-list-item-title>User Management</v-list-item-title>
        </v-list-item>

        <v-divider></v-divider>

        <v-list-item v-if="authStore.isAuthenticated" @click="logout">
          <v-list-item-title>Logout</v-list-item-title>
        </v-list-item>
        <div v-else>
          <v-list-item to="/login">
            <v-list-item-title>Login</v-list-item-title>
          </v-list-item>
          <v-list-item to="/register">
            <v-list-item-title>Register</v-list-item-title>
          </v-list-item>
        </div>
      </v-list>
    </v-navigation-drawer>

    <!-- Main Content -->
    <v-main>
      <!-- Status Alerts -->
      <v-alert v-if="authStore.isAuthenticated && !authStore.isVerified && authStore.firebaseConfigured && !isAdmin" type="warning" dismissible class="mb-0">
        <strong>Verification Required</strong> - Please verify your phone to access all features.
        <v-btn size="small" color="white" variant="text" @click="router.push('/verify-phone')">Verify Now</v-btn>
      </v-alert>

      <v-alert v-if="authStore.isAuthenticated && !authStore.isApproved && authStore.isVerified && !isAdmin" type="info" dismissible class="mb-0">
        <strong>Access Restricted</strong> - Your account access has been restricted. Please contact an administrator.
      </v-alert>

      <!-- Router View -->
      <router-view></router-view>
    </v-main>

    <!-- Notifications Panel -->
    <v-navigation-drawer v-model="showNotifications" app right temporary width="400">
      <v-list>
        <v-list-item>
          <v-list-item-title class="text-h6">Notifications</v-list-item-title>
          <template v-slot:append>
            <v-btn icon @click="markAllRead" :disabled="unreadNotifications === 0">
              <v-icon>mdi-check-all</v-icon>
            </v-btn>
          </template>
        </v-list-item>
      </v-list>
      <v-divider></v-divider>
      <v-list v-if="notifications.length > 0">
        <v-list-item
          v-for="notification in notifications"
          :key="notification.id"
          :class="{ 'bg-grey-lighten-4': !notification.is_read }"
        >
          <div @click="handleNotificationClick(notification)" style="cursor: pointer; flex-grow: 1;">
            <v-list-item-title>{{ notification.title }}</v-list-item-title>
            <v-list-item-subtitle>{{ notification.message }}</v-list-item-subtitle>
            <v-list-item-subtitle class="text-caption">
              {{ formatDate(notification.created_at) }}
            </v-list-item-subtitle>
          </div>
          <template v-slot:append>
            <v-btn
              icon
              size="small"
              @click="clearSingleNotification(notification)"
              :disabled="notification.is_read"
            >
              <v-icon size="small">mdi-check</v-icon>
            </v-btn>
          </template>
        </v-list-item>
      </v-list>
      <v-container v-else>
        <p class="text-center text-grey">No notifications</p>
      </v-container>
    </v-navigation-drawer>
  </v-app>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'
import { useTheme } from 'vuetify'
import axios from 'axios'
import { API_URL } from './config'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const theme = useTheme()

const drawer = ref(false)
const showNotifications = ref(false)
const notifications = ref([])
const unreadNotifications = ref(0)

// Check if user is admin
const isAdmin = computed(() => authStore.user?.is_staff || authStore.user?.is_superuser)

onMounted(async () => {
  authStore.initializeAuth()

  // Initialize theme store first (handles both authenticated and non-authenticated)
  await themeStore.initializeTheme()

  // Debug: Log theme object structure
  console.log('Vuetify theme object:', theme)
  console.log('Theme global:', theme.global)

  // Apply the theme to Vuetify - try different approaches
  try {
    if (theme.global && theme.global.name) {
      theme.global.name.value = themeStore.currentTheme
    }
  } catch (e) {
    console.warn('Could not set theme with .value, trying direct assignment')
    try {
      if (theme.global) {
        theme.global.name = themeStore.currentTheme
      }
    } catch (e2) {
      console.error('Could not set theme:', e2)
    }
  }

  if (authStore.isAuthenticated) {
    fetchNotifications()
    // Poll for notifications every 30 seconds
    setInterval(fetchNotifications, 30000)
  }
})

// Watch for theme changes from the store
watch(() => themeStore.currentTheme, (newTheme) => {
  // Update Vuetify theme with multiple fallback approaches
  try {
    if (theme.global && theme.global.name) {
      theme.global.name.value = newTheme
    }
  } catch (e) {
    console.warn('Could not set theme with .value in watcher, trying direct assignment')
    try {
      if (theme.global) {
        theme.global.name = newTheme
      }
    } catch (e2) {
      console.error('Could not set theme in watcher:', e2)
    }
  }
})

// Watch for authentication changes to load theme from profile
watch(() => authStore.isAuthenticated, async (isAuth) => {
  if (isAuth) {
    // User just logged in, load their theme preference
    await themeStore.loadThemeFromProfile()
    try {
      if (theme.global && theme.global.name) {
        theme.global.name.value = themeStore.currentTheme
      }
    } catch (e) {
      if (theme.global) {
        theme.global.name = themeStore.currentTheme
      }
    }
  }
})

const fetchNotifications = async () => {
  try {
    const response = await axios.get(`${API_URL}/notifications/`)
    const allNotifications = response.data.results || response.data

    // Show only unread notifications
    notifications.value = allNotifications.filter(n => !n.is_read)
    unreadNotifications.value = notifications.value.length
  } catch (error) {
    console.error('Failed to fetch notifications:', error)
  }
}

const markAllRead = async () => {
  try {
    await axios.post(`${API_URL}/notifications/mark_all_read/`)
    // Clear all notifications from the list after marking as read
    notifications.value = []
    unreadNotifications.value = 0
  } catch (error) {
    console.error('Failed to mark notifications as read:', error)
  }
}

const markNotificationRead = async (notificationId) => {
  try {
    await axios.patch(`${API_URL}/notifications/${notificationId}/`, { is_read: true })
  } catch (error) {
    console.error('Failed to mark notification as read:', error)
  }
}

const clearSingleNotification = async (notification) => {
  // Mark as read in the backend
  if (!notification.is_read) {
    await markNotificationRead(notification.id)
  }
  // Remove from local list
  notifications.value = notifications.value.filter(n => n.id !== notification.id)
  unreadNotifications.value = Math.max(0, unreadNotifications.value - 1)
}

const handleNotificationClick = async (notification) => {
  // Navigate based on notification type without marking as read
  if (notification.related_game) {
    // Close the notification drawer
    showNotifications.value = false
    // Navigate to games page - don't filter by status, just highlight the game
    router.push({
      path: '/games',
      query: { highlight: notification.related_game }
    })
  } else if (notification.related_tournament) {
    showNotifications.value = false
    router.push('/tournaments')
  }
}

const toggleTheme = () => {
  themeStore.toggleTheme()
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}
</script>

<style>
.text-decoration-none {
  text-decoration: none;
}
</style>