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
              <!-- Verification Method Selection (only if Firebase enabled) -->
              <v-radio-group v-if="firebaseEnabled" v-model="verificationMethod" inline class="mb-4">
                <v-radio label="Verify by Phone" value="phone"></v-radio>
                <v-radio label="Verify by Email" value="email"></v-radio>
              </v-radio-group>

              <!-- Phone Number -->
              <v-text-field
                v-if="verificationMethod === 'phone' || !firebaseEnabled"
                v-model="formData.phone_number"
                :label="firebaseEnabled ? 'Phone Number' : 'Phone Number (optional)'"
                placeholder="+1234567890"
                hint="Include country code (e.g., +1 for US)"
                prepend-icon="mdi-phone"
                :required="firebaseEnabled && verificationMethod === 'phone'"
                :error-messages="errors.phone_number"
                @input="formatPhoneNumber"
              ></v-text-field>

              <!-- Email -->
              <v-text-field
                v-if="verificationMethod === 'email' || !firebaseEnabled"
                v-model="formData.email"
                :label="firebaseEnabled ? 'Email' : 'Email (optional)'"
                type="email"
                prepend-icon="mdi-email"
                :required="firebaseEnabled && verificationMethod === 'email'"
                :error-messages="errors.email"
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

              <!-- Optional fields when Firebase enabled -->
              <v-text-field
                v-if="firebaseEnabled && verificationMethod === 'phone'"
                v-model="formData.email"
                label="Email (optional)"
                type="email"
                prepend-icon="mdi-email"
                :error-messages="errors.email"
              ></v-text-field>

              <v-text-field
                v-if="firebaseEnabled && verificationMethod === 'email'"
                v-model="formData.phone_number"
                label="Phone Number (optional)"
                placeholder="+1234567890"
                prepend-icon="mdi-phone"
                :error-messages="errors.phone_number"
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
              <v-btn @click="resendPhoneCode" :loading="resending">Resend Code</v-btn>
              <v-spacer></v-spacer>
              <v-btn color="primary" @click="handlePhoneVerification" :loading="verifying">
                Verify
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <!-- Email Verification Notice Dialog -->
        <v-dialog v-model="showEmailVerification" persistent max-width="400">
          <v-card>
            <v-card-title>Verify Your Email</v-card-title>
            <v-card-text>
              <v-icon size="64" color="primary" class="d-block mx-auto mb-4">mdi-email-check</v-icon>
              <p class="text-center">
                We've sent a verification email to <strong>{{ formData.email }}</strong>
              </p>
              <p class="text-center text-grey">
                Please check your inbox and click the verification link.
                After verifying, come back and log in.
              </p>
            </v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn color="primary" @click="goToLogin">
                Go to Login
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
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
const verificationMethod = ref('phone')
const formData = ref({
  phone_number: '',
  username: '',
  display_name: '',
  email: '',
  password: '',
  password_confirm: ''
})

const loading = ref(false)
const showPhoneVerification = ref(false)
const showEmailVerification = ref(false)
const verificationCode = ref('')
const verifying = ref(false)
const resending = ref(false)
const successMessage = ref('')
const verificationError = ref('')

const errors = ref({
  phone_number: '',
  username: '',
  display_name: '',
  email: '',
  password: '',
  password_confirm: '',
  general: ''
})

// Initialize reCAPTCHA for phone registration
watch(verificationMethod, (newMethod) => {
  if (newMethod === 'phone' && firebaseEnabled.value) {
    setTimeout(() => {
      authStore.initRecaptcha('register-recaptcha-container')
    }, 100)
  }
})

onMounted(() => {
  if (verificationMethod.value === 'phone' && firebaseEnabled.value) {
    authStore.initRecaptcha('register-recaptcha-container')
  }
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
    email: '',
    password: '',
    password_confirm: '',
    general: ''
  }
  verificationError.value = ''
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
        verification_method: 'phone'  // Default to phone but doesn't require verification
      })
      successMessage.value = 'Registration successful! Please wait for admin approval.'
      setTimeout(() => router.push('/'), 2000)
    } else if (verificationMethod.value === 'phone') {
      // Phone registration: Send OTP first
      await authStore.sendPhoneOTP(formData.value.phone_number)
      showPhoneVerification.value = true
    } else {
      // Email registration: Create Firebase user and send verification email
      await authStore.signUpWithEmail(formData.value.email, formData.value.password)
      await authStore.register({
        ...formData.value,
        verification_method: 'email'
      })
      showEmailVerification.value = true
    }
  } catch (error) {
    console.error('Registration error:', error)

    if (error.code) {
      switch (error.code) {
        case 'auth/invalid-phone-number':
          errors.value.phone_number = 'Invalid phone number format'
          break
        case 'auth/email-already-in-use':
          errors.value.email = 'Email already in use'
          break
        case 'auth/weak-password':
          errors.value.password = 'Password is too weak. Use at least 6 characters.'
          break
        case 'auth/invalid-email':
          errors.value.email = 'Invalid email format'
          break
        case 'auth/too-many-requests':
          errors.value.general = 'Too many attempts. Please try again later.'
          break
        default:
          errors.value.general = error.message || 'Registration failed'
      }
    } else if (error) {
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
    const result = await authStore.verifyPhoneOTP(verificationCode.value)
    await authStore.register({
      ...formData.value,
      verification_method: 'phone',
      firebase_token: result.idToken
    })

    showPhoneVerification.value = false
    successMessage.value = 'Registration successful! Please wait for admin approval.'
    setTimeout(() => router.push('/'), 2000)
  } catch (error) {
    console.error('Verification error:', error)

    if (error.code === 'auth/invalid-verification-code') {
      verificationError.value = 'Invalid verification code'
    } else if (error.code === 'auth/code-expired') {
      verificationError.value = 'Code expired. Please request a new one.'
    } else {
      verificationError.value = error.error || error.message || 'Verification failed'
    }
  } finally {
    verifying.value = false
  }
}

const resendPhoneCode = async () => {
  resending.value = true
  verificationError.value = ''

  try {
    authStore.initRecaptcha('register-recaptcha-container')
    await authStore.sendPhoneOTP(formData.value.phone_number)
  } catch (error) {
    verificationError.value = error.message || 'Failed to resend code'
  } finally {
    resending.value = false
  }
}

const goToLogin = () => {
  showEmailVerification.value = false
  router.push('/login')
}
</script>
