// TTS Service for secure Azure Text-to-Speech integration
export class TTSService {
  private audioContext: AudioContext | null = null
  private currentAudio: HTMLAudioElement | null = null

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

    try {
      // Stop any currently playing audio
      this.stop()

      // Determine language
      let language = fallbackLanguage
      if (deckLanguage) {
        language = this.extractLanguageFromCode(deckLanguage)
      }

      console.log(`TTS: Speaking "${text}" in language: ${language}`)

      // Call our secure backend API
      const response = await fetch('/api/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          language: language
        })
      })

      if (!response.ok) {
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
      await this.currentAudio.play()

      // Clean up URL when audio ends
      this.currentAudio.onended = () => {
        URL.revokeObjectURL(audioUrl)
        this.currentAudio = null
      }

    } catch (error) {
      console.error('TTS Error:', error)
      
      // Fallback to browser TTS
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
