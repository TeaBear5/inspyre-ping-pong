<template>
  <v-container>
    <h1 class="text-h3 mb-6">User Management</h1>

    <v-alert v-if="!isAdmin" type="warning" prominent>
      You must be an admin to access this page.
    </v-alert>

    <v-card v-if="isAdmin">
      <v-card-title>
        <v-row>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="search"
              append-icon="mdi-magnify"
              label="Search users"
              single-line
              hide-details
              density="compact"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="6" class="text-right">
            <v-btn color="primary" @click="refreshUsers">
              <v-icon left>mdi-refresh</v-icon>
              Refresh
            </v-btn>
          </v-col>
        </v-row>
      </v-card-title>

      <v-table>
        <thead>
          <tr>
            <th>Username</th>
            <th>Display Name</th>
            <th>Phone</th>
            <th>Status</th>
            <th>Joined</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.display_name }}</td>
            <td>{{ user.phone_number }}</td>
            <td>
              <v-chip-group>
                <v-chip
                  :color="user.phone_verified ? 'success' : 'warning'"
                  size="small"
                >
                  {{ user.phone_verified ? '✓ Verified' : '⚠ Unverified' }}
                </v-chip>
                <v-chip
                  :color="user.is_approved ? 'success' : 'error'"
                  size="small"
                >
                  {{ user.is_approved ? '✓ Approved' : '✗ Pending' }}
                </v-chip>
                <v-chip
                  v-if="user.is_staff"
                  color="blue"
                  size="small"
                >
                  Admin
                </v-chip>
              </v-chip-group>
            </td>
            <td>{{ formatDate(user.date_joined) }}</td>
            <td>
              <v-btn-group density="compact">
                <v-btn
                  v-if="!user.phone_verified"
                  color="primary"
                  size="small"
                  @click="verifyPhone(user)"
                  :loading="loading[user.id]"
                >
                  Verify Phone
                </v-btn>
                <v-btn
                  v-if="!user.is_approved"
                  color="success"
                  size="small"
                  @click="approveUser(user)"
                  :loading="loading[user.id]"
                >
                  Approve
                </v-btn>
                <v-btn
                  v-if="!user.phone_verified || !user.is_approved"
                  color="info"
                  size="small"
                  @click="approveAndVerify(user)"
                  :loading="loading[user.id]"
                >
                  Approve & Verify
                </v-btn>
                <v-btn
                  v-if="user.is_approved"
                  color="warning"
                  size="small"
                  @click="unapproveUser(user)"
                  :loading="loading[user.id]"
                >
                  Revoke
                </v-btn>
              </v-btn-group>
            </td>
          </tr>
        </tbody>
      </v-table>

      <v-card-text v-if="users.length === 0" class="text-center">
        <p>No users found</p>
      </v-card-text>
    </v-card>

    <!-- Status Summary -->
    <v-row class="mt-6" v-if="isAdmin">
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text class="text-center">
            <div class="text-h3">{{ users.length }}</div>
            <div>Total Users</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text class="text-center">
            <div class="text-h3">{{ verifiedCount }}</div>
            <div>Phone Verified</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text class="text-center">
            <div class="text-h3">{{ approvedCount }}</div>
            <div>Approved</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text class="text-center">
            <div class="text-h3">{{ pendingCount }}</div>
            <div>Pending Approval</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const authStore = useAuthStore()
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const users = ref([])
const search = ref('')
const loading = ref({})

const isAdmin = computed(() => authStore.user?.is_staff || authStore.user?.is_superuser)

const filteredUsers = computed(() => {
  if (!search.value) return users.value

  const searchLower = search.value.toLowerCase()
  return users.value.filter(user =>
    user.username.toLowerCase().includes(searchLower) ||
    user.display_name.toLowerCase().includes(searchLower) ||
    user.phone_number.includes(searchLower)
  )
})

const verifiedCount = computed(() => users.value.filter(u => u.phone_verified).length)
const approvedCount = computed(() => users.value.filter(u => u.is_approved).length)
const pendingCount = computed(() => users.value.filter(u => !u.is_approved).length)

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

const refreshUsers = async () => {
  try {
    const response = await axios.get(`${API_URL}/admin/users/`)
    users.value = response.data
  } catch (error) {
    console.error('Failed to fetch users:', error)
    users.value = []
  }
}

const updateUser = async (user, updates) => {
  loading.value[user.id] = true
  try {
    const response = await axios.patch(`${API_URL}/admin/users/${user.id}/`, updates)

    // Update the user in our local list
    const index = users.value.findIndex(u => u.id === user.id)
    if (index !== -1) {
      users.value[index] = { ...users.value[index], ...response.data }
    }

    return true
  } catch (error) {
    console.error('Failed to update user:', error)
    alert('Failed to update user. Please try again.')
    return false
  } finally {
    loading.value[user.id] = false
  }
}

const verifyPhone = async (user) => {
  if (await updateUser(user, { phone_verified: true })) {
    console.log(`Phone verified for ${user.username}`)
  }
}

const approveUser = async (user) => {
  if (await updateUser(user, { is_approved: true })) {
    console.log(`User ${user.username} approved`)
  }
}

const approveAndVerify = async (user) => {
  if (await updateUser(user, { is_approved: true, phone_verified: true })) {
    console.log(`User ${user.username} approved and verified`)
  }
}

const unapproveUser = async (user) => {
  if (confirm(`Are you sure you want to revoke approval for ${user.username}?`)) {
    if (await updateUser(user, { is_approved: false })) {
      console.log(`Approval revoked for ${user.username}`)
    }
  }
}

onMounted(() => {
  if (isAdmin.value) {
    refreshUsers()
  }
})
</script>