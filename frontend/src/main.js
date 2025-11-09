import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

// Global styles
import './assets/global.css'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          primary: '#2ea3f2',      // Inspyre Hub Blue
          secondary: '#333333',     // Dark Gray/Charcoal
          accent: '#2ea3f2',        // Same as primary
          error: '#F44336',
          warning: '#FF9800',
          info: '#2ea3f2',
          success: '#4CAF50',
          background: '#f3f3f3',    // Light gray background
          surface: '#ffffff',       // White surface
          'on-primary': '#ffffff',  // White text on primary
          'on-secondary': '#ffffff' // White text on secondary
        }
      },
      dark: {
        dark: true,
        colors: {
          primary: '#2ea3f2',      // Inspyre Hub Blue
          secondary: '#4a4a4a',     // Lighter gray for dark mode
          accent: '#2ea3f2',        // Same as primary
          error: '#FF5252',
          warning: '#FFC107',
          info: '#2ea3f2',
          success: '#4CAF50',
          background: '#121212',    // Dark background
          surface: '#1e1e1e',       // Dark surface
          'surface-variant': '#2a2a2a', // Slightly lighter surface
          'on-primary': '#ffffff',  // White text on primary
          'on-secondary': '#ffffff', // White text on secondary
          'on-background': '#e0e0e0', // Light text on dark background
          'on-surface': '#e0e0e0'   // Light text on dark surface
        }
      }
    }
  }
})

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(vuetify)

// Initialize authentication
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
authStore.initializeAuth()

app.mount('#app')