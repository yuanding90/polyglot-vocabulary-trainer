'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { User } from '@supabase/supabase-js'
import Auth from '@/components/Auth'
import Dashboard from '@/app/dashboard/page'

export default function Home() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get initial session with error handling
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      if (error) {
        console.log('Session error (this is normal on first load):', error.message)
        // Clear any stale auth data
        supabase.auth.signOut()
      }
      setUser(session?.user ?? null)
      setLoading(false)
    }).catch((error) => {
      console.log('Session fetch error:', error.message)
      // Clear any stale auth data
      supabase.auth.signOut()
      setUser(null)
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    )
  }

  if (!user) {
    return <Auth />
  }

  return <Dashboard />
}
