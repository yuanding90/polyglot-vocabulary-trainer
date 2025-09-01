import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { supabase } from "./supabase"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// SRS (Spaced Repetition System) calculations
export const SRS = {
  AGAIN_INTERVAL: 0,
  NEW_WORD_INTERVAL: 1,
  MASTERED_INTERVAL: 365,
  EASE_FACTOR_DEFAULT: 2.5,
  MIN_EASE_FACTOR: 1.3,
  LEECH_THRESHOLD: 4,
  NEAR_FUTURE_THRESHOLD: 3, // Days ahead to pull forward for review
}

export function calculateNextReview(
  currentInterval: number,
  easeFactor: number,
  repetitions: number,
  rating: 'again' | 'hard' | 'good' | 'easy'
): { interval: number; easeFactor: number; repetitions: number } {
  let newInterval: number
  let newEaseFactor: number
  let newRepetitions: number

  switch (rating) {
    case 'again':
      newInterval = SRS.AGAIN_INTERVAL
      newEaseFactor = Math.max(SRS.MIN_EASE_FACTOR, easeFactor - 0.2)
      newRepetitions = 0
      break
    case 'hard':
      newInterval = Math.max(1, Math.ceil(currentInterval / 2))
      newEaseFactor = Math.max(SRS.MIN_EASE_FACTOR, easeFactor - 0.15)
      newRepetitions = repetitions
      break
    case 'good':
      // Proper interval calculation based on repetitions (HTML app logic)
      if (repetitions === 0) {
        newInterval = SRS.NEW_WORD_INTERVAL
      } else if (repetitions === 1) {
        newInterval = 6
      } else {
        newInterval = Math.ceil(currentInterval * easeFactor)
      }
      
      // Proper ease factor calculation (HTML app logic)
      const ratingValue = 4 // good rating
      newEaseFactor = Math.max(
        SRS.MIN_EASE_FACTOR, 
        easeFactor + (0.1 - (5 - ratingValue) * (0.08 + (5 - ratingValue) * 0.02))
      )
      
      newRepetitions = repetitions + 1
      break
    case 'easy':
      // Proper interval calculation based on repetitions (HTML app logic)
      if (repetitions === 0) {
        newInterval = SRS.NEW_WORD_INTERVAL
      } else if (repetitions === 1) {
        newInterval = 6
      } else {
        newInterval = Math.ceil(currentInterval * easeFactor)
      }
      
      // Proper ease factor calculation (HTML app logic)
      const ratingValueEasy = 5 // easy rating
      newEaseFactor = Math.max(
        SRS.MIN_EASE_FACTOR, 
        easeFactor + (0.1 - (5 - ratingValueEasy) * (0.08 + (5 - ratingValueEasy) * 0.02))
      )
      
      newRepetitions = repetitions + 1
      break
    default:
      newInterval = currentInterval
      newEaseFactor = easeFactor
      newRepetitions = repetitions
  }

  return { interval: newInterval, easeFactor: newEaseFactor, repetitions: newRepetitions }
}

export function isDueForReview(nextReviewDate: string): boolean {
  return new Date(nextReviewDate) <= new Date()
}

export function getDaysUntilReview(nextReviewDate: string): number {
  const now = new Date()
  const reviewDate = new Date(nextReviewDate)
  const diffTime = reviewDate.getTime() - now.getTime()
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

export function isNearFuture(nextReviewDate: string): boolean {
  const daysUntil = getDaysUntilReview(nextReviewDate)
  return daysUntil > 0 && daysUntil <= SRS.NEAR_FUTURE_THRESHOLD
}

// Language codes for text-to-speech
export const LANGUAGE_CODES = {
  'Chinese': 'zh-CN',
  'French': 'fr-FR',
  'English': 'en-US',
  'Spanish': 'es-ES',
  'German': 'de-DE',
  'Italian': 'it-IT',
  'Portuguese': 'pt-PT',
  'Russian': 'ru-RU',
  'Japanese': 'ja-JP',
  'Korean': 'ko-KR'
}

export function getLanguageCode(languageName: string): string {
  return LANGUAGE_CODES[languageName as keyof typeof LANGUAGE_CODES] || 'en-US'
}

// Text-to-speech utility (adapted for multi-language)
export function speakText(text: string, languageCode: string = 'en-US') {
  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = languageCode
    utterance.rate = 0.8
    speechSynthesis.speak(utterance)
  }
}

// Date utilities
export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function isToday(date: string | Date): boolean {
  const today = new Date()
  const checkDate = new Date(date)
  return (
    today.getFullYear() === checkDate.getFullYear() &&
    today.getMonth() === checkDate.getMonth() &&
    today.getDate() === checkDate.getDate()
  )
}

// Session utilities
export function getCardType(): 'recognition' | 'production' | 'listening' {
  const types = ['recognition', 'production', 'listening']
  return types[Math.floor(Math.random() * types.length)] as 'recognition' | 'production' | 'listening'
}

export function normalizeText(text: string): string {
  return text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
}

export function checkAnswer(userAnswer: string, correctAnswer: string): boolean {
  const normalizedUser = normalizeText(userAnswer.trim())
  const normalizedCorrect = normalizeText(correctAnswer)
  return normalizedUser === normalizedCorrect
}

// Rating history utilities for leech removal logic
export async function logRating(
  userId: string,
  wordId: string,
  deckId: string,
  rating: 'again' | 'hard' | 'good' | 'easy' | 'learn' | 'know'
): Promise<void> {
  try {
    const { error } = await supabase
      .from('rating_history')
      .insert({
        user_id: userId,
        word_id: wordId, // Keep as UUID string
        deck_id: deckId,
        rating,
        timestamp: new Date().toISOString()
      })

    if (error) {
      // If table doesn't exist, just log a warning instead of error
      if (error.code === '42P01') { // Table doesn't exist
        console.warn('Rating history table not found. Skipping rating log.')
        return
      }
      console.error('Error logging rating:', error)
    }
  } catch (error) {
    // If table doesn't exist, just log a warning instead of error
    if (error instanceof Error && error.message.includes('relation "rating_history" does not exist')) {
      console.warn('Rating history table not found. Skipping rating log.')
      return
    }
    console.error('Error in logRating:', error)
  }
}

export async function getRecentRatings(
  userId: string,
  wordId: string,
  limit: number = 10
): Promise<string[]> {
  try {
    const { data, error } = await supabase
      .from('rating_history')
      .select('rating')
      .eq('user_id', userId)
      .eq('word_id', wordId) // Keep as UUID string
      .order('timestamp', { ascending: false })
      .limit(limit)

    if (error) {
      // If table doesn't exist, just return empty array
      if (error.code === '42P01') { // Table doesn't exist
        console.warn('Rating history table not found. Returning empty ratings.')
        return []
      }
      console.error('Error getting recent ratings:', error)
      return []
    }

    return data?.map(row => row.rating).reverse() || [] // Return in chronological order
  } catch (error) {
    // If table doesn't exist, just return empty array
    if (error instanceof Error && error.message.includes('relation "rating_history" does not exist')) {
      console.warn('Rating history table not found. Returning empty ratings.')
      return []
    }
    console.error('Error in getRecentRatings:', error)
    return []
  }
}

export function shouldRemoveFromLeech(
  rating: 'again' | 'hard' | 'good' | 'easy',
  interval: number,
  recentRatings: string[]
): boolean {
  // Remove from leeches after 2 consecutive 'easy' ratings and interval >= 7 days
  return (
    rating === 'easy' &&
    interval >= 7 &&
    recentRatings.length >= 2 &&
    recentRatings.slice(-2).every(r => r === 'easy')
  )
}
