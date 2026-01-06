<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card>
          <v-card-title class="text-h5">Login</v-card-title>
          <v-card-text>
            <!-- Login method toggle -->
            <v-btn-toggle
              v-model="loginMethod"
              mandatory
              color="primary"
              class="mb-4 d-flex"
              density="comfortable"
            >
              <v-btn value="phone" :disabled="!firebaseEnabled" class="flex-grow-1">
                <v-icon start>mdi-phone</v-icon>
                Phone
              </v-btn>
              <v-btn value="password" class="flex-grow-1">
                <v-icon start>mdi-lock</v-icon>
                Password
              </v-btn>
            </v-btn-toggle>

            <!-- Dev mode notice -->
            <v-alert v-if="!firebaseEnabled && loginMethod === 'phone'" type="warning" variant="tonal" class="mb-4" density="compact">
              Phone login requires Firebase configuration
            </v-alert>

            <v-form @submit.prevent="handleLogin">
              <!-- Phone Number field for phone login -->
              <template v-if="loginMethod === 'phone' && firebaseEnabled">
                <v-text-field
                  v-model="phoneNumber"
                  label="Phone Number"
                  placeholder="+1234567890"
                  hint="Include country code (e.g., +1 for US)"
                  prepend-icon="mdi-phone"
                  required
                  :error-messages="errors.phone"
                  :disabled="otpSent"
                  @input="formatPhoneNumber"
                ></v-text-field>

                <!-- OTP field for phone login -->
                <v-text-field
                  v-if="otpSent"
                  v-model="otpCode"
                  label="Verification Code"
                  placeholder="123456"
                  prepend-icon="mdi-numeric"
                  maxlength="6"
                  :error-messages="errors.otp"
                  @keyup.enter="handleLogin"
                ></v-text-field>
              </template>

              <!-- Username/Password fields -->
              <template v-if="loginMethod === 'password'">
                <v-text-field
                  v-model="identifier"
                  label="Username, Email, or Phone"
                  placeholder="Enter your login"
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

              <!-- reCAPTCHA container (invisible) -->
              <div id="recaptcha-container"></div>

              <v-alert v-if="errors.general" type="error" class="mb-4">
                {{ errors.general }}
              </v-alert>

              <!-- Phone login buttons -->
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

              <!-- Password login button -->
              <v-btn
                v-if="loginMethod === 'password'"
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
import { ref, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const firebaseEnabled = computed(() => authStore.firebaseConfigured)

// Default to password login if Firebase is not configured, otherwise phone
const loginMethod = ref(firebaseEnabled.value ? 'phone' : 'password')

const phoneNumber = ref('')
const identifier = ref('')
const password = ref('')
const otpCode = ref('')
const otpSent = ref(false)
const loading = ref(false)
const errors = ref({
  phone: '',
  identifier: '',
  password: '',
  otp: '',
  general: ''
})

// reCAPTCHA container ID for this component
const RECAPTCHA_CONTAINER_ID = 'recaptcha-container'

// Reset state when switching login methods
watch(loginMethod, () => {
  resetErrors()
  otpSent.value = false
  otpCode.value = ''
  authStore.clearRecaptcha()
})

// Cleanup reCAPTCHA when component unmounts
onUnmounted(() => {
  authStore.clearRecaptcha()
})

const resetErrors = () => {
  errors.value = {
    phone: '',
    identifier: '',
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
  authStore.clearRecaptcha()
}

const formatPhoneNumber = () => {
  if (phoneNumber.value && !phoneNumber.value.startsWith('+')) {
    phoneNumber.value = '+' + phoneNumber.value.replace(/^\+/, '')
  }
}

const getFormattedPhone = () => {
  let phone = phoneNumber.value.trim().replace(/[\s\-\(\)]/g, '')
  if (phone && !phone.startsWith('+')) {
    phone = '+' + phone
  }
  return phone
}

const sendOTP = async () => {
  loading.value = true
  resetErrors()

  const phone = getFormattedPhone()

  try {
    await authStore.sendPhoneOTP(phone, RECAPTCHA_CONTAINER_ID)
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
    if (loginMethod.value === 'phone' && firebaseEnabled.value) {
      // Phone OTP login
      const phone = getFormattedPhone()
      await authStore.loginWithPhone(phone, otpCode.value)
    } else {
      // Password-based login
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
