/**
 * Application Configuration
 * Centralized config for API URLs and other settings
 */

// Ensure API_URL ends with /api
function getApiUrl() {
  let url = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
  // Remove trailing slash if present
  url = url.replace(/\/$/, '')
  // Ensure it ends with /api
  if (!url.endsWith('/api')) {
    url = url + '/api'
  }
  return url
}

export const API_URL = getApiUrl()

// Log in production for debugging
if (import.meta.env.PROD) {
  console.log('[Config] API URL:', API_URL)
}
