/**
 * Firebase Configuration
 *
 * In DEVELOPMENT: Firebase is optional. Leave env vars empty to use password-based auth.
 * In PRODUCTION: Configure Firebase for phone/email verification.
 */

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || '',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || '',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || '',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || '',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || ''
}

// Check if Firebase is configured
export const isFirebaseConfigured = () => {
  return !!(firebaseConfig.apiKey && firebaseConfig.projectId)
}

// Export stubs - these get replaced if Firebase is configured
export let app = null
export let auth = null
export let RecaptchaVerifier = null
export let signInWithPhoneNumber = null
export let signInWithEmailAndPassword = null
export let createUserWithEmailAndPassword = null
export let sendEmailVerification = null

// Initialize Firebase only if configured
export const initializeFirebase = async () => {
  if (!isFirebaseConfigured()) {
    console.log('[DEV MODE] Firebase not configured - using password-based authentication')
    return false
  }

  try {
    const { initializeApp } = await import('firebase/app')
    const firebaseAuth = await import('firebase/auth')

    app = initializeApp(firebaseConfig)
    auth = firebaseAuth.getAuth(app)
    RecaptchaVerifier = firebaseAuth.RecaptchaVerifier
    signInWithPhoneNumber = firebaseAuth.signInWithPhoneNumber
    signInWithEmailAndPassword = firebaseAuth.signInWithEmailAndPassword
    createUserWithEmailAndPassword = firebaseAuth.createUserWithEmailAndPassword
    sendEmailVerification = firebaseAuth.sendEmailVerification

    console.log('[Firebase] Initialized successfully')
    return true
  } catch (error) {
    console.error('[Firebase] Failed to initialize:', error)
    return false
  }
}

// Auto-initialize if configured
if (isFirebaseConfigured()) {
  initializeFirebase()
}
