import { defineStore } from 'pinia'
import axios from 'axios'
import { isFirebaseConfigured, initializeFirebase } from '../firebase'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

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
     * Initialize reCAPTCHA verifier for phone authentication
     */
    async initRecaptcha(containerId) {
      if (!await this.ensureFirebaseInitialized()) {
        console.log('[DEV] Firebase not configured - reCAPTCHA not initialized')
        return false
      }

      try {
        // Dynamic import after ensuring Firebase is initialized
        const { auth, RecaptchaVerifier } = await import('../firebase')
        if (!auth || !RecaptchaVerifier) {
          console.log('[DEV] Firebase auth not available')
          return false
        }

        this.recaptchaVerifier = new RecaptchaVerifier(auth, containerId, {
          size: 'invisible',
          callback: () => console.log('reCAPTCHA solved'),
          'expired-callback': () => console.log('reCAPTCHA expired')
        })
        return true
      } catch (error) {
        console.error('reCAPTCHA initialization error:', error)
        return false
      }
    },

    /**
     * Send OTP to phone number via Firebase
     */
    async sendPhoneOTP(phoneNumber) {
      if (!await this.ensureFirebaseInitialized()) {
        console.log('[DEV] Firebase not configured - skipping phone OTP')
        return { success: true, dev: true }
      }

      if (!this.recaptchaVerifier) {
        throw new Error('reCAPTCHA not initialized. Call initRecaptcha first.')
      }

      try {
        const { auth, signInWithPhoneNumber } = await import('../firebase')
        this.confirmationResult = await signInWithPhoneNumber(auth, phoneNumber, this.recaptchaVerifier)
        return { success: true }
      } catch (error) {
        console.error('Send OTP error:', error)
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
    async syncVerificationStatus() {
      if (!this.firebaseUser) {
        return null
      }

      try {
        const idToken = await this.firebaseUser.getIdToken()
        const response = await axios.post(`${API_URL}/auth/firebase-verify/`, {
          firebase_token: idToken
        })

        if (response.data.user) {
          this.user = response.data.user
          this.isVerified = response.data.user.is_verified
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
