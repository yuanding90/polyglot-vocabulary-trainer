import { NextRequest, NextResponse } from 'next/server'

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

export async function POST(request: NextRequest) {
  try {
    const { text, language } = await request.json()

    if (!text || !language) {
      return NextResponse.json(
        { error: 'Text and language are required' },
        { status: 400 }
      )
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

    // Call Azure Cognitive Services TTS
    const response = await fetch(
      `https://${region}.tts.speech.microsoft.com/cognitiveservices/v1`,
      {
        method: 'POST',
        headers: {
          'Ocp-Apim-Subscription-Key': subscriptionKey,
          'Content-Type': 'application/ssml+xml',
          'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3'
        },
        body: ssml
      }
    )

    if (!response.ok) {
      console.error('Azure TTS failed:', response.status, response.statusText)
      return NextResponse.json(
        { error: 'TTS service error' },
        { status: 500 }
      )
    }

    // Get the audio blob
    const audioBlob = await response.blob()
    const audioBuffer = await audioBlob.arrayBuffer()

    // Return the audio as a response
    return new NextResponse(audioBuffer, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Cache-Control': 'public, max-age=3600' // Cache for 1 hour
      }
    })

  } catch (error) {
    console.error('TTS API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
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
