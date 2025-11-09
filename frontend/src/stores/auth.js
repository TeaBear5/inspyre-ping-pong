import { defineStore } from 'pinia'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export const useAuthStore = defineStore('auth', {
  state: () => {
    const storedUser = JSON.parse(localStorage.getItem('user')) || null
    return {
      user: storedUser,
      token: localStorage.getItem('token') || null,
      isAuthenticated: !!localStorage.getItem('token'),
      isApproved: storedUser?.is_approved || false,
      phoneVerified: storedUser?.phone_verified || false
    }
  },

  actions: {
    async register(userData) {
      try {
        console.log('Sending registration data:', userData)  // Debug log
        const response = await axios.post(`${API_URL}/auth/register/`, userData)

        // Auto-login after registration
        if (response.data.token) {
          this.token = response.data.token
          this.user = response.data.user
          this.isAuthenticated = true
          this.isApproved = response.data.user.is_approved
          this.phoneVerified = response.data.user.phone_verified

          // Store in localStorage
          localStorage.setItem('token', this.token)
          localStorage.setItem('user', JSON.stringify(this.user))

          // Set default axios header
          axios.defaults.headers.common['Authorization'] = `Token ${this.token}`
        }

        return response.data
      } catch (error) {
        console.error('Registration API error:', error.response)  // Debug log
        throw error.response?.data || { error: 'Registration failed' }
      }
    },

    async login(credentials) {
      try {
        const response = await axios.post(`${API_URL}/auth/login/`, credentials)
        this.token = response.data.token
        this.user = response.data.user
        this.isAuthenticated = true
        this.isApproved = response.data.user.is_approved
        this.phoneVerified = response.data.user.phone_verified

        // Store in localStorage
        localStorage.setItem('token', this.token)
        localStorage.setItem('user', JSON.stringify(this.user))

        // Set default axios header (Django uses 'Token' not 'Bearer')
        axios.defaults.headers.common['Authorization'] = `Token ${this.token}`

        return response.data
      } catch (error) {
        throw error.response?.data || error
      }
    },

    async verifyPhone(code) {
      try {
        const response = await axios.post(`${API_URL}/auth/verify-phone/`, { code })
        this.phoneVerified = true
        if (this.user) {
          this.user.phone_verified = true
          localStorage.setItem('user', JSON.stringify(this.user))
        }
        return response.data
      } catch (error) {
        throw error.response?.data || error
      }
    },

    async resendVerification() {
      try {
        const response = await axios.post(`${API_URL}/auth/resend-verification/`)
        return response.data
      } catch (error) {
        throw error.response?.data || error
      }
    },

    async fetchProfile() {
      try {
        const response = await axios.get(`${API_URL}/auth/profile/`)
        this.user = response.data
        this.isApproved = response.data.is_approved
        this.phoneVerified = response.data.phone_verified
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

    logout() {
      this.user = null
      this.token = null
      this.isAuthenticated = false
      this.isApproved = false
      this.phoneVerified = false

      localStorage.removeItem('token')
      localStorage.removeItem('user')

      delete axios.defaults.headers.common['Authorization']
    },

    initializeAuth() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Token ${this.token}`
      }
    }
  },

  getters: {
    canAccessApp() {
      return this.isAuthenticated && this.isApproved && this.phoneVerified
    }
  }
})