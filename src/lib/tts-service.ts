// TTS Service for secure Azure Text-to-Speech integration
function isAbortError(err: unknown): boolean {
  if (typeof err !== 'object' || err === null) return false
  const maybe = err as { name?: unknown }
  return typeof maybe.name === 'string' && maybe.name === 'AbortError'
}

export class TTSService {
  private audioContext: AudioContext | null = null
  private currentAudio: HTMLAudioElement | null = null
  private inFlightAbort: AbortController | null = null
  private lastPlayAt = 0
  private unlocked = false
  private backoffUntil = 0
  private cache = new Map<string, { url: string; expiresAt: number }>()

  constructor() {
    // Initialize audio context for better audio handling
    if (typeof window !== 'undefined') {
      this.audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)()
    }
  }

  // Get language code from deck language settings
  private getLanguageCode(languageName: string): string {
    const languageMap: Record<string, string> = {
      'french': 'fr',
      'english': 'en',
      'chinese': 'zh',
      'spanish': 'es',
      'german': 'de',
      'italian': 'it',
      'japanese': 'ja',
      'korean': 'ko',
      'portuguese': 'pt',
      'russian': 'ru'
    }

    return languageMap[languageName.toLowerCase()] || 'en'
  }

  // Extract language from deck language code (e.g., 'fr-FR' -> 'fr')
  private extractLanguageFromCode(languageCode: string): string {
    return languageCode.split('-')[0].toLowerCase()
  }

  // Speak text with automatic language detection
  async speakText(text: string, deckLanguage?: string, fallbackLanguage: string = 'en'): Promise<void> {
    if (!text || typeof window === 'undefined') return

    // Debounce rapid-fire plays
    const now = Date.now()
    if (now < this.backoffUntil) return
    if (now - this.lastPlayAt < 250) return
    this.lastPlayAt = now

    try {
      // Stop any currently playing audio
      this.stop()

      // Ensure audio unlock once per session on user gesture
      if (this.audioContext && this.audioContext.state === 'suspended') {
        try { await this.audioContext.resume(); this.unlocked = true } catch {}
      }

      // Determine language
      let language = fallbackLanguage
      if (deckLanguage) {
        language = this.extractLanguageFromCode(deckLanguage)
      }

      console.log(`TTS: Speaking "${text}" in language: ${language}`)

      // Serve from short-lived cache if available (reduces duplicate fetches)
      const cacheKey = language + '|' + text
      const cached = this.cache.get(cacheKey)
      if (cached && Date.now() < cached.expiresAt) {
        this.stop()
        this.currentAudio = new Audio(cached.url)
        await this.currentAudio.play().catch(() => {})
        return
      }

      // Call our secure backend API
      // Cancel any in-flight
      if (this.inFlightAbort) this.inFlightAbort.abort()
      this.inFlightAbort = new AbortController()
      const response = await fetch('/api/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          language: language
        }),
        signal: this.inFlightAbort.signal
      })

      if (!response.ok) {
        if (response.status === 429) {
          // Back off briefly to avoid hammering
          this.backoffUntil = Date.now() + 500
        }
        throw new Error(`TTS API error: ${response.status}`)
      }

      // Get audio blob from response
      const audioBlob = await response.blob()
      const audioUrl = URL.createObjectURL(audioBlob)

      // Create and play audio
      this.currentAudio = new Audio(audioUrl)
      this.currentAudio.preload = 'auto'

      // Wait for audio to load
      await new Promise((resolve, reject) => {
        if (!this.currentAudio) return reject(new Error('Audio not created'))
        
        this.currentAudio.oncanplaythrough = resolve
        this.currentAudio.onerror = reject
        this.currentAudio.load()
      })

      // Play the audio
      try {
        await this.currentAudio.play()
      } catch {
        // Autoplay blocked; show a minimal prompt in console
        console.warn('Audio play blocked by browser. Prompting user gesture.')
        // Optionally surface a UI prompt elsewhere in app if needed
      }

      // Clean up URL when audio ends
      this.currentAudio.onended = () => {
        URL.revokeObjectURL(audioUrl)
        this.currentAudio = null
      }

      // Cache for 60s
      this.cache.set(cacheKey, { url: audioUrl, expiresAt: Date.now() + 60_000 })

    } catch (error) {
      if (isAbortError(error)) {
        // Ignore expected aborts from cancelling in-flight requests
        return
      }
      console.error('TTS Error:', error)
      // Fallback to browser TTS even on 429 in local testing to keep UX responsive
      this.speakWithBrowser(text, deckLanguage || fallbackLanguage)
    }
  }

  // Browser TTS fallback
  private speakWithBrowser(text: string, language: string): void {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      console.warn('Browser TTS not available')
      return
    }

    // Stop any current speech
    window.speechSynthesis.cancel()

    // Create utterance
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = this.getLanguageLocale(language)
    utterance.rate = 0.9
    utterance.pitch = 1.0
    utterance.volume = 1.0

    // Speak
    window.speechSynthesis.speak(utterance)
  }

  // Get language locale for browser TTS
  private getLanguageLocale(language: string): string {
    const localeMap: Record<string, string> = {
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

    return localeMap[language] || 'en-US'
  }

  // Stop current audio
  stop(): void {
    if (this.currentAudio) {
      this.currentAudio.pause()
      this.currentAudio.currentTime = 0
      this.currentAudio = null
    }

    if (this.inFlightAbort) {
      try { this.inFlightAbort.abort() } catch {}
      this.inFlightAbort = null
    }

    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }
  }

  // Check if TTS is available
  isAvailable(): boolean {
    return typeof window !== 'undefined' && (
      window.speechSynthesis !== undefined || 
      this.audioContext !== null
    )
  }
}

// Export singleton instance
export const ttsService = new TTSService()
