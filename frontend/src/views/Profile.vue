<template>
  <v-container fluid class="pa-3 pa-md-6">
    <!-- Loading State -->
    <v-row v-if="profileLoading" class="mt-4 mt-md-8">
      <v-col cols="12" class="text-center">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
        <div class="mt-4">Loading profile...</div>
      </v-col>
    </v-row>

    <!-- Error State -->
    <v-row v-else-if="profileError" class="mt-4 mt-md-8">
      <v-col cols="12" class="text-center">
        <v-alert type="error" class="mx-auto" max-width="600">
          {{ profileError }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Profile Content -->
    <template v-else>
    <v-row>
      <!-- Profile Header -->
      <v-col cols="12">
        <v-card>
          <v-card-text class="pa-4 pa-md-6">
            <v-row align="center" class="flex-column flex-md-row">
              <v-col cols="12" md="auto" class="text-center text-md-left">
                <v-avatar :size="$vuetify.display.mobile ? 80 : 100" color="primary">
                  <span :class="$vuetify.display.mobile ? 'text-h4' : 'text-h3'">
                    {{ userInitial }}
                  </span>
                </v-avatar>
              </v-col>
              <v-col cols="12" md="" class="text-center text-md-left">
                <h1 :class="$vuetify.display.mobile ? 'text-h4' : 'text-h3'">{{ displayName }}</h1>
                <div class="text-subtitle-1 text-grey">@{{ username }}</div>
                <div class="mt-2 d-flex flex-wrap justify-center justify-md-start">
                  <v-chip class="ma-1" color="primary" size="small">
                    ELO: {{ playerProfile?.singles_elo || 1000 }}
                  </v-chip>
                  <!-- Doubles ELO hidden temporarily -->
                  <v-chip class="ma-1" color="info" size="small">
                    Weekly: {{ playerProfile?.weekly_points || 0 }}
                  </v-chip>
                </div>
              </v-col>
              <v-col cols="12" md="auto" v-if="isOwnProfile" class="text-center text-md-right">
                <v-btn
                  color="primary"
                  @click="showEditDialog = true"
                  :size="$vuetify.display.mobile ? 'small' : 'default'"
                  :block="$vuetify.display.mobile"
                >
                  <v-icon left>mdi-pencil</v-icon>
                  Edit Profile
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Statistics Overview -->
    <v-row class="mt-4">
      <v-col cols="6" md="3">
        <v-card>
          <v-card-text class="text-center pa-3 pa-md-4">
            <div :class="$vuetify.display.mobile ? 'text-h5' : 'text-h4'">{{ totalGamesPlayed }}</div>
            <div :class="$vuetify.display.mobile ? 'text-caption' : 'text-subtitle-1'">Total Games</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" md="3">
        <v-card>
          <v-card-text class="text-center pa-3 pa-md-4">
            <div :class="$vuetify.display.mobile ? 'text-h5' : 'text-h4'">{{ totalWins }}</div>
            <div :class="$vuetify.display.mobile ? 'text-caption' : 'text-subtitle-1'">Total Wins</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" md="3">
        <v-card>
          <v-card-text class="text-center pa-3 pa-md-4">
            <div :class="$vuetify.display.mobile ? 'text-h5' : 'text-h4'">{{ winRate }}%</div>
            <div :class="$vuetify.display.mobile ? 'text-caption' : 'text-subtitle-1'">Win Rate</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" md="3">
        <v-card>
          <v-card-text class="text-center pa-3 pa-md-4">
            <div :class="$vuetify.display.mobile ? 'text-h5' : 'text-h4'">{{ playerProfile?.current_streak || 0 }}</div>
            <div :class="$vuetify.display.mobile ? 'text-caption' : 'text-subtitle-1'">Current Streak</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Detailed Statistics -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>Game Statistics</v-card-title>
          <v-card-text>
            <v-table>
              <tbody>
                <tr>
                  <td>Current ELO</td>
                  <td class="text-right font-weight-bold">{{ playerProfile?.singles_elo || 1000 }}</td>
                </tr>
                <tr>
                  <td>Peak ELO</td>
                  <td class="text-right">
                    {{ playerProfile?.peak_singles_elo || 1000 }}
                    <div class="text-caption" v-if="playerProfile?.peak_singles_date">
                      {{ formatDate(playerProfile.peak_singles_date) }}
                    </div>
                  </td>
                </tr>
                <tr>
                  <td>Games Played</td>
                  <td class="text-right">{{ playerProfile?.singles_games_played || 0 }}</td>
                </tr>
                <tr>
                  <td>Wins</td>
                  <td class="text-right text-success">{{ playerProfile?.singles_wins || 0 }}</td>
                </tr>
                <tr>
                  <td>Losses</td>
                  <td class="text-right text-error">{{ playerProfile?.singles_losses || 0 }}</td>
                </tr>
                <tr>
                  <td>Win Rate</td>
                  <td class="text-right">{{ playerProfile?.singles_win_rate || '0.0' }}%</td>
                </tr>
                <tr>
                  <td>Current Streak</td>
                  <td class="text-right">{{ playerProfile?.current_streak || 0 }}</td>
                </tr>
                <tr>
                  <td>Longest Streak</td>
                  <td class="text-right">{{ playerProfile?.longest_streak || 0 }}</td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Trophies Section -->
    <v-row class="mt-4" v-if="trophies.length > 0">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon left color="amber">mdi-trophy</v-icon>
            Trophies & Achievements
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col
                v-for="trophy in trophies"
                :key="trophy.id"
                cols="12"
                md="4"
              >
                <v-card variant="outlined">
                  <v-card-text class="text-center">
                    <v-icon size="40" :color="getTrophyColor(trophy.trophy_type)">
                      {{ getTrophyIcon(trophy.trophy_type) }}
                    </v-icon>
                    <div class="text-subtitle-1 mt-2">{{ trophy.title }}</div>
                    <div class="text-caption">{{ trophy.description }}</div>
                    <div class="text-caption mt-2">
                      {{ formatDate(trophy.awarded_at) }}
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Recent Games -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            Recent Games
            <v-spacer></v-spacer>
            <v-btn
              text
              color="primary"
              @click="router.push('/games')"
            >
              View All
              <v-icon right>mdi-arrow-right</v-icon>
            </v-btn>
          </v-card-title>
          <v-table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Opponent(s)</th>
                <th>Score</th>
                <th>Result</th>
                <th>ELO Change</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="game in recentGames" :key="game.id">
                <td>{{ formatDate(game.played_at) }}</td>
                <td>
                  <v-chip size="small" :color="game.game_type === 'singles' ? 'blue' : 'green'">
                    {{ game.game_type }}
                  </v-chip>
                </td>
                <td>
                  <div v-if="game.game_type === 'singles'">
                    vs {{ getOpponentName(game) }}
                  </div>
                  <div v-else>
                    {{ getDoublesOpponents(game) }}
                  </div>
                </td>
                <td>{{ game.player1_score }} - {{ game.player2_score }}</td>
                <td>
                  <v-chip
                    size="small"
                    :color="isWin(game) ? 'success' : 'error'"
                  >
                    {{ isWin(game) ? 'Won' : 'Lost' }}
                  </v-chip>
                </td>
                <td>
                  <v-chip
                    size="small"
                    :color="getEloChange(game) > 0 ? 'success' : 'error'"
                    v-if="game.status === 'verified'"
                  >
                    {{ getEloChange(game) > 0 ? '+' : '' }}{{ getEloChange(game) }}
                  </v-chip>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </v-table>
          <v-card-text v-if="recentGames.length === 0" class="text-center">
            No games played yet
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Edit Profile Dialog -->
    <v-dialog v-model="showEditDialog" max-width="500">
      <v-card>
        <v-card-title>Edit Profile</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editData.display_name"
            label="Display Name"
            variant="outlined"
          ></v-text-field>
          <v-textarea
            v-model="editData.bio"
            label="Bio"
            rows="3"
            variant="outlined"
            counter
            maxlength="500"
          ></v-textarea>

          <!-- Theme Preference -->
          <div class="mt-4">
            <v-switch
              v-model="editData.dark_mode"
              label="Dark Mode"
              color="primary"
              :hint="editData.dark_mode ? 'Dark theme enabled' : 'Light theme enabled'"
              persistent-hint
            ></v-switch>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showEditDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            @click="updateProfile"
            :loading="updateLoading"
          >
            Save Changes
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    </template>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useThemeStore } from '../stores/theme'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Data
const user = ref(null)
const playerProfile = ref(null)
const recentGames = ref([])
const trophies = ref([])
const showEditDialog = ref(false)
const updateLoading = ref(false)
const profileLoading = ref(true)
const profileError = ref(null)
const editData = ref({
  display_name: '',
  bio: '',
  dark_mode: false
})

// Get username from route or use current user
const username = computed(() => route.params.username || authStore.user?.username)
const isOwnProfile = computed(() => !route.params.username || route.params.username === authStore.user?.username)

// Watch for dialog opening to sync current data
watch(showEditDialog, (newVal) => {
  if (newVal && isOwnProfile.value) {
    // Sync all current data when opening dialog
    editData.value = {
      display_name: user.value?.display_name || '',
      bio: user.value?.bio || '',
      dark_mode: themeStore.currentTheme === 'dark'
    }
  }
})

// User display info
const displayName = computed(() => user.value?.display_name || user.value?.username || 'Unknown')
const userInitial = computed(() => displayName.value[0]?.toUpperCase() || '?')

// Statistics (Singles only while doubles is disabled)
const totalGamesPlayed = computed(() => {
  if (!playerProfile.value) return 0
  return playerProfile.value.singles_games_played || 0
})

const totalWins = computed(() => {
  if (!playerProfile.value) return 0
  return playerProfile.value.singles_wins || 0
})

const winRate = computed(() => {
  if (!totalGamesPlayed.value) return '0.0'
  return ((totalWins.value / totalGamesPlayed.value) * 100).toFixed(1)
})

// Methods
const fetchProfile = async () => {
  profileLoading.value = true
  profileError.value = null

  try {
    // Ensure we have a username to fetch
    if (!username.value) {
      console.error('No username available for profile fetch')
      console.log('Current route params:', route.params)
      console.log('Current auth user:', authStore.user)
      profileError.value = 'No username available'
      router.push('/')
      return
    }

    console.log('Fetching profile for username:', username.value)

    // Fetch player profile
    const profileResponse = await axios.get(`${API_URL}/profiles/by-username/${username.value}/`)
    playerProfile.value = profileResponse.data
    user.value = profileResponse.data.user

    // Set edit data
    editData.value = {
      display_name: user.value.display_name || '',
      bio: user.value.bio || '',
      dark_mode: playerProfile.value?.theme_preference === 'dark'
    }

    // If this is the current user's profile, sync theme
    // Only set theme if it's different from current
    try {
      if (isOwnProfile.value && playerProfile.value?.theme_preference && playerProfile.value.theme_preference !== themeStore.currentTheme) {
        themeStore.setTheme(playerProfile.value.theme_preference)
      }
    } catch (themeError) {
      console.warn('Failed to sync theme preference:', themeError)
      // Continue loading profile even if theme sync fails
    }

    // Fetch recent games
    const gamesResponse = await axios.get(`${API_URL}/games/`, {
      params: {
        player: user.value.id,
        page_size: 10,
        status: 'verified'
      }
    })
    recentGames.value = gamesResponse.data.results || gamesResponse.data

    // Fetch trophies (using profile ID instead of user ID)
    if (playerProfile.value && playerProfile.value.id) {
      try {
        const trophiesResponse = await axios.get(`${API_URL}/profiles/${playerProfile.value.id}/trophies/`)
        trophies.value = trophiesResponse.data.results || trophiesResponse.data
      } catch (trophyError) {
        console.warn('Failed to fetch trophies:', trophyError)
        // Don't fail the whole profile load if trophies fail
        trophies.value = []
      }
    } else {
      console.warn('No profile ID available for fetching trophies')
      trophies.value = []
    }
  } catch (error) {
    console.error('Failed to fetch profile:', error)
    console.error('Error details:', error.response?.data)

    if (error.response?.status === 404) {
      profileError.value = `Profile not found for username: ${username.value}`
    } else {
      profileError.value = error.response?.data?.error || error.response?.data?.detail || 'Failed to load profile'
    }
  } finally {
    profileLoading.value = false
  }
}

const updateProfile = async () => {
  updateLoading.value = true
  try {
    // Update user profile
    const response = await authStore.updateProfile({
      display_name: editData.value.display_name,
      bio: editData.value.bio
    })
    user.value = response

    // Convert boolean to theme string
    const newTheme = editData.value.dark_mode ? 'dark' : 'light'

    // Update theme preference in player profile if changed
    if (newTheme !== playerProfile.value?.theme_preference) {
      // Update backend
      await axios.patch(`${API_URL}/profiles/me/`, {
        theme_preference: newTheme
      })

      // Update local profile data
      if (playerProfile.value) {
        playerProfile.value.theme_preference = newTheme
      }
    }

    // Always apply theme change immediately (even if it's the same)
    // This ensures it takes effect right away
    themeStore.setTheme(newTheme)

    showEditDialog.value = false
  } catch (error) {
    console.error('Failed to update profile:', error)
    alert('Failed to update profile. Please try again.')
  } finally {
    updateLoading.value = false
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

const getOpponentName = (game) => {
  if (game.game_type !== 'singles') return ''

  const isPlayer1 = game.player1?.id === user.value?.id || game.player1 === user.value?.id
  const opponent = isPlayer1 ? game.player2 : game.player1

  if (typeof opponent === 'object') {
    return opponent.display_name || opponent.username
  }
  return 'Unknown'
}

const getDoublesOpponents = (game) => {
  if (game.game_type !== 'doubles') return ''

  // Determine which team the user is on
  const userId = user.value?.id
  const isTeam1 = game.team1_player1?.id === userId || game.team1_player2?.id === userId ||
                   game.team1_player1 === userId || game.team1_player2 === userId

  if (isTeam1) {
    return 'vs Team 2'
  } else {
    return 'vs Team 1'
  }
}

const isWin = (game) => {
  const userId = user.value?.id

  if (game.game_type === 'singles') {
    const isPlayer1 = game.player1?.id === userId || game.player1 === userId
    return (isPlayer1 && game.winner === 'player1') || (!isPlayer1 && game.winner === 'player2')
  } else {
    const isTeam1 = game.team1_player1?.id === userId || game.team1_player2?.id === userId ||
                     game.team1_player1 === userId || game.team1_player2 === userId
    return (isTeam1 && game.winner === 'team1') || (!isTeam1 && game.winner === 'team2')
  }
}

const getEloChange = (game) => {
  if (!game.elo_change || game.status !== 'verified') return 0

  const userId = user.value?.id
  const isPlayer1 = game.player1?.id === userId || game.player1 === userId ||
                     game.team1_player1?.id === userId || game.team1_player2?.id === userId ||
                     game.team1_player1 === userId || game.team1_player2 === userId

  // If user is player1/team1 and won, or player2/team2 and lost, ELO goes up
  const won = isWin(game)
  return won ? Math.abs(game.elo_change) : -Math.abs(game.elo_change)
}

const getTrophyIcon = (type) => {
  switch (type) {
    case 'weekly_winner': return 'mdi-trophy'
    case 'monthly_winner': return 'mdi-trophy-variant'
    case 'tournament_winner': return 'mdi-tournament'
    case 'streak': return 'mdi-fire'
    case 'milestone': return 'mdi-star'
    default: return 'mdi-medal'
  }
}

const getTrophyColor = (type) => {
  switch (type) {
    case 'weekly_winner': return 'amber'
    case 'monthly_winner': return 'orange'
    case 'tournament_winner': return 'purple'
    case 'streak': return 'red'
    case 'milestone': return 'blue'
    default: return 'grey'
  }
}

// Watch for route changes
watch(() => route.params.username, (newUsername) => {
  if (authStore.isAuthenticated) {
    fetchProfile()
  }
})

onMounted(async () => {
  // Wait a tick to ensure auth store is fully initialized
  await new Promise(resolve => setTimeout(resolve, 100))

  // Only fetch if we have auth data or a username in the route
  if (authStore.isAuthenticated || route.params.username) {
    fetchProfile()
  } else {
    console.error('Not authenticated and no username provided')
    profileError.value = 'Authentication required'
    profileLoading.value = false
  }
})
</script>