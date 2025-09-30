import { NextRequest, NextResponse } from 'next/server'
export const runtime = 'nodejs'

// Rate limiting and quota management
const RATE_LIMIT_WINDOW = 60 * 1000 // 1 minute
const MAX_REQUESTS_PER_MINUTE = 10 // Conservative limit
const MAX_REQUESTS_PER_MONTH = 1000 // Conservative monthly limit

// In-memory rate limiting (for production, use Redis or database)
const rateLimitStore = new Map<string, { count: number; resetTime: number }>()
const monthlyQuotaStore = new Map<string, { count: number; month: string }>()

// Language to Azure voice mapping
const LANGUAGE_VOICES: Record<string, string> = {
  'fr': 'fr-FR-DeniseNeural',
  'en': 'en-US-JennyNeural',
  'zh': 'zh-CN-XiaoxiaoNeural',
  'es': 'es-ES-ElviraNeural',
  'de': 'de-DE-KatjaNeural',
  'it': 'it-IT-ElsaNeural',
  'ja': 'ja-JP-NanamiNeural',
  'ko': 'ko-KR-SunHiNeural',
  'pt': 'pt-BR-FranciscaNeural',
  'ru': 'ru-RU-SvetlanaNeural'
}

// Language to Azure locale mapping
const LANGUAGE_LOCALES: Record<string, string> = {
  'fr': 'fr-FR',
  'en': 'en-US',
  'zh': 'zh-CN',
  'es': 'es-ES',
  'de': 'de-DE',
  'it': 'it-IT',
  'ja': 'ja-JP',
  'ko': 'ko-KR',
  'pt': 'pt-BR',
  'ru': 'ru-RU'
}

// Rate limiting function
function checkRateLimit(identifier: string): { allowed: boolean; remaining: number; resetTime: number } {
  const now = Date.now()
  const current = rateLimitStore.get(identifier)
  
  if (!current || now > current.resetTime) {
    // Reset or initialize
    rateLimitStore.set(identifier, { count: 1, resetTime: now + RATE_LIMIT_WINDOW })
    return { allowed: true, remaining: MAX_REQUESTS_PER_MINUTE - 1, resetTime: now + RATE_LIMIT_WINDOW }
  }
  
  if (current.count >= MAX_REQUESTS_PER_MINUTE) {
    return { allowed: false, remaining: 0, resetTime: current.resetTime }
  }
  
  current.count++
  return { allowed: true, remaining: MAX_REQUESTS_PER_MINUTE - current.count, resetTime: current.resetTime }
}

// Monthly quota check
function checkMonthlyQuota(identifier: string): { allowed: boolean; remaining: number } {
  const now = new Date()
  const currentMonth = `${now.getFullYear()}-${now.getMonth()}`
  const current = monthlyQuotaStore.get(identifier)
  
  if (!current || current.month !== currentMonth) {
    // Reset for new month
    monthlyQuotaStore.set(identifier, { count: 1, month: currentMonth })
    return { allowed: true, remaining: MAX_REQUESTS_PER_MONTH - 1 }
  }
  
  if (current.count >= MAX_REQUESTS_PER_MONTH) {
    return { allowed: false, remaining: 0 }
  }
  
  current.count++
  return { allowed: true, remaining: MAX_REQUESTS_PER_MONTH - current.count }
}

export async function POST(request: NextRequest) {
  try {
    const { text, language } = await request.json()

    if (!text || !language) {
      return NextResponse.json(
        { error: 'Text and language are required' },
        { status: 400 }
      )
    }

    // Rate limit & quota (bypass in development for easier local testing)
    const isDev = process.env.NODE_ENV !== 'production'
    const clientIP = request.headers.get('x-forwarded-for') || 
                    request.headers.get('x-real-ip') || 
                    'unknown'
    let rateLimit = { allowed: true, remaining: MAX_REQUESTS_PER_MINUTE, resetTime: Date.now() + RATE_LIMIT_WINDOW }
    let quotaCheck = { allowed: true, remaining: MAX_REQUESTS_PER_MONTH }
    if (!isDev) {
      rateLimit = checkRateLimit(clientIP)
      if (!rateLimit.allowed) {
        return NextResponse.json(
          { 
            error: 'Rate limit exceeded', 
            remaining: rateLimit.remaining,
            resetTime: rateLimit.resetTime 
          },
          { status: 429 }
        )
      }
      quotaCheck = checkMonthlyQuota(clientIP)
      if (!quotaCheck.allowed) {
        return NextResponse.json(
          { 
            error: 'Monthly quota exceeded', 
            remaining: quotaCheck.remaining 
          },
          { status: 429 }
        )
      }
    }

    // Get Azure configuration from environment variables
    const subscriptionKey = process.env.AZURE_SPEECH_KEY
    const region = process.env.AZURE_SPEECH_REGION || 'eastus'

    if (!subscriptionKey) {
      console.error('Azure Speech API key not configured')
      return NextResponse.json(
        { error: 'TTS service not configured' },
        { status: 500 }
      )
    }

    // Get voice and locale for the language
    const voice = LANGUAGE_VOICES[language] || LANGUAGE_VOICES['en']
    const locale = LANGUAGE_LOCALES[language] || LANGUAGE_LOCALES['en']

    // Prepare SSML for Azure TTS
    const ssml = `
      <speak version='1.0' xml:lang='${locale}'>
        <voice xml:lang='${locale}' xml:gender='Female' name='${voice}'>
          <break time="100ms"/>
          ${escapeXml(text)}
        </voice>
      </speak>
    `

    // Call Azure Cognitive Services TTS with timeout and one retry on 429
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 10000)
    const endpoint = `https://${region}.tts.speech.microsoft.com/cognitiveservices/v1`
    const start = Date.now()
    let response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Ocp-Apim-Subscription-Key': subscriptionKey,
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3'
      },
      body: ssml,
      signal: controller.signal
    })
    clearTimeout(timeout)

    // Retry once on 429 with small backoff
    if (response.status === 429) {
      await new Promise(r => setTimeout(r, 300))
      const retryController = new AbortController()
      const retryTimeout = setTimeout(() => retryController.abort(), 10000)
      response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Ocp-Apim-Subscription-Key': subscriptionKey,
          'Content-Type': 'application/ssml+xml',
          'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3'
        },
        body: ssml,
        signal: retryController.signal
      })
      clearTimeout(retryTimeout)
    }

    if (!response.ok) {
      const dur = Date.now() - start
      console.error('Azure TTS failed:', { status: response.status, statusText: response.statusText, durationMs: dur })
      const status = response.status
      if (status === 401 || status === 403) {
        return NextResponse.json({ error: 'Unauthorized to TTS provider' }, { status })
      }
      if (status === 429) {
        return NextResponse.json({ error: 'TTS rate limited' }, { status })
      }
      return NextResponse.json({ error: 'TTS service error' }, { status: 502 })
    }

    // Get the audio blob
    const audioBlob = await response.blob()
    const audioBuffer = await audioBlob.arrayBuffer()

    // Return the audio as a response with rate limit headers
    return new NextResponse(audioBuffer, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
        'X-RateLimit-Remaining': rateLimit.remaining.toString(),
        'X-RateLimit-Reset': rateLimit.resetTime.toString(),
        'X-Quota-Remaining': quotaCheck.remaining.toString()
      }
    })

  } catch (error) {
    const isAbort = error instanceof Error && (error.name === 'AbortError')
    console.error('TTS API error:', error)
    return NextResponse.json(
      { error: isAbort ? 'TTS request timeout' : 'Internal server error' },
      { status: isAbort ? 504 : 500 }
    )
  }
}

// Helper function to escape XML
function escapeXml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}
