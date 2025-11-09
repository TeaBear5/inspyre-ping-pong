<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card>
          <v-card-title class="text-h5">Register</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="handleRegister">
              <v-text-field
                v-model="formData.phone_number"
                label="Phone Number"
                placeholder="+1234567890"
                hint="Include country code (e.g., +1 for US)"
                prepend-icon="mdi-phone"
                required
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
                v-model="formData.email"
                label="Email (optional)"
                type="email"
                prepend-icon="mdi-email"
                :error-messages="errors.email"
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

        <!-- Verification Dialog -->
        <v-dialog v-model="showVerification" persistent max-width="400">
          <v-card>
            <v-card-title>Verify Phone Number</v-card-title>
            <v-card-text>
              <p>We've sent a verification code to {{ formData.phone_number }}</p>
              <v-text-field
                v-model="verificationCode"
                label="Verification Code"
                maxlength="6"
                @keyup.enter="handleVerification"
              ></v-text-field>
            </v-card-text>
            <v-card-actions>
              <v-btn @click="resendCode" :loading="resending">Resend Code</v-btn>
              <v-spacer></v-spacer>
              <v-btn color="primary" @click="handleVerification" :loading="verifying">
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formData = ref({
  phone_number: '',
  username: '',
  display_name: '',
  email: '',
  password: '',
  password_confirm: ''
})

const loading = ref(false)
const showVerification = ref(false)
const verificationCode = ref('')
const verifying = ref(false)
const resending = ref(false)
const successMessage = ref('')

const errors = ref({
  phone_number: '',
  username: '',
  display_name: '',
  email: '',
  password: '',
  password_confirm: '',
  general: ''
})

const formatPhoneNumber = () => {
  // Ensure phone number starts with + if it doesn't already
  if (formData.value.phone_number && !formData.value.phone_number.startsWith('+')) {
    formData.value.phone_number = '+' + formData.value.phone_number.replace(/^\+/, '')
  }
}

const handleRegister = async () => {
  loading.value = true
  errors.value = {
    phone_number: '',
    username: '',
    display_name: '',
    email: '',
    password: '',
    password_confirm: '',
    general: ''
  }

  // Ensure phone number has + prefix
  formatPhoneNumber()

  console.log('Registering with data:', formData.value) // Debug logging

  try {
    const response = await authStore.register(formData.value)
    successMessage.value = response.message
    showVerification.value = true
  } catch (error) {
    console.error('Registration error:', error) // Debug logging

    if (error) {
      const data = error
      Object.keys(data).forEach(key => {
        if (errors.value.hasOwnProperty(key)) {
          errors.value[key] = Array.isArray(data[key]) ? data[key][0] : data[key]
        } else if (key === 'non_field_errors' || key === 'detail' || key === 'error') {
          errors.value.general = Array.isArray(data[key]) ? data[key][0] : data[key]
        }
      })

      // If no specific errors were set, show a general message
      if (Object.values(errors.value).every(v => !v)) {
        errors.value.general = error.error || 'Registration failed. Please check your information and try again.'
      }
    } else {
      errors.value.general = 'Registration failed. Please try again.'
    }
  } finally {
    loading.value = false
  }
}

const handleVerification = async () => {
  verifying.value = true
  try {
    await authStore.verifyPhone(verificationCode.value)
    alert('Phone verified successfully! Please wait for admin approval.')
    router.push('/login')
  } catch (error) {
    alert('Verification failed. Please try again.')
  } finally {
    verifying.value = false
  }
}

const resendCode = async () => {
  resending.value = true
  try {
    await authStore.resendVerification()
    alert('Verification code resent!')
  } catch (error) {
    alert('Failed to resend code. Please try again.')
  } finally {
    resending.value = false
  }
}
</script>