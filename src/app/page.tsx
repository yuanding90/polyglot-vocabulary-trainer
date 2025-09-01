'use client'

import { useEffect } from 'react'

export default function Home() {
  useEffect(() => {
    // Redirect directly to dashboard
    window.location.href = '/dashboard'
  }, [])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-xl">Redirecting to dashboard...</div>
    </div>
  )
}
