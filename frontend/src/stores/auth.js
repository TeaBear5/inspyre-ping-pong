import { defineStore } from 'pinia'
import axios from 'axios'
import { isFirebaseConfigured, initializeFirebase } from '../firebase'
import { API_URL } from '../config'

export const useAuthStore = defineStore('auth', {
  state: () => {
    const storedUser = JSON.parse(localStorage.getItem('user')) || null
    return {
      user: storedUser,
      token: localStorage.getItem('token') || null,
      isAuthenticated: !!localStorage.getItem('token'),
      isApproved: storedUser?.is_approved || false,
      isVerified: storedUser?.is_verified || false,
      // Firebase-specific state
      confirmationResult: null,
      recaptchaVerifier: null,
      recaptchaWidgetId: null,
      currentRecaptchaContainerId: null,
      firebaseUser: null,
      firebaseInitialized: false
    }
  },

  actions: {
    /**
     * Ensure Firebase is initialized (only when needed)
     */
    async ensureFirebaseInitialized() {
      if (!isFirebaseConfigured()) {
        return false
      }
      if (!this.firebaseInitialized) {
        this.firebaseInitialized = await initializeFirebase()
      }
      return this.firebaseInitialized
    },

    /**
     * Safely clear existing reCAPTCHA verifier
     */
    clearRecaptcha() {
      if (this.recaptchaVerifier) {
        try {
          this.recaptchaVerifier.clear()
        } catch (e) {
          // Ignore errors during cleanup - verifier may already be destroyed
          console.log('[reCAPTCHA] Cleanup note:', e.message)
        }
        this.recaptchaVerifier = null
        this.recaptchaWidgetId = null
      }
    },

    /**
     * Initialize reCAPTCHA verifier for phone authentication
     * This creates a fresh verifier each time it's called
     */
    async initRecaptcha(containerId) {
      if (!await this.ensureFirebaseInitialized()) {
        console.log('[DEV] Firebase not configured - reCAPTCHA not initialized')
        return false
      }

      try {
        const { auth, RecaptchaVerifier } = await import('../firebase')
        if (!auth || !RecaptchaVerifier) {
          console.log('[DEV] Firebase auth not available')
          return false
        }

        // Always clear any existing verifier first
        this.clearRecaptcha()

        // Wait a tick for DOM to be ready and any previous cleanup to complete
        await new Promise(resolve => setTimeout(resolve, 100))

        // Check that the container element exists
        const container = document.getElementById(containerId)
        if (!container) {
          console.error('[reCAPTCHA] Container element not found:', containerId)
          return false
        }

        // Clear any leftover reCAPTCHA elements in the container
        container.innerHTML = ''

        // Create fresh verifier
        this.recaptchaVerifier = new RecaptchaVerifier(auth, containerId, {
          size: 'invisible',
          callback: (token) => {
            console.log('[reCAPTCHA] Solved successfully')
          },
          'expired-callback': () => {
            console.log('[reCAPTCHA] Token expired')
            // Don't null out verifier here - just let it be re-used
          },
          'error-callback': (error) => {
            console.error('[reCAPTCHA] Error:', error)
          }
        })

        // Pre-render the widget to catch any initialization errors early
        try {
          this.recaptchaWidgetId = await this.recaptchaVerifier.render()
          console.log('[reCAPTCHA] Rendered with widget ID:', this.recaptchaWidgetId)
        } catch (renderError) {
          console.error('[reCAPTCHA] Render error:', renderError)
          this.clearRecaptcha()
          return false
        }

        this.currentRecaptchaContainerId = containerId
        return true
      } catch (error) {
        console.error('[reCAPTCHA] Initialization error:', error)
        this.clearRecaptcha()
        return false
      }
    },

    /**
     * Send OTP to phone number via Firebase
     * Automatically handles reCAPTCHA initialization/reset
     */
    async sendPhoneOTP(phoneNumber, containerId = null) {
      if (!await this.ensureFirebaseInitialized()) {
        console.log('[DEV] Firebase not configured - skipping phone OTP')
        return { success: true, dev: true }
      }

      // Determine which container to use
      const targetContainerId = containerId || this.currentRecaptchaContainerId || 'recaptcha-container'

      // Always reinitialize reCAPTCHA for each OTP request
      // This ensures we have a fresh, valid verifier
      console.log('[Phone OTP] Initializing fresh reCAPTCHA for:', targetContainerId)
      const initialized = await this.initRecaptcha(targetContainerId)

      if (!initialized || !this.recaptchaVerifier) {
        throw new Error('Failed to initialize reCAPTCHA. Please refresh the page and try again.')
      }

      try {
        const { auth, signInWithPhoneNumber } = await import('../firebase')
        console.log('[Phone OTP] Sending verification code to:', phoneNumber)
        this.confirmationResult = await signInWithPhoneNumber(auth, phoneNumber, this.recaptchaVerifier)
        console.log('[Phone OTP] Verification code sent successfully')
        return { success: true }
      } catch (error) {
        console.error('[Phone OTP] Send error:', error)
        // Clear verifier on error so next attempt starts fresh
        this.clearRecaptcha()
        throw error
      }
    },

    /**
     * Verify phone OTP code
     */
    async verifyPhoneOTP(code) {
      if (!isFirebaseConfigured()) {
        console.log('[DEV] Firebase not configured - skipping OTP verification')
        return { success: true, dev: true }
      }

      if (!this.confirmationResult) {
        throw new Error('No pending verification. Send OTP first.')
      }

      try {
        const result = await this.confirmationResult.confirm(code)
        this.firebaseUser = result.user
        return {
          success: true,
          user: result.user,
          idToken: await result.user.getIdToken()
        }
      } catch (error) {
        console.error('Verify OTP error:', error)
        throw error
      }
    },

    /**
     * Sign up with email and password via Firebase
     */
    async signUpWithEmail(email, password) {
      if (!await this.ensureFirebaseInitialized()) {
        console.log('[DEV] Firebase not configured - skipping email signup')
        return { success: true, dev: true }
      }

      try {
        const { auth, createUserWithEmailAndPassword, sendEmailVerification } = await import('../firebase')
        const userCredential = await createUserWithEmailAndPassword(auth, email, password)
        await sendEmailVerification(userCredential.user)
        this.firebaseUser = userCredential.user
        return {
          success: true,
          user: userCredential.user,
          idToken: await userCredential.user.getIdToken()
        }
      } catch (error) {
        console.error('Email signup error:', error)
        throw error
      }
    },

    /**
     * Sign in with email and password via Firebase
     */
    async signInWithEmail(email, password) {
      if (!await this.ensureFirebaseInitialized()) {
        console.log('[DEV] Firebase not configured - skipping email signin')
        return { success: true, dev: true }
      }

      try {
        const { auth, signInWithEmailAndPassword } = await import('../firebase')
        const userCredential = await signInWithEmailAndPassword(auth, email, password)
        this.firebaseUser = userCredential.user
        return {
          success: true,
          user: userCredential.user,
          idToken: await userCredential.user.getIdToken()
        }
      } catch (error) {
        console.error('Email signin error:', error)
        throw error
      }
    },

    /**
     * Get current Firebase ID token
     */
    async getFirebaseIdToken() {
      if (!this.firebaseUser) {
        return null
      }
      return await this.firebaseUser.getIdToken()
    },

    /**
     * Register a new user (backend + optional Firebase)
     */
    async register(userData) {
      try {
        console.log('Sending registration data:', userData)

        const payload = { ...userData }
        if (this.firebaseUser) {
          payload.firebase_token = await this.firebaseUser.getIdToken()
        }

        const response = await axios.post(`${API_URL}/auth/register/`, payload)

        if (response.data.token) {
          this.token = response.data.token
          this.user = response.data.user
          this.isAuthenticated = true
          this.isApproved = response.data.user.is_approved
          this.isVerified = response.data.user.is_verified

          localStorage.setItem('token', this.token)
          localStorage.setItem('user', JSON.stringify(this.user))

          axios.defaults.headers.common['Authorization'] = `Token ${this.token}`
        }

        return response.data
      } catch (error) {
        console.error('Registration API error:', error.response)
        throw error.response?.data || { error: 'Registration failed' }
      }
    },

    /**
     * Login - supports both Firebase token and password-based login
     */
    async login(credentials) {
      try {
        const payload = { ...credentials }
        if (this.firebaseUser) {
          payload.firebase_token = await this.firebaseUser.getIdToken()
        }

        const response = await axios.post(`${API_URL}/auth/login/`, payload)
        this.token = response.data.token
        this.user = response.data.user
        this.isAuthenticated = true
        this.isApproved = response.data.user.is_approved
        this.isVerified = response.data.user.is_verified

        localStorage.setItem('token', this.token)
        localStorage.setItem('user', JSON.stringify(this.user))

        axios.defaults.headers.common['Authorization'] = `Token ${this.token}`

        return response.data
      } catch (error) {
        throw error.response?.data || error
      }
    },

    /**
     * Login with Firebase phone OTP
     */
    async loginWithPhone(phoneNumber, code) {
      const firebaseResult = await this.verifyPhoneOTP(code)

      return await this.login({
        phone_number: phoneNumber,
        firebase_token: firebaseResult.idToken
      })
    },

    /**
     * Login with Firebase email/password
     */
    async loginWithEmail(email, password) {
      const firebaseResult = await this.signInWithEmail(email, password)

      return await this.login({
        email: email,
        firebase_token: firebaseResult.dev ? undefined : firebaseResult.idToken
      })
    },

    /**
     * Sync verification status from Firebase
     */
    async syncVerificationStatus(phoneNumber = null) {
      if (!this.firebaseUser) {
        return null
      }

      try {
        const idToken = await this.firebaseUser.getIdToken()
        const payload = {
          firebase_token: idToken
        }
        // Allow updating phone number during verification
        if (phoneNumber) {
          payload.phone_number = phoneNumber
        }
        
        const response = await axios.post(`${API_URL}/auth/firebase-verify/`, payload)

        if (response.data.user) {
          this.user = response.data.user
          this.isVerified = response.data.user.is_verified
          this.isApproved = response.data.user.is_approved
          localStorage.setItem('user', JSON.stringify(this.user))
        }

        return response.data
      } catch (error) {
        console.error('Sync verification error:', error)
        throw error.response?.data || error
      }
    },

    async fetchProfile() {
      try {
        const response = await axios.get(`${API_URL}/auth/profile/`)
        this.user = response.data
        this.isApproved = response.data.is_approved
        this.isVerified = response.data.is_verified
        localStorage.setItem('user', JSON.stringify(this.user))
        return response.data
      } catch (error) {
        throw error.response?.data || error
      }
    },

    async updateProfile(profileData) {
      try {
        const response = await axios.patch(`${API_URL}/auth/profile/`, profileData)
        this.user = response.data
        localStorage.setItem('user', JSON.stringify(this.user))
        return response.data
      } catch (error) {
        throw error.response?.data || error
      }
    },

    async logout() {
      this.user = null
      this.token = null
      this.isAuthenticated = false
      this.isApproved = false
      this.isVerified = false
      this.firebaseUser = null
      this.confirmationResult = null

      localStorage.removeItem('token')
      localStorage.removeItem('user')

      delete axios.defaults.headers.common['Authorization']

      // Sign out from Firebase if configured
      if (isFirebaseConfigured()) {
        try {
          const { auth } = await import('../firebase')
          if (auth) {
            await auth.signOut()
          }
        } catch (error) {
          console.error('Firebase signout error:', error)
        }
      }
    },

    initializeAuth() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Token ${this.token}`
      }
    }
  },

  getters: {
    canAccessApp() {
      return this.isAuthenticated && this.isApproved && this.isVerified
    },

    firebaseConfigured() {
      return isFirebaseConfigured()
    }
  }
})
