// File: src/supabaseClient.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://tkjotztgexetfbumfpsv.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRram90enRnZXhldGZidW1mcHN2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDM2ODgyNywiZXhwIjoyMDg5OTQ0ODI3fQ.boUzWf2ItMydr5vRB4FXxgXoQEMpXWIz4WQcolLP6aI'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Helper to initialize auth with token from localStorage (from backend login)
export const initializeAuthSession = async () => {
  const token = localStorage.getItem('token')
  if (!token) return null

  try {
    // Use the token to authenticate Supabase requests
    const { data, error } = await supabase.auth.getUser(token)
    
    if (error || !data.user) {
      console.warn('Token validation failed:', error?.message)
      return null
    }
    
    console.log('✓ Auth initialized with token for user:', data.user.id)
    return data.user
  } catch (err) {
    console.warn('Auth initialization error:', err.message)
    return null
  }
}

