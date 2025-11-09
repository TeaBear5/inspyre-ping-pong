<template>
  <v-container fluid class="pa-3 pa-md-6">
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4 text-md-h3">Games History</h1>

      <!-- Report New Game Button -->
      <v-btn
        color="primary"
        @click="router.push('/report-game')"
        v-if="authStore.canAccessApp"
        size="small"
        class="d-md-none"
      >
        <v-icon>mdi-plus</v-icon>
      </v-btn>
      <v-btn
        color="primary"
        @click="router.push('/report-game')"
        v-if="authStore.canAccessApp"
        class="d-none d-md-flex"
      >
        <v-icon left>mdi-plus</v-icon>
        Report New Game
      </v-btn>
    </div>

    <!-- Filters -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.status"
              :items="statusOptions"
              label="Status"
              clearable
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.gameType"
              :items="gameTypeOptions"
              label="Game Type"
              clearable
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-autocomplete
              v-model="filters.player"
              :items="players"
              :item-title="player => player.display_name || player.username"
              :item-value="player => player.id"
              label="Player"
              clearable
            ></v-autocomplete>
          </v-col>
          <v-col cols="12" md="3">
            <v-btn color="primary" @click="fetchGames" block>
              <v-icon left>mdi-magnify</v-icon>
              Search
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Games Requiring Action -->
    <v-alert
      v-if="gamesRequiringAction.length > 0"
      type="info"
      variant="outlined"
      class="mb-4"
    >
      <div class="d-flex align-center">
        <div class="flex-grow-1">
          You have {{ gamesRequiringAction.length }} game(s) requiring your verification
        </div>
        <v-btn
          color="info"
          size="small"
          @click="showOnlyPending = !showOnlyPending"
        >
          {{ showOnlyPending ? 'Show All' : 'Show Only Pending' }}
        </v-btn>
      </div>
    </v-alert>

    <!-- Games List -->
    <v-card>
      <!-- Desktop Table -->
      <v-table class="d-none d-md-block">
        <thead>
          <tr>
            <th>Date</th>
            <th>Type</th>
            <th>Players</th>
            <th>Score</th>
            <th>Winner</th>
            <th>Status</th>
            <th>ELO Change</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="game in displayedGames"
            :key="game.id"
            :id="`game-${game.id}`"
            :class="{ 'bg-yellow-lighten-4': highlightedGameId === game.id }"
          >
            <td>{{ formatDate(game.played_at) }}</td>
            <td>
              <v-chip size="small" :color="game.game_type === 'singles' ? 'primary' : 'green'">
                {{ game.game_type }}
              </v-chip>
            </td>
            <td>
              <div v-if="game.game_type === 'singles'">
                <router-link :to="`/profile/${game.player1?.username || game.player1}`" class="text-decoration-none text-primary">
                  {{ getPlayerName(game.player1) }}
                </router-link>
                vs
                <router-link :to="`/profile/${game.player2?.username || game.player2}`" class="text-decoration-none text-primary">
                  {{ getPlayerName(game.player2) }}
                </router-link>
              </div>
              <div v-else>
                <!-- Doubles games hidden for now -->
                <span class="text-caption">Doubles game</span>
              </div>
            </td>
            <td>{{ game.player1_score }} - {{ game.player2_score }}</td>
            <td>
              <div v-if="game.game_type === 'singles'">
                <router-link
                  :to="`/profile/${game.winner === 'player1' ? (game.player1?.username || game.player1) : (game.player2?.username || game.player2)}`"
                  class="text-decoration-none text-primary"
                >
                  {{ game.winner === 'player1' ? getPlayerName(game.player1) : getPlayerName(game.player2) }}
                </router-link>
              </div>
              <div v-else>
                <!-- Doubles winner hidden -->
                <span class="text-caption">Doubles</span>
              </div>
            </td>
            <td>
              <v-chip
                size="small"
                :color="getStatusColor(game.status)"
              >
                {{ game.status }}
              </v-chip>
            </td>
            <td>
              <div v-if="game.status === 'verified' && game.elo_change">
                <v-chip size="small" :color="game.elo_change > 0 ? 'success' : 'error'">
                  {{ game.elo_change > 0 ? '+' : '' }}{{ game.elo_change }}
                </v-chip>
              </div>
              <div v-else>
                -
              </div>
            </td>
            <td>
              <v-btn-group density="compact">
                <v-btn
                  v-if="game.needs_my_verification"
                  color="success"
                  size="small"
                  @click="verifyGame(game)"
                  :loading="loading[game.id]"
                >
                  Verify
                </v-btn>
                <v-btn
                  v-if="game.needs_my_verification"
                  color="error"
                  size="small"
                  @click="openDisputeDialog(game)"
                  :loading="loading[game.id]"
                >
                  Dispute
                </v-btn>
                <v-btn
                  icon
                  size="small"
                  @click="viewGameDetails(game)"
                >
                  <v-icon>mdi-eye</v-icon>
                </v-btn>
                <v-btn
                  icon
                  size="small"
                  @click="toggleComments(game)"
                >
                  <v-icon>mdi-comment</v-icon>
                </v-btn>
              </v-btn-group>
            </td>
          </tr>
        </tbody>
      </v-table>

      <!-- Mobile List -->
      <v-list class="d-md-none pa-0">
        <v-list-item
          v-for="game in displayedGames"
          :key="game.id"
          :id="`game-${game.id}`"
          :class="{ 'bg-yellow-lighten-4': highlightedGameId === game.id }"
          class="px-3 py-3 border-b"
        >
          <div class="d-flex justify-space-between align-start mb-2">
            <div class="text-caption">{{ formatDate(game.played_at) }}</div>
            <v-chip
              size="small"
              :color="getStatusColor(game.status)"
            >
              {{ game.status }}
            </v-chip>
          </div>

          <div class="mb-2">
            <div v-if="game.game_type === 'singles'" class="font-weight-medium">
              <router-link :to="`/profile/${game.player1?.username || game.player1}`" class="text-decoration-none text-primary">
                {{ getPlayerName(game.player1) }}
              </router-link>
              <span class="mx-1">vs</span>
              <router-link :to="`/profile/${game.player2?.username || game.player2}`" class="text-decoration-none text-primary">
                {{ getPlayerName(game.player2) }}
              </router-link>
            </div>
            <div class="text-h6">{{ game.player1_score }} - {{ game.player2_score }}</div>
          </div>

          <div class="d-flex justify-space-between align-center">
            <div>
              <span class="text-caption">Winner: </span>
              <router-link
                v-if="game.game_type === 'singles'"
                :to="`/profile/${game.winner === 'player1' ? (game.player1?.username || game.player1) : (game.player2?.username || game.player2)}`"
                class="text-decoration-none text-primary font-weight-medium"
              >
                {{ game.winner === 'player1' ? getPlayerName(game.player1) : getPlayerName(game.player2) }}
              </router-link>
              <v-chip v-if="game.status === 'verified' && game.elo_change" size="x-small" :color="game.elo_change > 0 ? 'success' : 'error'" class="ml-2">
                {{ game.elo_change > 0 ? '+' : '' }}{{ game.elo_change }}
              </v-chip>
            </div>

            <div>
              <v-btn
                v-if="game.needs_my_verification"
                color="success"
                size="x-small"
                @click="verifyGame(game)"
                :loading="loading[game.id]"
                class="mr-1"
              >
                Verify
              </v-btn>
              <v-btn
                v-if="game.needs_my_verification"
                color="error"
                size="x-small"
                @click="openDisputeDialog(game)"
                :loading="loading[game.id]"
                class="mr-1"
              >
                Dispute
              </v-btn>
              <v-btn
                icon
                size="x-small"
                @click="viewGameDetails(game)"
              >
                <v-icon size="small">mdi-eye</v-icon>
              </v-btn>
            </div>
          </div>
        </v-list-item>
      </v-list>

      <v-card-text v-if="games.length === 0" class="text-center">
        <p>No games found</p>
      </v-card-text>

      <!-- Pagination -->
      <v-card-actions v-if="totalPages > 1">
        <v-pagination
          v-model="currentPage"
          :length="totalPages"
          @update:modelValue="fetchGames"
        ></v-pagination>
      </v-card-actions>
    </v-card>

    <!-- Dispute Dialog -->
    <v-dialog v-model="showDisputeDialog" max-width="500">
      <v-card>
        <v-card-title>Dispute Game</v-card-title>
        <v-card-text>
          <v-textarea
            v-model="disputeReason"
            label="Reason for dispute (required)"
            rows="3"
            auto-grow
            :rules="[v => !!v || 'Reason is required']"
          ></v-textarea>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showDisputeDialog = false">Cancel</v-btn>
          <v-btn
            color="error"
            @click="disputeGame"
            :disabled="!disputeReason"
            :loading="disputeLoading"
          >
            Submit Dispute
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Game Details Dialog -->
    <v-dialog v-model="showDetailsDialog" max-width="800">
      <v-card v-if="selectedGame">
        <v-card-title>Game Details</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <div class="text-subtitle-2">Game Type</div>
              <div>{{ selectedGame.game_type }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-subtitle-2">Status</div>
              <v-chip :color="getStatusColor(selectedGame.status)">
                {{ selectedGame.status }}
              </v-chip>
            </v-col>
          </v-row>

          <v-row class="mt-2">
            <v-col cols="12" md="6">
              <div class="text-subtitle-2">Date Played</div>
              <div>{{ formatDateTime(selectedGame.played_at) }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-subtitle-2">Reported By</div>
              <div>{{ getPlayerName(selectedGame.reported_by) }}</div>
            </v-col>
          </v-row>

          <v-row class="mt-2" v-if="selectedGame.game_type === 'singles'">
            <v-col cols="12" md="6">
              <div class="text-subtitle-2">Player 1</div>
              <div>{{ getPlayerName(selectedGame.player1) }}</div>
              <div class="text-caption">Score: {{ selectedGame.player1_score }}</div>
              <div class="text-caption" v-if="selectedGame.player1_elo_before">
                ELO: {{ selectedGame.player1_elo_before }} → {{ selectedGame.player1_elo_after }}
              </div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-subtitle-2">Player 2</div>
              <div>{{ getPlayerName(selectedGame.player2) }}</div>
              <div class="text-caption">Score: {{ selectedGame.player2_score }}</div>
              <div class="text-caption" v-if="selectedGame.player2_elo_before">
                ELO: {{ selectedGame.player2_elo_before }} → {{ selectedGame.player2_elo_after }}
              </div>
            </v-col>
          </v-row>

          <v-row class="mt-2" v-if="selectedGame.notes">
            <v-col cols="12">
              <div class="text-subtitle-2">Notes</div>
              <div>{{ selectedGame.notes }}</div>
            </v-col>
          </v-row>

          <v-row class="mt-2" v-if="selectedGame.dispute_reason">
            <v-col cols="12">
              <v-alert type="warning" variant="outlined">
                <div class="text-subtitle-2">Dispute Reason</div>
                <div>{{ selectedGame.dispute_reason }}</div>
                <div class="text-caption mt-2">
                  Disputed by: {{ getPlayerName(selectedGame.disputed_by) }}
                </div>
              </v-alert>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showDetailsDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Comments Section -->
    <v-dialog v-model="showCommentsDialog" max-width="600">
      <v-card v-if="selectedGame">
        <v-card-title>Game Comments</v-card-title>
        <v-card-text>
          <!-- Comments List -->
          <div v-if="comments.length > 0" class="mb-4">
            <v-card
              v-for="comment in comments"
              :key="comment.id"
              variant="outlined"
              class="mb-2"
            >
              <v-card-text>
                <div class="d-flex justify-space-between">
                  <div class="font-weight-bold">
                    {{ getPlayerName(comment.author) }}
                  </div>
                  <div class="text-caption">
                    {{ formatDateTime(comment.created_at) }}
                  </div>
                </div>
                <div class="mt-2">{{ comment.content }}</div>
              </v-card-text>
            </v-card>
          </div>
          <div v-else class="text-center text-grey mb-4">
            No comments yet
          </div>

          <!-- Add Comment -->
          <v-textarea
            v-model="newComment"
            label="Add a comment"
            rows="2"
            auto-grow
            variant="outlined"
          ></v-textarea>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showCommentsDialog = false">Close</v-btn>
          <v-btn
            color="primary"
            @click="postComment"
            :disabled="!newComment"
            :loading="commentLoading"
          >
            Post Comment
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Data
const games = ref([])
const players = ref([])
const loading = ref({})
const currentPage = ref(1)
const totalPages = ref(1)
const showOnlyPending = ref(false)
const highlightedGameId = ref(null)

// Filters
const filters = ref({
  status: null,
  gameType: null,
  player: null
})

const statusOptions = [
  { title: 'Pending', value: 'pending' },
  { title: 'Verified', value: 'verified' },
  { title: 'Disputed', value: 'disputed' },
  { title: 'Resolved', value: 'resolved' }
]

const gameTypeOptions = [
  { title: 'Singles', value: 'singles' }
  // Doubles option temporarily hidden
  // { title: 'Doubles', value: 'doubles' }
]

// Dialogs
const showDisputeDialog = ref(false)
const showDetailsDialog = ref(false)
const showCommentsDialog = ref(false)
const selectedGame = ref(null)
const disputeReason = ref('')
const disputeLoading = ref(false)
const comments = ref([])
const newComment = ref('')
const commentLoading = ref(false)

// Computed
const gamesRequiringAction = computed(() => {
  return games.value.filter(game => game.needs_my_verification)
})

const displayedGames = computed(() => {
  if (showOnlyPending.value) {
    return gamesRequiringAction.value
  }
  return games.value
})

// Methods
const fetchGames = async () => {
  try {
    const params = {
      page: currentPage.value
    }

    if (filters.value.status) {
      params.status = filters.value.status
    }
    if (filters.value.gameType) {
      params.game_type = filters.value.gameType
    }
    if (filters.value.player) {
      params.player = filters.value.player
    }

    const response = await axios.get(`${API_URL}/games/`, { params })
    games.value = response.data.results || response.data
    totalPages.value = Math.ceil((response.data.count || games.value.length) / 10)
  } catch (error) {
    console.error('Failed to fetch games:', error)
    games.value = []
  }
}

const fetchPlayers = async () => {
  try {
    const response = await axios.get(`${API_URL}/players/approved/`)
    players.value = response.data.results || response.data
  } catch (error) {
    console.error('Failed to fetch players:', error)
  }
}

const getPlayerName = (player) => {
  if (!player) return 'Unknown'
  if (typeof player === 'object') {
    return player.display_name || player.username
  }
  // If it's an ID, find the player
  const foundPlayer = players.value.find(p => p.id === player)
  return foundPlayer ? (foundPlayer.display_name || foundPlayer.username) : 'Unknown'
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

const formatDateTime = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString()
}

const getStatusColor = (status) => {
  switch (status) {
    case 'pending': return 'warning'
    case 'verified': return 'success'
    case 'disputed': return 'error'
    case 'resolved': return 'info'
    default: return 'grey'
  }
}

const verifyGame = async (game) => {
  loading.value[game.id] = true
  try {
    await axios.post(`${API_URL}/games/${game.id}/verify/`, {
      action: 'verify'
    })
    await fetchGames()
  } catch (error) {
    console.error('Failed to verify game:', error)
    alert('Failed to verify game. Please try again.')
  } finally {
    loading.value[game.id] = false
  }
}

const openDisputeDialog = (game) => {
  selectedGame.value = game
  disputeReason.value = ''
  showDisputeDialog.value = true
}

const disputeGame = async () => {
  if (!selectedGame.value || !disputeReason.value) return

  disputeLoading.value = true
  try {
    await axios.post(`${API_URL}/games/${selectedGame.value.id}/verify/`, {
      action: 'dispute',
      reason: disputeReason.value
    })
    showDisputeDialog.value = false
    await fetchGames()
  } catch (error) {
    console.error('Failed to dispute game:', error)
    alert('Failed to dispute game. Please try again.')
  } finally {
    disputeLoading.value = false
  }
}

const viewGameDetails = (game) => {
  selectedGame.value = game
  showDetailsDialog.value = true
}

const toggleComments = async (game) => {
  selectedGame.value = game
  comments.value = []
  newComment.value = ''
  showCommentsDialog.value = true

  // Fetch comments
  try {
    const response = await axios.get(`${API_URL}/games/${game.id}/comments/`)
    comments.value = response.data.results || response.data
  } catch (error) {
    console.error('Failed to fetch comments:', error)
  }
}

const postComment = async () => {
  if (!newComment.value || !selectedGame.value) return

  commentLoading.value = true
  try {
    await axios.post(`${API_URL}/games/${selectedGame.value.id}/comments/`, {
      content: newComment.value
    })

    // Refresh comments
    const response = await axios.get(`${API_URL}/games/${selectedGame.value.id}/comments/`)
    comments.value = response.data.results || response.data
    newComment.value = ''
  } catch (error) {
    console.error('Failed to post comment:', error)
    alert('Failed to post comment. Please try again.')
  } finally {
    commentLoading.value = false
  }
}

// Watch for route query changes
watch(() => route.query.highlight, (newHighlight) => {
  if (newHighlight) {
    highlightedGameId.value = newHighlight
    // Scroll to the game after a short delay
    setTimeout(() => {
      const element = document.getElementById(`game-${newHighlight}`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }, 500)
  }
})

onMounted(() => {
  // Check for highlighted game from notification
  if (route.query.highlight) {
    highlightedGameId.value = route.query.highlight
    // Don't filter, show all games so the highlighted one is visible
    filters.value.status = null
    // Scroll to the game after data loads
    setTimeout(() => {
      const element = document.getElementById(`game-${route.query.highlight}`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }, 1000)
  }

  fetchGames()
  fetchPlayers()
})
</script>