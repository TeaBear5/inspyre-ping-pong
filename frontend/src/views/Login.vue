<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card>
          <v-card-title class="text-h5">Login</v-card-title>
          <v-card-text>
            <!-- Dev mode notice -->
            <v-alert v-if="!firebaseEnabled" type="info" variant="tonal" class="mb-4" density="compact">
              Development mode - use username + password
            </v-alert>

            <v-form @submit.prevent="handleLogin">
              <!-- Unified identifier field -->
              <v-text-field
                v-model="identifier"
                :label="firebaseEnabled ? 'Phone, Email, or Username' : 'Username, Email, or Phone'"
                :placeholder="firebaseEnabled ? '+1234567890 or username' : 'Enter your login'"
                :hint="firebaseEnabled && isPhoneNumber ? 'Phone detected - will send verification code' : ''"
                :prepend-icon="identifierIcon"
                required
                :error-messages="errors.identifier"
                :disabled="otpSent"
                @input="detectInputType"
              ></v-text-field>

              <!-- Password field (shown for non-phone logins) -->
              <v-text-field
                v-if="!isPhoneLogin || !firebaseEnabled"
                v-model="password"
                label="Password"
                type="password"
                prepend-icon="mdi-lock"
                required
                :error-messages="errors.password"
              ></v-text-field>

              <!-- OTP field for phone login -->
              <v-text-field
                v-if="otpSent && isPhoneLogin && firebaseEnabled"
                v-model="otpCode"
                label="Verification Code"
                placeholder="123456"
                prepend-icon="mdi-numeric"
                maxlength="6"
                :error-messages="errors.otp"
              ></v-text-field>

              <!-- reCAPTCHA container (invisible) -->
              <div id="recaptcha-container"></div>

              <v-alert v-if="errors.general" type="error" class="mb-4">
                {{ errors.general }}
              </v-alert>

              <!-- Phone login has two-step flow -->
              <template v-if="isPhoneLogin && firebaseEnabled">
                <v-btn
                  v-if="!otpSent"
                  @click="sendOTP"
                  color="primary"
                  block
                  :loading="loading"
                  class="mt-4"
                >
                  Send Verification Code
                </v-btn>

                <v-btn
                  v-else
                  type="submit"
                  color="primary"
                  block
                  :loading="loading"
                  class="mt-4"
                >
                  Verify & Login
                </v-btn>

                <v-btn
                  v-if="otpSent"
                  @click="resetPhoneLogin"
                  variant="text"
                  block
                  class="mt-2"
                >
                  Use different login
                </v-btn>
              </template>

              <v-btn
                v-else
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
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const firebaseEnabled = computed(() => authStore.firebaseConfigured)
const identifier = ref('')
const password = ref('')
const otpCode = ref('')
const otpSent = ref(false)
const loading = ref(false)
const isPhoneNumber = ref(false)
const errors = ref({
  identifier: '',
  password: '',
  otp: '',
  general: ''
})

// Detect if input looks like a phone number
const detectInputType = () => {
  const value = identifier.value.trim()
  // Check if it starts with + or is all digits (potential phone)
  isPhoneNumber.value = /^\+?\d{7,}$/.test(value.replace(/[\s\-\(\)]/g, ''))
}

// Computed to check if we should use phone login flow
const isPhoneLogin = computed(() => isPhoneNumber.value && firebaseEnabled.value)

// Dynamic icon based on detected input type
const identifierIcon = computed(() => {
  if (isPhoneNumber.value) return 'mdi-phone'
  if (identifier.value.includes('@')) return 'mdi-email'
  return 'mdi-account'
})

onMounted(() => {
  if (firebaseEnabled.value) {
    authStore.initRecaptcha('recaptcha-container')
  }
})

const resetErrors = () => {
  errors.value = {
    identifier: '',
    password: '',
    otp: '',
    general: ''
  }
}

const resetPhoneLogin = () => {
  otpSent.value = false
  otpCode.value = ''
  identifier.value = ''
  isPhoneNumber.value = false
  resetErrors()
  if (firebaseEnabled.value) {
    setTimeout(() => {
      authStore.initRecaptcha('recaptcha-container')
    }, 100)
  }
}

const formatPhoneNumber = () => {
  let phone = identifier.value.trim().replace(/[\s\-\(\)]/g, '')
  if (phone && !phone.startsWith('+')) {
    phone = '+' + phone
  }
  return phone
}

const sendOTP = async () => {
  loading.value = true
  resetErrors()

  const phone = formatPhoneNumber()

  try {
    await authStore.sendPhoneOTP(phone)
    otpSent.value = true
  } catch (error) {
    if (error.code === 'auth/invalid-phone-number') {
      errors.value.identifier = 'Invalid phone number format'
    } else if (error.code === 'auth/too-many-requests') {
      errors.value.general = 'Too many attempts. Please try again later.'
    } else {
      errors.value.general = error.message || 'Failed to send verification code'
    }
  } finally {
    loading.value = false
  }
}

const handleLogin = async () => {
  loading.value = true
  resetErrors()

  try {
    if (isPhoneLogin.value && firebaseEnabled.value) {
      // Phone OTP login
      const phone = formatPhoneNumber()
      await authStore.loginWithPhone(phone, otpCode.value)
    } else {
      // Password-based login (username, email, or phone with password)
      await authStore.login({
        identifier: identifier.value.trim(),
        password: password.value
      })
    }
    router.push('/')
  } catch (error) {
    if (error.code) {
      switch (error.code) {
        case 'auth/invalid-verification-code':
          errors.value.otp = 'Invalid verification code'
          break
        case 'auth/code-expired':
          errors.value.otp = 'Code expired. Please request a new one.'
          break
        case 'auth/user-not-found':
        case 'auth/wrong-password':
          errors.value.general = 'Invalid credentials'
          break
        case 'auth/too-many-requests':
          errors.value.general = 'Too many attempts. Please try again later.'
          break
        default:
          errors.value.general = error.message || 'Login failed'
      }
    } else if (error.error || error.detail) {
      errors.value.general = error.error || error.detail
    } else {
      errors.value.general = 'Login failed. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>
