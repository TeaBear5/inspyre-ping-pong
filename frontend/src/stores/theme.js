import { defineStore } from 'pinia'
import axios from 'axios'
import { API_URL } from '../config'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    currentTheme: 'light',
    isLoading: false
  }),

  getters: {
    isDark: (state) => state.currentTheme === 'dark',
    isLight: (state) => state.currentTheme === 'light'
  },

  actions: {

    async initializeTheme() {
      // First check localStorage for immediate theme application
      const savedTheme = localStorage.getItem('theme')
      if (savedTheme) {
        this.setTheme(savedTheme)
      }

      // Then try to load from user profile if authenticated
      const token = localStorage.getItem('authToken')
      if (token) {
        try {
          await this.loadThemeFromProfile()
        } catch (error) {
          console.warn('Could not load theme from profile, using localStorage theme')
        }
      } else if (!savedTheme) {
        // Only set default if no saved theme exists
        this.setTheme('light')
      }
    },

    async loadThemeFromProfile() {
      try {
        const token = localStorage.getItem('authToken')
        if (!token) {
          // Default to light theme for non-authenticated users
          this.setTheme('light')
          return
        }

        const response = await axios.get(`${API_URL}/profiles/me/`)
        if (response.data?.theme_preference) {
          this.setTheme(response.data.theme_preference)
        } else {
          // Default to light if no preference set
          this.setTheme('light')
        }
      } catch (error) {
        console.error('Failed to load theme preference:', error)
        // Default to light theme on error
        this.setTheme('light')
      }
    },

    async saveThemeToProfile(theme) {
      try {
        const token = localStorage.getItem('authToken')
        if (!token) return

        await axios.patch(`${API_URL}/profiles/me/`, {
          theme_preference: theme
        })
      } catch (error) {
        console.error('Failed to save theme preference:', error)
      }
    },

    setTheme(theme) {
      this.currentTheme = theme

      // Save to localStorage for immediate persistence
      localStorage.setItem('theme', theme)

      // The watcher in App.vue will handle updating Vuetify theme
    },

    async toggleTheme() {
      const newTheme = this.currentTheme === 'light' ? 'dark' : 'light'
      this.setTheme(newTheme)

      // Save to profile if user is authenticated
      const token = localStorage.getItem('authToken')
      if (token) {
        try {
          await this.saveThemeToProfile(newTheme)
        } catch (error) {
          console.warn('Could not save theme to profile, but localStorage is updated')
        }
      }
      // For non-authenticated users, theme is already saved to localStorage in setTheme()
    }
  }
})