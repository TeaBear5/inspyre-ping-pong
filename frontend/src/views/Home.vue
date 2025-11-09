<template>
  <v-container fluid class="pa-3 pa-md-6">
    <v-row>
      <v-col cols="12">
        <h1 :class="$vuetify.display.mobile ? 'text-h3' : 'text-h2'" class="text-center mb-4 mb-md-6 text-primary">
          Welcome to Inspyre Ping Pong
        </h1>
        <p :class="$vuetify.display.mobile ? 'text-subtitle-1' : 'text-h6'" class="text-center">
          Track your games, improve your ELO, compete in tournaments!
        </p>
      </v-col>
    </v-row>

    <v-row v-if="!authStore.isAuthenticated" class="mt-6">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>New Player?</v-card-title>
          <v-card-text>
            Join our community and start tracking your ping pong journey.
          </v-card-text>
          <v-card-actions>
            <v-btn color="primary" to="/register">Register Now</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Existing Player?</v-card-title>
          <v-card-text>
            Login to report games and check your ranking.
          </v-card-text>
          <v-card-actions>
            <v-btn color="secondary" to="/login">Login</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-row v-else class="mt-6">
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>Quick Actions</v-card-title>
          <v-list>
            <v-list-item to="/report-game">
              <v-list-item-title>Report a Game</v-list-item-title>
            </v-list-item>
            <v-list-item to="/rankings">
              <v-list-item-title>View Rankings</v-list-item-title>
            </v-list-item>
            <v-list-item to="/games">
              <v-list-item-title>Recent Games</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card>
          <v-card-title>Your Stats</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="4" class="text-center">
                <div class="text-h4 text-primary">{{ playerProfile?.singles_elo || 1200 }}</div>
                <div class="text-caption">ELO Rating</div>
              </v-col>
              <v-col cols="4" class="text-center">
                <div class="text-h4 text-success">{{ playerProfile?.singles_win_rate || 0 }}%</div>
                <div class="text-caption">Win Rate</div>
              </v-col>
              <v-col cols="4" class="text-center">
                <div class="text-h4 text-info">{{ playerProfile?.singles_games_played || 0 }}</div>
                <div class="text-caption">Games Played</div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const authStore = useAuthStore()
const playerProfile = ref(null)
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

onMounted(async () => {
  if (authStore.isAuthenticated) {
    try {
      const response = await axios.get(`${API_URL}/profiles/me/`)
      playerProfile.value = response.data
    } catch (error) {
      console.error('Failed to fetch profile:', error)
    }
  }
})
</script>