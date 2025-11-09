<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card>
          <v-card-title class="text-h5">Verify Your Phone Number</v-card-title>
          <v-card-text>
            <p v-if="authStore.user">
              We've sent a verification code to {{ authStore.user.phone_number || 'your phone' }}
            </p>
            <v-form @submit.prevent="handleVerification">
              <v-text-field
                v-model="verificationCode"
                label="Verification Code"
                placeholder="123456"
                maxlength="6"
                prepend-icon="mdi-shield-check"
                required
                :error-messages="errorMessage"
                @input="errorMessage = ''"
              ></v-text-field>

              <v-alert v-if="successMessage" type="success" class="mb-4">
                {{ successMessage }}
              </v-alert>

              <v-alert v-if="errorMessage" type="error" class="mb-4">
                {{ errorMessage }}
              </v-alert>

              <v-btn
                type="submit"
                color="primary"
                block
                :loading="verifying"
                class="mt-4"
                :disabled="verificationCode.length !== 6"
              >
                Verify
              </v-btn>

              <v-btn
                @click="resendCode"
                color="secondary"
                block
                :loading="resending"
                class="mt-2"
                variant="outlined"
              >
                Resend Code
              </v-btn>
            </v-form>

            <v-divider class="my-4"></v-divider>

            <p class="text-center text-caption">
              If you're testing, check the Django console for your verification code.
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

const verificationCode = ref('')
const verifying = ref(false)
const resending = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const handleVerification = async () => {
  if (verificationCode.value.length !== 6) {
    errorMessage.value = 'Please enter a 6-digit code'
    return
  }

  verifying.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    await authStore.verifyPhone(verificationCode.value)
    successMessage.value = 'Phone verified successfully!'

    // Update user profile to reflect verification
    await authStore.fetchProfile()

    setTimeout(() => {
      router.push('/')
    }, 2000)
  } catch (error) {
    console.error('Verification error:', error)
    errorMessage.value = error.error || 'Invalid or expired verification code'
  } finally {
    verifying.value = false
  }
}

const resendCode = async () => {
  resending.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    await authStore.resendVerification()
    successMessage.value = 'Verification code resent! Check your phone (or Django console).'
  } catch (error) {
    console.error('Resend error:', error)
    errorMessage.value = error.error || 'Failed to resend code. Please try again.'
  } finally {
    resending.value = false
  }
}

// Check if already verified
if (authStore.phoneVerified) {
  router.push('/')
}
</script>