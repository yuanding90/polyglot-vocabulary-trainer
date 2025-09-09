'use client'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertTriangle } from 'lucide-react'

export default function AuthCodeError() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center text-2xl text-red-600">
            <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
            Authentication Error
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center">
          <p className="text-gray-600 mb-6">
            There was an error processing your authentication request. This could be due to:
          </p>
          
          <ul className="text-left text-sm text-gray-600 mb-6 space-y-2">
            <li>• Invalid or expired authentication code</li>
            <li>• Network connectivity issues</li>
            <li>• Browser security settings</li>
            <li>• Incorrect redirect URL configuration</li>
          </ul>
          
          <div className="space-y-3">
            <Button 
              onClick={() => window.location.href = '/'}
              className="w-full"
            >
              Try Again
            </Button>
            
            <Button 
              variant="outline"
              onClick={() => window.location.href = '/dashboard'}
              className="w-full"
            >
              Go to Dashboard
            </Button>
          </div>
          
          <p className="text-xs text-gray-500 mt-4">
            If the problem persists, please check your internet connection and try again.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

