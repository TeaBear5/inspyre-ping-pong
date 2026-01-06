<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card>
          <v-card-title class="text-h5">Phone Verification</v-card-title>
          <v-card-text>
            <!-- Dev mode notice -->
            <v-alert v-if="!firebaseEnabled" type="info" class="mb-4">
              <strong>Development Mode</strong>
              <p class="mb-0">Verification is not required in development mode. Your account is automatically active.</p>
            </v-alert>

            <!-- Firebase enabled - show verification -->
            <template v-else>
              <v-alert v-if="authStore.isVerified" type="success" class="mb-4">
                <strong>Already Verified!</strong>
                <p class="mb-0">Your account is verified. You can access all features.</p>
              </v-alert>

              <template v-else>
                <p class="mb-4">
                  Your phone number needs verification to access all features.
                </p>

                <!-- Phone verification -->
                <v-card variant="outlined" class="mb-4" v-if="authStore.user?.phone_number">
                  <v-card-title class="text-subtitle-1">
                    <v-icon class="mr-2">mdi-phone</v-icon>
                    Verify Your Phone
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
                        class="mb-2"
                      >
                        Verify Code
                      </v-btn>
                      <v-btn
                        variant="text"
                        @click="resendPhoneCode"
                        :loading="sendingOtp"
                        block
                        size="small"
                      >
                        Didn't receive code? Resend
                      </v-btn>
                    </template>
                  </v-card-text>
                </v-card>

                <v-alert v-if="!authStore.user?.phone_number" type="warning" class="mb-4">
                  No phone number on file. Please update your profile to add a phone number.
                </v-alert>

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
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const firebaseEnabled = computed(() => authStore.firebaseConfigured)
const otpSent = ref(false)
const otpCode = ref('')
const sendingOtp = ref(false)
const verifying = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// reCAPTCHA container ID for this component
const RECAPTCHA_CONTAINER_ID = 'verify-recaptcha-container'

// Cleanup reCAPTCHA when component unmounts
onUnmounted(() => {
  authStore.clearRecaptcha()
})

const startPhoneVerification = async () => {
  sendingOtp.value = true
  errorMessage.value = ''

  try {
    // Pass container ID - sendPhoneOTP handles reCAPTCHA initialization
    await authStore.sendPhoneOTP(authStore.user?.phone_number, RECAPTCHA_CONTAINER_ID)
    otpSent.value = true
    successMessage.value = 'Verification code sent!'
  } catch (error) {
    errorMessage.value = error.message || 'Failed to send verification code'
  } finally {
    sendingOtp.value = false
  }
}

const resendPhoneCode = async () => {
  sendingOtp.value = true
  errorMessage.value = ''
  otpCode.value = ''

  try {
    // sendPhoneOTP handles reCAPTCHA initialization internally
    await authStore.sendPhoneOTP(authStore.user?.phone_number, RECAPTCHA_CONTAINER_ID)
    successMessage.value = 'New verification code sent!'
  } catch (error) {
    if (error.code === 'auth/too-many-requests') {
      errorMessage.value = 'Too many attempts. Please wait a few minutes and try again.'
    } else {
      errorMessage.value = error.message || 'Failed to resend code'
    }
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
</script>
