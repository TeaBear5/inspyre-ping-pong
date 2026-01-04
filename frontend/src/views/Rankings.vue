<template>
  <v-container fluid class="pa-3 pa-md-6">
    <h1 class="text-h4 text-md-h3 mb-4 mb-md-6">Rankings</h1>

    <v-tabs v-model="tab" class="mb-6">
      <v-tab value="singles">ELO Rankings</v-tab>
      <!-- Doubles tab hidden temporarily -->
      <v-tab value="weekly">Weekly Points</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <!-- Singles Rankings -->
      <v-window-item value="singles">
        <v-card>
          <v-card-title class="text-h6 text-md-h5">ELO Rankings</v-card-title>

          <!-- Desktop Table -->
          <v-table class="d-none d-md-block">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Player</th>
                <th>ELO</th>
                <th>Games</th>
                <th>Win Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(player, index) in rankings.singles_rankings" :key="player.user.id">
                <td>{{ index + 1 }}</td>
                <td>
                  <router-link :to="`/profile/${player.user.username}`" class="text-decoration-none text-primary">
                    {{ player.user.display_name }}
                  </router-link>
                </td>
                <td><strong>{{ player.singles_elo }}</strong></td>
                <td>{{ player.singles_games_played }}</td>
                <td>{{ Math.round(player.singles_win_rate) }}%</td>
              </tr>
            </tbody>
          </v-table>

          <!-- Mobile List -->
          <v-list class="d-md-none">
            <v-list-item
              v-for="(player, index) in rankings.singles_rankings"
              :key="player.user.id"
              class="px-3"
            >
              <template v-slot:prepend>
                <div class="text-h6 font-weight-bold mr-3">#{{ index + 1 }}</div>
              </template>

              <v-list-item-title>
                <router-link :to="`/profile/${player.user.username}`" class="text-decoration-none text-primary">
                  {{ player.user.display_name }}
                </router-link>
              </v-list-item-title>

              <v-list-item-subtitle>
                <span class="font-weight-bold">{{ player.singles_elo }} ELO</span> •
                {{ player.singles_games_played }} games •
                {{ Math.round(player.singles_win_rate) }}% win rate
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
      </v-window-item>

      <!-- Doubles Rankings - Temporarily Hidden -->
      <!-- Doubles functionality preserved in code but hidden from UI -->

      <!-- Weekly Leaderboard -->
      <v-window-item value="weekly">
        <v-card>
          <v-card-title class="text-h6 text-md-h5">Weekly Points Leaderboard</v-card-title>

          <!-- Desktop Table -->
          <v-table class="d-none d-md-block">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Player</th>
                <th>Points</th>
                <th>Games</th>
                <th>Wins</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entry, index) in rankings.weekly_leaderboard" :key="entry.user.id">
                <td>{{ index + 1 }}</td>
                <td>
                  <router-link :to="`/profile/${entry.user.username}`" class="text-decoration-none text-primary">
                    {{ entry.user.display_name }}
                  </router-link>
                </td>
                <td><strong>{{ entry.weekly_points }}</strong></td>
                <td>{{ entry.singles_games_played }}</td>
                <td>{{ entry.singles_wins }}</td>
              </tr>
            </tbody>
          </v-table>

          <!-- Mobile List -->
          <v-list class="d-md-none">
            <v-list-item
              v-for="(entry, index) in rankings.weekly_leaderboard"
              :key="entry.user.id"
              class="px-3"
            >
              <template v-slot:prepend>
                <div class="text-h6 font-weight-bold mr-3">#{{ index + 1 }}</div>
              </template>

              <v-list-item-title>
                <router-link :to="`/profile/${entry.user.username}`" class="text-decoration-none text-primary">
                  {{ entry.user.display_name }}
                </router-link>
              </v-list-item-title>

              <v-list-item-subtitle>
                <span class="font-weight-bold">{{ entry.weekly_points }} points</span> •
                {{ entry.singles_wins }}/{{ entry.singles_games_played }} wins
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
      </v-window-item>
    </v-window>

    <!-- Recent Games -->
    <v-card class="mt-6">
      <v-card-title>Recent Games</v-card-title>
      <v-list>
        <v-list-item v-for="game in rankings.recent_games" :key="game.id">
          <div>
            <v-list-item-title>
              {{ game.player1?.display_name }} vs {{ game.player2?.display_name }}
            </v-list-item-title>
            <v-list-item-subtitle>
              Score: {{ game.player1_score }} - {{ game.player2_score }} |
              ELO Change: ±{{ game.elo_change }}
            </v-list-item-subtitle>
          </div>
        </v-list-item>
      </v-list>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const tab = ref('singles')
const rankings = ref({
  singles_rankings: [],
  doubles_rankings: [],
  weekly_leaderboard: [],
  recent_games: [],
  all_players: []
})

import { API_URL } from '../config'

onMounted(async () => {
  try {
    const response = await axios.get(`${API_URL}/rankings/`)
    rankings.value = response.data

    // If no players have enough games for rankings, show all players who have played
    if (rankings.value.singles_rankings.length === 0 && rankings.value.all_players.length > 0) {
      rankings.value.singles_rankings = rankings.value.all_players.filter(p => p.singles_games_played > 0)
    }
    if (rankings.value.doubles_rankings.length === 0 && rankings.value.all_players.length > 0) {
      rankings.value.doubles_rankings = rankings.value.all_players.filter(p => p.doubles_games_played > 0)
    }
  } catch (error) {
    console.error('Failed to fetch rankings:', error)
  }
})
</script>