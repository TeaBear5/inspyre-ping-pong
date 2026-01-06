<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card>
          <v-card-title class="text-h5">Register</v-card-title>
          <v-card-text>
            <!-- Dev mode notice -->
            <v-alert v-if="!firebaseEnabled" type="info" variant="tonal" class="mb-4" density="compact">
              Development mode - verification skipped
            </v-alert>

            <v-form @submit.prevent="handleRegister">
              <!-- Phone Number (required for verification) -->
              <v-text-field
                v-model="formData.phone_number"
                :label="firebaseEnabled ? 'Phone Number' : 'Phone Number (optional)'"
                placeholder="+1234567890"
                hint="Include country code (e.g., +1 for US)"
                prepend-icon="mdi-phone"
                :required="firebaseEnabled"
                :error-messages="errors.phone_number"
                @input="formatPhoneNumber"
              ></v-text-field>

              <v-text-field
                v-model="formData.username"
                label="Username"
                prepend-icon="mdi-account"
                required
                :error-messages="errors.username"
              ></v-text-field>

              <v-text-field
                v-model="formData.display_name"
                label="Display Name"
                prepend-icon="mdi-card-account-details"
                required
                :error-messages="errors.display_name"
              ></v-text-field>

              <v-text-field
                v-model="formData.password"
                label="Password"
                type="password"
                prepend-icon="mdi-lock"
                required
                :error-messages="errors.password"
              ></v-text-field>

              <v-text-field
                v-model="formData.password_confirm"
                label="Confirm Password"
                type="password"
                prepend-icon="mdi-lock-check"
                required
                :error-messages="errors.password_confirm"
              ></v-text-field>

              <!-- reCAPTCHA container for phone verification -->
              <div id="register-recaptcha-container"></div>

              <v-alert v-if="successMessage" type="success" class="mb-4">
                {{ successMessage }}
              </v-alert>

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
                Register
              </v-btn>
            </v-form>

            <v-divider class="my-4"></v-divider>

            <p class="text-center">
              Already have an account?
              <router-link to="/login">Login here</router-link>
            </p>
          </v-card-text>
        </v-card>

        <!-- Phone Verification Dialog -->
        <v-dialog v-model="showPhoneVerification" persistent max-width="400">
          <v-card>
            <v-card-title>Verify Phone Number</v-card-title>
            <v-card-text>
              <p>We've sent a verification code to {{ formData.phone_number }}</p>
              <v-text-field
                v-model="verificationCode"
                label="Verification Code"
                maxlength="6"
                prepend-icon="mdi-numeric"
                @keyup.enter="handlePhoneVerification"
              ></v-text-field>
              <v-alert v-if="verificationError" type="error" class="mt-2">
                {{ verificationError }}
              </v-alert>
            </v-card-text>
            <v-card-actions>
              <v-btn @click="cancelVerification" variant="text">Cancel</v-btn>
              <v-btn @click="resendPhoneCode" :loading="resending">Resend Code</v-btn>
              <v-spacer></v-spacer>
              <v-btn color="primary" @click="handlePhoneVerification" :loading="verifying">
                Verify
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const firebaseEnabled = computed(() => authStore.firebaseConfigured)
const formData = ref({
  phone_number: '',
  username: '',
  display_name: '',
  password: '',
  password_confirm: ''
})

const loading = ref(false)
const showPhoneVerification = ref(false)
const verificationCode = ref('')
const verifying = ref(false)
const resending = ref(false)
const successMessage = ref('')
const verificationError = ref('')

const errors = ref({
  phone_number: '',
  username: '',
  display_name: '',
  password: '',
  password_confirm: '',
  general: ''
})

// reCAPTCHA container ID for this component
const RECAPTCHA_CONTAINER_ID = 'register-recaptcha-container'

// Cleanup reCAPTCHA when component unmounts
onUnmounted(() => {
  authStore.clearRecaptcha()
})

const formatPhoneNumber = () => {
  if (formData.value.phone_number && !formData.value.phone_number.startsWith('+')) {
    formData.value.phone_number = '+' + formData.value.phone_number.replace(/^\+/, '')
  }
}

const resetErrors = () => {
  errors.value = {
    phone_number: '',
    username: '',
    display_name: '',
    password: '',
    password_confirm: '',
    general: ''
  }
  verificationError.value = ''
}

// Helper to extract error message from backend response
const extractErrorMessage = (error) => {
  if (!error) return 'An error occurred'

  // If it's a string, return it
  if (typeof error === 'string') return error

  // Check for common error properties
  if (error.error) return error.error
  if (error.detail) return error.detail
  if (error.message) return error.message

  // Check for field-specific errors and combine them
  const fieldErrors = []
  for (const [key, value] of Object.entries(error)) {
    if (key !== 'error' && key !== 'detail' && key !== 'message') {
      const msg = Array.isArray(value) ? value[0] : value
      if (msg) fieldErrors.push(`${key}: ${msg}`)
    }
  }
  if (fieldErrors.length > 0) return fieldErrors.join(', ')

  return 'An error occurred'
}

const handleRegister = async () => {
  loading.value = true
  resetErrors()

  if (formData.value.password !== formData.value.password_confirm) {
    errors.value.password_confirm = 'Passwords do not match'
    loading.value = false
    return
  }

  formatPhoneNumber()

  try {
    if (!firebaseEnabled.value) {
      // Dev mode - just register directly with password
      await authStore.register({
        ...formData.value,
        verification_method: 'phone'
      })
      successMessage.value = 'Registration successful!'
      setTimeout(() => router.push('/'), 2000)
    } else {
      // Step 1: Validate registration data with backend FIRST
      // This checks username/phone availability before we even touch Firebase
      console.log('[Register] Validating registration data with backend...')
      await authStore.validateRegistration({
        ...formData.value,
        verification_method: 'phone'
      })
      console.log('[Register] Validation passed, sending OTP...')

      // Step 2: Only send OTP after validation passes
      await authStore.sendPhoneOTP(formData.value.phone_number, RECAPTCHA_CONTAINER_ID)
      showPhoneVerification.value = true
    }
  } catch (error) {
    console.error('Registration error:', error)

    if (error.code) {
      // Firebase error
      switch (error.code) {
        case 'auth/invalid-phone-number':
          errors.value.phone_number = 'Invalid phone number format'
          break
        case 'auth/too-many-requests':
          errors.value.general = 'Too many attempts. Please try again later.'
          break
        default:
          errors.value.general = error.message || 'Registration failed'
      }
    } else if (error) {
      // Backend validation error - show field-specific errors
      const data = error
      Object.keys(data).forEach(key => {
        if (errors.value.hasOwnProperty(key)) {
          errors.value[key] = Array.isArray(data[key]) ? data[key][0] : data[key]
        } else if (key === 'non_field_errors' || key === 'detail' || key === 'error') {
          errors.value.general = Array.isArray(data[key]) ? data[key][0] : data[key]
        }
      })

      if (Object.values(errors.value).every(v => !v)) {
        errors.value.general = error.error || 'Registration failed. Please check your information.'
      }
    }
  } finally {
    loading.value = false
  }
}

const handlePhoneVerification = async () => {
  verifying.value = true
  verificationError.value = ''

  try {
    // Step 1: Verify the OTP with Firebase
    console.log('[Register] Verifying OTP with Firebase...')
    const result = await authStore.verifyPhoneOTP(verificationCode.value)
    console.log('[Register] Firebase verification successful, registering with backend...')

    // Step 2: Register with the backend
    try {
      await authStore.register({
        ...formData.value,
        verification_method: 'phone',
        firebase_token: result.idToken
      })

      showPhoneVerification.value = false
      successMessage.value = 'Registration successful! You can now use the app.'
      setTimeout(() => router.push('/'), 2000)
    } catch (backendError) {
      console.error('[Register] Backend registration failed:', backendError)

      // Cleanup Firebase session since backend registration failed
      // This handles the edge case where username was taken between validation and registration
      console.log('[Register] Cleaning up Firebase session...')
      await authStore.cleanupFirebaseAuth()

      // Close the dialog and show the error on the main form
      // This allows user to fix the issue (e.g., change username) and try again
      showPhoneVerification.value = false
      verificationCode.value = ''

      // Show the error on the main form
      const errorMsg = extractErrorMessage(backendError)
      errors.value.general = errorMsg
    }
  } catch (firebaseError) {
    console.error('[Register] Firebase verification failed:', firebaseError)

    if (firebaseError.code === 'auth/invalid-verification-code') {
      verificationError.value = 'Invalid verification code'
    } else if (firebaseError.code === 'auth/code-expired') {
      verificationError.value = 'Code expired. Please request a new one.'
    } else {
      verificationError.value = firebaseError.message || 'Verification failed'
    }
  } finally {
    verifying.value = false
  }
}

const resendPhoneCode = async () => {
  resending.value = true
  verificationError.value = ''

  try {
    // sendPhoneOTP handles reCAPTCHA initialization internally
    await authStore.sendPhoneOTP(formData.value.phone_number, RECAPTCHA_CONTAINER_ID)
    verificationError.value = '' // Clear any previous errors
  } catch (error) {
    verificationError.value = error.message || 'Failed to resend code'
  } finally {
    resending.value = false
  }
}

const cancelVerification = () => {
  showPhoneVerification.value = false
  verificationCode.value = ''
  verificationError.value = ''
  // Clear reCAPTCHA to allow fresh attempt
  authStore.clearRecaptcha()
}
</script>
