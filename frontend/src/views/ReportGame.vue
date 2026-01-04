<template>
  <v-container fluid class="pa-3 pa-md-6">
    <h1 class="text-h4 text-md-h3 mb-4 mb-md-6">Report Game</h1>

    <v-alert v-if="!authStore.canAccessApp" type="warning" prominent>
      You must have a verified phone number and be approved to report games.
    </v-alert>

    <v-card v-if="authStore.canAccessApp">
      <v-form @submit.prevent="submitGame" ref="form">
        <v-card-text>
          <!-- Game Type - Singles Only (Doubles temporarily disabled) -->
          <!-- Hidden field to always set singles -->
          <input type="hidden" v-model="gameData.game_type" value="singles" />

          <!-- Singles Game Fields -->
          <v-row>
            <v-col cols="12" md="6">
              <v-autocomplete
                v-model="gameData.player1"
                :items="players"
                :item-title="player => player.display_name || player.username"
                :item-value="player => player.id"
                label="Player 1"
                :rules="[rules.required]"
                clearable
                :disabled="lockPlayer1"
              ></v-autocomplete>
            </v-col>
            <v-col cols="12" md="6">
              <v-autocomplete
                v-model="gameData.player2"
                :items="filteredOpponents"
                :item-title="player => player.display_name || player.username"
                :item-value="player => player.id"
                label="Player 2 (Opponent)"
                :rules="[rules.required]"
                clearable
              ></v-autocomplete>
            </v-col>
          </v-row>

          <!-- Doubles Game Fields - Temporarily Disabled -->
          <!-- Doubles functionality is hidden but preserved in code -->

          <!-- Score Fields -->
          <v-row>
            <v-col cols="12">
              <div class="text-subtitle-1 mb-2">Score</div>
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model.number="gameData.player1_score"
                :label="scoreLabel1"
                type="number"
                :rules="[rules.required, rules.score]"
                min="0"
                max="30"
              ></v-text-field>
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model.number="gameData.player2_score"
                :label="scoreLabel2"
                type="number"
                :rules="[rules.required, rules.score]"
                min="0"
                max="30"
              ></v-text-field>
            </v-col>
          </v-row>

          <!-- Winner Selection -->
          <v-row>
            <v-col cols="12">
              <v-radio-group v-model="gameData.winner" inline>
                <template v-slot:label>
                  <div class="text-subtitle-1 mb-2">Winner</div>
                </template>
                <v-radio
                  :label="winnerLabel1"
                  value="player1"
                ></v-radio>
                <v-radio
                  :label="winnerLabel2"
                  value="player2"
                ></v-radio>
              </v-radio-group>
            </v-col>
          </v-row>

          <!-- Date and Time -->
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="gameDate"
                label="Game Date"
                type="date"
                :rules="[rules.required]"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="gameTime"
                label="Game Time"
                type="time"
                :rules="[rules.required]"
              ></v-text-field>
            </v-col>
          </v-row>

          <!-- Notes -->
          <v-row>
            <v-col cols="12">
              <v-textarea
                v-model="gameData.notes"
                label="Notes (optional)"
                rows="3"
                auto-grow
              ></v-textarea>
            </v-col>
          </v-row>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            type="submit"
            :loading="loading"
            :disabled="!isFormValid"
          >
            Submit Game
          </v-btn>
        </v-card-actions>
      </v-form>
    </v-card>

    <!-- Success Dialog -->
    <v-dialog v-model="showSuccess" max-width="500">
      <v-card>
        <v-card-title>Game Reported Successfully!</v-card-title>
        <v-card-text>
          Your game has been submitted and is pending verification from
          {{ gameData.game_type === 'singles' ? 'your opponent' : 'the other team' }}.
          You'll be notified once it's verified.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="resetForm">Report Another</v-btn>
          <v-btn color="success" @click="router.push('/games')">View Games</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Error Dialog -->
    <v-dialog v-model="showError" max-width="500">
      <v-card>
        <v-card-title>Error Reporting Game</v-card-title>
        <v-card-text>
          {{ errorMessage }}
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="showError = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()
import { API_URL } from '../config'

// Form refs
const form = ref(null)
const loading = ref(false)
const showSuccess = ref(false)
const showError = ref(false)
const errorMessage = ref('')

// Players list
const players = ref([])

// Game data
const gameData = ref({
  game_type: 'singles',
  player1: null,
  player2: null,
  team1_player1: null,
  team1_player2: null,
  team2_player1: null,
  team2_player2: null,
  player1_score: null,
  player2_score: null,
  winner: null,
  notes: ''
})

// Date and time (separate for better UX)
const gameDate = ref(new Date().toISOString().split('T')[0])
const gameTime = ref(new Date().toTimeString().slice(0, 5))

// Auto-select current user as player1
const lockPlayer1 = computed(() => {
  // Always set current user as player1 or team1_player1
  return true
})

// Validation rules
const rules = {
  required: v => !!v || 'This field is required',
  score: v => (v >= 0 && v <= 30) || 'Score must be between 0 and 30'
}

// Computed properties for dynamic labels
const scoreLabel1 = computed(() => {
  if (gameData.value.game_type === 'singles') {
    const player = players.value.find(p => p.id === gameData.value.player1)
    return player ? `${player.display_name || player.username} Score` : 'Player 1 Score'
  }
  return 'Team 1 Score'
})

const scoreLabel2 = computed(() => {
  if (gameData.value.game_type === 'singles') {
    const player = players.value.find(p => p.id === gameData.value.player2)
    return player ? `${player.display_name || player.username} Score` : 'Player 2 Score'
  }
  return 'Team 2 Score'
})

const winnerLabel1 = computed(() => {
  const player = players.value.find(p => p.id === gameData.value.player1)
  return player ? (player.display_name || player.username) : 'Player 1'
})

const winnerLabel2 = computed(() => {
  const player = players.value.find(p => p.id === gameData.value.player2)
  return player ? (player.display_name || player.username) : 'Player 2'
})

// Filtered lists to prevent duplicate selections
const filteredOpponents = computed(() => {
  return players.value.filter(p => p.id !== gameData.value.player1)
})

const filteredTeam1Player2 = computed(() => {
  return players.value.filter(p => p.id !== gameData.value.team1_player1)
})

const filteredTeam2Players = computed(() => {
  const usedIds = [gameData.value.team1_player1, gameData.value.team1_player2]
  return players.value.filter(p => !usedIds.includes(p.id))
})

const filteredTeam2Player2 = computed(() => {
  const usedIds = [gameData.value.team1_player1, gameData.value.team1_player2, gameData.value.team2_player1]
  return players.value.filter(p => !usedIds.includes(p.id))
})

// Check if form is valid
const isFormValid = computed(() => {
  if (gameData.value.game_type === 'singles') {
    return gameData.value.player1 && gameData.value.player2 &&
           gameData.value.player1_score !== null && gameData.value.player2_score !== null &&
           gameData.value.winner && gameDate.value && gameTime.value
  } else {
    return gameData.value.team1_player1 && gameData.value.team1_player2 &&
           gameData.value.team2_player1 && gameData.value.team2_player2 &&
           gameData.value.player1_score !== null && gameData.value.player2_score !== null &&
           gameData.value.winner && gameDate.value && gameTime.value
  }
})

// Fetch players list
const fetchPlayers = async () => {
  try {
    const response = await axios.get(`${API_URL}/players/approved/`)
    players.value = response.data.results || response.data

    // Auto-select current user as player1/team1_player1
    const currentUser = authStore.user
    if (currentUser) {
      const currentUserId = players.value.find(p => p.username === currentUser.username)?.id
      if (currentUserId) {
        gameData.value.player1 = currentUserId
        gameData.value.team1_player1 = currentUserId
      }
    }
  } catch (error) {
    console.error('Failed to fetch players:', error)
  }
}

// Submit game
const submitGame = async () => {
  const valid = await form.value.validate()
  if (!valid.valid) return

  loading.value = true
  try {
    // Combine date and time
    const played_at = `${gameDate.value}T${gameTime.value}:00`

    const payload = {
      game_type: gameData.value.game_type,
      player1_score: gameData.value.player1_score,
      player2_score: gameData.value.player2_score,
      winner: gameData.value.winner,
      played_at: played_at,
      notes: gameData.value.notes
    }

    if (gameData.value.game_type === 'singles') {
      payload.player1 = gameData.value.player1
      payload.player2 = gameData.value.player2
    } else {
      payload.team1_player1 = gameData.value.team1_player1
      payload.team1_player2 = gameData.value.team1_player2
      payload.team2_player1 = gameData.value.team2_player1
      payload.team2_player2 = gameData.value.team2_player2
    }

    await axios.post(`${API_URL}/games/`, payload)
    showSuccess.value = true
  } catch (error) {
    console.error('Failed to submit game:', error)
    errorMessage.value = error.response?.data?.detail ||
                        error.response?.data?.error ||
                        JSON.stringify(error.response?.data) ||
                        'Failed to submit game. Please try again.'
    showError.value = true
  } finally {
    loading.value = false
  }
}

// Reset form
const resetForm = () => {
  showSuccess.value = false
  gameData.value = {
    game_type: 'singles',
    player1: null,
    player2: null,
    team1_player1: null,
    team1_player2: null,
    team2_player1: null,
    team2_player2: null,
    player1_score: null,
    player2_score: null,
    winner: null,
    notes: ''
  }
  gameDate.value = new Date().toISOString().split('T')[0]
  gameTime.value = new Date().toTimeString().slice(0, 5)

  // Re-select current user
  const currentUser = authStore.user
  if (currentUser) {
    const currentUserId = players.value.find(p => p.username === currentUser.username)?.id
    if (currentUserId) {
      gameData.value.player1 = currentUserId
      gameData.value.team1_player1 = currentUserId
    }
  }
}

onMounted(() => {
  fetchPlayers()
})
</script>