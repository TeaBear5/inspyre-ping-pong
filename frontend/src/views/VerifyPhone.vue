<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card>
          <v-card-title class="text-h5">Account Verification</v-card-title>
          <v-card-text>
            <!-- Dev mode notice -->
            <v-alert v-if="!firebaseEnabled" type="info" class="mb-4">
              <strong>Development Mode</strong>
              <p class="mb-2">Verification is not required in development mode.</p>
              <p class="mb-0">Your account should already be accessible once approved by an admin.</p>
            </v-alert>

            <!-- Firebase enabled - show verification options -->
            <template v-else>
              <v-alert v-if="authStore.isVerified" type="success" class="mb-4">
                <strong>Already Verified!</strong>
                <p class="mb-0">Your account is verified. You can access all features.</p>
              </v-alert>

              <template v-else>
                <p class="mb-4">
                  Your account needs verification. Please complete one of the following:
                </p>

                <!-- Phone verification option -->
                <v-card variant="outlined" class="mb-4" v-if="authStore.user?.phone_number">
                  <v-card-title class="text-subtitle-1">
                    <v-icon class="mr-2">mdi-phone</v-icon>
                    Phone Verification
                  </v-card-title>
                  <v-card-text>
                    <p class="text-grey mb-2">Phone: {{ authStore.user?.phone_number }}</p>
                    <v-btn
                      color="primary"
                      @click="startPhoneVerification"
                      :loading="sendingOtp"
                      :disabled="otpSent"
                    >
                      {{ otpSent ? 'Code Sent' : 'Send Verification Code' }}
                    </v-btn>

                    <template v-if="otpSent">
                      <v-text-field
                        v-model="otpCode"
                        label="Enter 6-digit code"
                        maxlength="6"
                        class="mt-4"
                        @keyup.enter="verifyOtp"
                      ></v-text-field>
                      <v-btn
                        color="success"
                        @click="verifyOtp"
                        :loading="verifying"
                        block
                      >
                        Verify Code
                      </v-btn>
                    </template>
                  </v-card-text>
                </v-card>

                <!-- Email verification option -->
                <v-card variant="outlined" class="mb-4" v-if="authStore.user?.email">
                  <v-card-title class="text-subtitle-1">
                    <v-icon class="mr-2">mdi-email</v-icon>
                    Email Verification
                  </v-card-title>
                  <v-card-text>
                    <p class="text-grey mb-2">Email: {{ authStore.user?.email }}</p>
                    <p class="text-body-2">
                      Check your email inbox for a verification link from Firebase.
                      Click the link to verify your email address.
                    </p>
                    <v-btn
                      color="primary"
                      variant="outlined"
                      @click="resendEmailVerification"
                      :loading="resending"
                    >
                      Resend Verification Email
                    </v-btn>
                  </v-card-text>
                </v-card>

                <v-alert v-if="errorMessage" type="error" class="mt-4">
                  {{ errorMessage }}
                </v-alert>

                <v-alert v-if="successMessage" type="success" class="mt-4">
                  {{ successMessage }}
                </v-alert>
              </template>
            </template>

            <v-divider class="my-4"></v-divider>

            <v-btn block variant="text" @click="router.push('/')">
              Back to Home
            </v-btn>
          </v-card-text>
        </v-card>

        <!-- reCAPTCHA container -->
        <div id="verify-recaptcha-container"></div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const firebaseEnabled = computed(() => authStore.firebaseConfigured)
const otpSent = ref(false)
const otpCode = ref('')
const sendingOtp = ref(false)
const verifying = ref(false)
const resending = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

onMounted(() => {
  if (firebaseEnabled.value) {
    authStore.initRecaptcha('verify-recaptcha-container')
  }
})

const startPhoneVerification = async () => {
  sendingOtp.value = true
  errorMessage.value = ''

  try {
    await authStore.sendPhoneOTP(authStore.user?.phone_number)
    otpSent.value = true
    successMessage.value = 'Verification code sent!'
  } catch (error) {
    errorMessage.value = error.message || 'Failed to send verification code'
  } finally {
    sendingOtp.value = false
  }
}

const verifyOtp = async () => {
  verifying.value = true
  errorMessage.value = ''

  try {
    await authStore.verifyPhoneOTP(otpCode.value)
    await authStore.syncVerificationStatus()
    successMessage.value = 'Phone verified successfully!'
    setTimeout(() => router.push('/'), 1500)
  } catch (error) {
    if (error.code === 'auth/invalid-verification-code') {
      errorMessage.value = 'Invalid verification code'
    } else if (error.code === 'auth/code-expired') {
      errorMessage.value = 'Code expired. Please request a new one.'
      otpSent.value = false
    } else {
      errorMessage.value = error.message || 'Verification failed'
    }
  } finally {
    verifying.value = false
  }
}

const resendEmailVerification = async () => {
  resending.value = true
  errorMessage.value = ''

  try {
    successMessage.value = 'Please check your email for the verification link. If you did not receive it, try logging out and registering again.'
  } catch (error) {
    errorMessage.value = error.message || 'Failed to resend verification email'
  } finally {
    resending.value = false
  }
}
</script>
