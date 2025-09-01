'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ArrowLeft } from 'lucide-react'

export default function StudySession() {
  const [loading, setLoading] = useState(false)

  const onBack = () => {
    window.location.href = '/dashboard'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading session...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <Button onClick={onBack} variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Dashboard
              </Button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Study Session</h1>
                <p className="text-sm text-gray-600">Test session</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto p-6 max-w-4xl">
        <Card>
          <CardContent className="p-8">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-4">Study Session Test</h2>
              <p className="text-gray-600 mb-6">
                This is a test version of the study session page.
              </p>
              <Button onClick={onBack} className="bg-blue-600 hover:bg-blue-700">
                Back to Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
