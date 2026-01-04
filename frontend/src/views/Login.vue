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

            <!-- Login Method Tabs (only show if Firebase is configured) -->
            <v-tabs v-if="firebaseEnabled" v-model="loginMethod" grow class="mb-4">
              <v-tab value="username">Username</v-tab>
              <v-tab value="phone">Phone</v-tab>
              <v-tab value="email">Email</v-tab>
            </v-tabs>

            <v-form @submit.prevent="handleLogin">
              <!-- Username/Password Login (default and dev mode) -->
              <template v-if="loginMethod === 'username' || !firebaseEnabled">
                <v-text-field
                  v-model="identifier"
                  label="Username, Email, or Phone"
                  prepend-icon="mdi-account"
                  required
                  :error-messages="errors.identifier"
                ></v-text-field>

                <v-text-field
                  v-model="password"
                  label="Password"
                  type="password"
                  prepend-icon="mdi-lock"
                  required
                  :error-messages="errors.password"
                ></v-text-field>
              </template>

              <!-- Phone Login (Firebase) -->
              <template v-else-if="loginMethod === 'phone' && firebaseEnabled">
                <v-text-field
                  v-model="phoneNumber"
                  label="Phone Number"
                  placeholder="+1234567890"
                  hint="Include country code (e.g., +1 for US)"
                  prepend-icon="mdi-phone"
                  required
                  :error-messages="errors.phone"
                  :disabled="otpSent"
                ></v-text-field>

                <v-text-field
                  v-if="otpSent"
                  v-model="otpCode"
                  label="Verification Code"
                  placeholder="123456"
                  prepend-icon="mdi-numeric"
                  maxlength="6"
                  :error-messages="errors.otp"
                ></v-text-field>

                <!-- reCAPTCHA container (invisible) -->
                <div id="recaptcha-container"></div>
              </template>

              <!-- Email Login (Firebase) -->
              <template v-else-if="loginMethod === 'email' && firebaseEnabled">
                <v-text-field
                  v-model="email"
                  label="Email"
                  type="email"
                  prepend-icon="mdi-email"
                  required
                  :error-messages="errors.email"
                ></v-text-field>

                <v-text-field
                  v-model="password"
                  label="Password"
                  type="password"
                  prepend-icon="mdi-lock"
                  required
                  :error-messages="errors.password"
                ></v-text-field>
              </template>

              <v-alert v-if="errors.general" type="error" class="mb-4">
                {{ errors.general }}
              </v-alert>

              <!-- Phone login has two-step flow -->
              <template v-if="loginMethod === 'phone' && firebaseEnabled">
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
                  Use different number
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
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const firebaseEnabled = computed(() => authStore.firebaseConfigured)
const loginMethod = ref('username')
const identifier = ref('')
const phoneNumber = ref('')
const email = ref('')
const password = ref('')
const otpCode = ref('')
const otpSent = ref(false)
const loading = ref(false)
const errors = ref({
  identifier: '',
  phone: '',
  email: '',
  password: '',
  otp: '',
  general: ''
})

// Initialize reCAPTCHA when switching to phone login
watch(loginMethod, (newMethod) => {
  if (newMethod === 'phone' && firebaseEnabled.value) {
    setTimeout(() => {
      authStore.initRecaptcha('recaptcha-container')
    }, 100)
  }
  resetErrors()
  otpSent.value = false
  otpCode.value = ''
})

onMounted(() => {
  if (loginMethod.value === 'phone' && firebaseEnabled.value) {
    authStore.initRecaptcha('recaptcha-container')
  }
})

const resetErrors = () => {
  errors.value = {
    identifier: '',
    phone: '',
    email: '',
    password: '',
    otp: '',
    general: ''
  }
}

const resetPhoneLogin = () => {
  otpSent.value = false
  otpCode.value = ''
  phoneNumber.value = ''
  resetErrors()
  if (firebaseEnabled.value) {
    setTimeout(() => {
      authStore.initRecaptcha('recaptcha-container')
    }, 100)
  }
}

const sendOTP = async () => {
  loading.value = true
  resetErrors()

  if (phoneNumber.value && !phoneNumber.value.startsWith('+')) {
    phoneNumber.value = '+' + phoneNumber.value.replace(/^\+/, '')
  }

  try {
    await authStore.sendPhoneOTP(phoneNumber.value)
    otpSent.value = true
  } catch (error) {
    if (error.code === 'auth/invalid-phone-number') {
      errors.value.phone = 'Invalid phone number format'
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
    if (loginMethod.value === 'username' || !firebaseEnabled.value) {
      // Password-based login (works in dev mode)
      await authStore.login({
        identifier: identifier.value,
        password: password.value
      })
    } else if (loginMethod.value === 'phone') {
      await authStore.loginWithPhone(phoneNumber.value, otpCode.value)
    } else if (loginMethod.value === 'email') {
      await authStore.loginWithEmail(email.value, password.value)
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
          errors.value.general = 'Invalid email or password'
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
