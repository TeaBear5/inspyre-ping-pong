<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card>
          <v-card-title class="text-h5">Login</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="handleLogin">
              <v-text-field
                v-model="phoneNumber"
                label="Phone Number"
                placeholder="+1234567890"
                prepend-icon="mdi-phone"
                required
                :error-messages="errors.phone"
              ></v-text-field>

              <v-text-field
                v-model="password"
                label="Password"
                type="password"
                prepend-icon="mdi-lock"
                required
                :error-messages="errors.password"
              ></v-text-field>

              <v-alert v-if="errors.general" type="error" class="mb-4">
                {{ errors.general }}
              </v-alert>

              <v-btn
                type="submit"
                color="primary"
                block
                :loading="loading"
                class="mt-4"
              >
                Login
              </v-btn>
            </v-form>

            <v-divider class="my-4"></v-divider>

            <p class="text-center">
              Don't have an account?
              <router-link to="/register">Register here</router-link>
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const phoneNumber = ref('')
const password = ref('')
const loading = ref(false)
const errors = ref({
  phone: '',
  password: '',
  general: ''
})

const handleLogin = async () => {
  loading.value = true
  errors.value = { phone: '', password: '', general: '' }

  try {
    await authStore.login({
      phone_number: phoneNumber.value,
      password: password.value
    })
    router.push('/')
  } catch (error) {
    if (error.response?.data) {
      const data = error.response.data
      errors.value.phone = data.phone_number?.[0] || ''
      errors.value.password = data.password?.[0] || ''
      errors.value.general = data.non_field_errors?.[0] || data.detail || 'Login failed'
    } else {
      errors.value.general = 'An error occurred. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>