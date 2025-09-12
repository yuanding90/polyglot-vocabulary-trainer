'use client'

import { useState, useEffect, useCallback, startTransition } from 'react'
import { useVocabularyStore } from '@/store/vocabulary-store'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  ArrowLeft,
  Volume2,
  AlertTriangle
} from 'lucide-react'
import { 
  SRS, 
  calculateNextReview, 
  logRating,
  isDueForReview,
  isNearFuture
} from '@/lib/utils'
import { DailySummaryManager } from '@/lib/daily-summary'
import { SimilarWordsPanel } from '@/components/SimilarWordsPanel'
import { ttsService } from '@/lib/tts-service'

import { Vocabulary, VocabularyDeck, UserProgress } from '@/lib/supabase'
// Removed unused User import


interface SessionProgress {
  total: number
  reviewed: number
  again: number
  hard: number
  good: number
  easy: number
  learn: number
  know: number
}

export default function StudySession() {
  const { sessionSettings } = useVocabularyStore()
  
  // Debug session settings
  console.log('Session settings in study session:', sessionSettings)
  const [currentWordIndex, setCurrentWordIndex] = useState(0)
  const [sessionWords, setLocalSessionWords] = useState<Vocabulary[]>([])
  const [loading, setLoading] = useState(true)
  const [showAnswer, setShowAnswer] = useState(false)
  const [cardType, setCardType] = useState<'recognition' | 'production' | 'listening'>('recognition')
  const [userAnswer, setUserAnswer] = useState('')
  const [isCorrect, setIsCorrect] = useState(false)
  const [sessionProgress, setSessionProgress] = useState<SessionProgress>({
    total: 0,
    reviewed: 0,
    again: 0,
    hard: 0,
    good: 0,
    easy: 0,
    learn: 0,
    know: 0
  })
  
  // Track session activity for daily summary
  const [sessionActivity, setSessionActivity] = useState({
    reviewsDone: 0,
    newWordsLearned: 0
  })
  const [currentWord, setCurrentWordState] = useState<Vocabulary | null>(null)
  const [currentWordProgress, setCurrentWordProgress] = useState<{ again_count: number } | null>(null) // Track current word's progress
  const [sessionType, setSessionType] = useState<'review' | 'discovery' | 'deep-dive'>('discovery')
  const [deepDiveCategory, setDeepDiveCategory] = useState<'leeches' | 'learning' | 'strengthening' | 'consolidating' | null>(null)
  const [currentDeck, setCurrentDeck] = useState<VocabularyDeck | null>(null)
  // Removed currentUser state - getting user inside each function like French app

  useEffect(() => {
    // Get session type from localStorage
    const storedSessionType = localStorage.getItem('sessionType') as 'review' | 'discovery' | 'deep-dive'
    if (storedSessionType) {
      setSessionType(storedSessionType)
    }
    
    // Get deep dive category if it exists
    const storedDeepDiveCategory = localStorage.getItem('deepDiveCategory') as 'leeches' | 'learning' | 'strengthening' | 'consolidating' | null
    if (storedDeepDiveCategory) {
      setDeepDiveCategory(storedDeepDiveCategory)
    }

    // Get current deck from localStorage
    const storedDeck = localStorage.getItem('selectedDeck')
    if (storedDeck) {
      try {
        const deck = JSON.parse(storedDeck)
        setCurrentDeck(deck)
        console.log('Loaded deck from localStorage:', deck.name, 'ID:', deck.id)
      } catch (error) {
        console.error('Error parsing stored deck:', error)
      }
    } else {
      console.log('No deck found in localStorage')
    }
  }, [])

  // Load session words when currentDeck is available
  useEffect(() => {
    if (currentDeck) {
      console.log('CurrentDeck available, loading session words')
      loadSessionWords()
    } else {
      console.log('Waiting for currentDeck:', { 
        hasDeck: !!currentDeck,
        deckId: null
      })
    }
  }, [currentDeck, sessionType])

  // Listen for localStorage changes to reload when deck changes
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'selectedDeck' && e.newValue) {
        try {
          const newDeck = JSON.parse(e.newValue)
          if (newDeck.id !== currentDeck?.id) {
            console.log('Deck changed in localStorage, reloading session:', newDeck)
            setCurrentDeck(newDeck)
            // Clear session words to force reload
            setLocalSessionWords([])
            setCurrentWordState(null)
            setCurrentWordIndex(0)
            setShowAnswer(false)
            setUserAnswer('')
            setIsCorrect(false)
          }
        } catch (error) {
          console.error('Error parsing new deck from localStorage:', error)
        }
      }
    }

    // Also check localStorage on focus (for when user switches tabs/windows)
    const handleFocus = () => {
      const storedDeck = localStorage.getItem('selectedDeck')
      if (storedDeck) {
        try {
          const deck = JSON.parse(storedDeck)
          if (deck.id !== currentDeck?.id) {
            console.log('Deck changed on focus, reloading session:', deck)
            setCurrentDeck(deck)
            setLocalSessionWords([])
            setCurrentWordState(null)
            setCurrentWordIndex(0)
            setShowAnswer(false)
            setUserAnswer('')
            setIsCorrect(false)
          }
        } catch (error) {
          console.error('Error parsing deck on focus:', error)
        }
      }
    }

    window.addEventListener('storage', handleStorageChange)
    window.addEventListener('focus', handleFocus)

    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('focus', handleFocus)
    }
  }, [currentDeck])

  const onBack = async () => {
    // Save session summary before leaving
    if (sessionProgress.total > 0) {
      console.log('Saving session summary before leaving...')
      await saveSessionSummary()
    }
    
    // Clear session data from localStorage
    localStorage.removeItem('sessionType')
    localStorage.removeItem('deepDiveCategory')
    window.location.href = '/dashboard'
  }

  const handleSignOut = async () => {
    try {
      await supabase.auth.signOut()
      console.log('User signed out successfully')
      // Redirect to main sign-in page
      window.location.href = '/'
    } catch (error) {
      console.error('Error signing out:', error)
      // Still redirect even if there's an error
      window.location.href = '/'
    }
  }

  // Fisher-Yates shuffle for better randomization
  const shuffleArray = (array: Vocabulary[]) => {
    const shuffled = [...array]
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
    }
    return shuffled
  }

  // Apply smart spacing for leeches to prevent fatigue (same as session-queues.ts)
  const applyLeechSpacing = (words: Vocabulary[], progressMap: Map<number, UserProgress>): Vocabulary[] => {
    // Separate leeches from regular words
    const leeches: Vocabulary[] = []
    const regularWords: Vocabulary[] = []
    
    words.forEach(word => {
      const progress = progressMap.get(word.id)
      const isLeech = progress && progress.again_count >= 4
      
      if (isLeech) {
        leeches.push(word)
      } else {
        regularWords.push(word)
      }
    })
    
    // Shuffle both arrays
    leeches.sort(() => Math.random() - 0.5)
    regularWords.sort(() => Math.random() - 0.5)
    
    // Apply spacing: insert leeches every 3-5 regular words
    const spacedWords: Vocabulary[] = []
    const spacingRange = { min: 3, max: 5 }
    let leechIndex = 0
    let regularIndex = 0
    let wordsSinceLastLeech = 0
    
    while (leechIndex < leeches.length || regularIndex < regularWords.length) {
      // Decide whether to add a leech or regular word
      const shouldAddLeech = leechIndex < leeches.length && 
                           (wordsSinceLastLeech >= spacingRange.min || regularIndex >= regularWords.length)
      
      if (shouldAddLeech) {
        spacedWords.push(leeches[leechIndex])
        leechIndex++
        wordsSinceLastLeech = 0
      } else if (regularIndex < regularWords.length) {
        spacedWords.push(regularWords[regularIndex])
        regularIndex++
        wordsSinceLastLeech++
      }
    }
    
    return spacedWords
  }

  const loadSessionWords = useCallback(async () => {
    if (!currentDeck) {
      console.log('No current deck found')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      console.log('Loading session words for deck:', currentDeck.id, 'deck name:', currentDeck.name, 'session type:', sessionType)
      
      // Get current user inside the function (like French app does)
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        console.error('No authenticated user found')
        setLoading(false)
        return
      }
      
      console.log('Study session: Using user:', user.email, 'ID:', user.id)
      
      // Get all vocabulary for the deck (like French app does)
      const { data: deckVocab, error: deckError } = await supabase
        .from('deck_vocabulary')
        .select('vocabulary_id')
        .eq('deck_id', currentDeck.id)
        .order('word_order')

      if (deckError) {
        console.error('Error fetching deck vocabulary:', deckError)
        setLoading(false)
        return
      }

      const vocabIds = deckVocab.map(item => item.vocabulary_id)

      // Get vocabulary words
      const { data: words, error: wordsError } = await supabase
        .from('vocabulary')
        .select('*')
        .in('id', vocabIds)

      if (wordsError) {
        console.error('Error fetching vocabulary words:', wordsError)
        setLoading(false)
        return
      }

      console.log('Loaded words:', words?.length || 0)

      if (words && words.length > 0) {
        // Filter words based on session type (like French app does)
        let filteredWords = words
        let userProgress: UserProgress[] = []
        
        // Get user progress for this deck
        const { data: progressData, error: progressError } = await supabase
          .from('user_progress')
          .select('*')
          .eq('user_id', user.id)
          .eq('deck_id', currentDeck.id)

        if (!progressError && progressData) {
          userProgress = progressData
          
          if (sessionType === 'review') {
            // Use the same logic as the dashboard for consistency
            const progressMap = new Map(userProgress.map(p => [p.word_id, p]))
            
            // Build review queue using the same logic as session-queues.ts
            const reviewWords: Vocabulary[] = []
            const nearFutureWords: Vocabulary[] = []
            
            words.forEach(word => {
              const progress = progressMap.get(word.id)
              
              if (progress) {
                // Has progress - check if due for review using the same function as dashboard
                if (isDueForReview(progress.next_review_date)) {
                  reviewWords.push(word)
                } else if (isNearFuture(progress.next_review_date)) {
                  nearFutureWords.push(word)
                }
              }
            })
            
            // If no Due Now words, use Due Soon words for review (same as dashboard)
            if (reviewWords.length === 0 && nearFutureWords.length > 0) {
              console.log(`No Due Now words, using ${nearFutureWords.length} Due Soon words for review`)
              filteredWords = nearFutureWords
            } else {
              filteredWords = reviewWords
            }
            
            // Apply leech spacing to match dashboard behavior
            filteredWords = applyLeechSpacing(filteredWords, progressMap)
            
            console.log(`Review session: Using ${filteredWords.length} words (${reviewWords.length} due now, ${nearFutureWords.length} due soon)`)
          } else if (sessionType === 'discovery') {
            // For discovery sessions, exclude words that have already been learned
            const learnedWordIds = userProgress.map(p => p.word_id)
            filteredWords = words.filter(word => !learnedWordIds.includes(word.id))
            console.log(`Discovery session: Using ${filteredWords.length} unseen words`)
          } else if (sessionType === 'deep-dive' && deepDiveCategory) {
            // For deep dive, filter based on selected category
            const progressMap = new Map(userProgress.map(p => [p.word_id, p]))
            
            filteredWords = words.filter(word => {
              const progress = progressMap.get(word.id)
              if (!progress) return false
              
              switch (deepDiveCategory) {
                case 'leeches':
                  return progress.again_count >= 3
                case 'learning':
                  return progress.again_count < 3 && progress.interval < 7
                case 'strengthening':
                  return progress.again_count < 3 && progress.interval >= 7 && progress.interval < 21
                case 'consolidating':
                  return progress.again_count < 3 && progress.interval >= 21 && progress.interval < 60
                default:
                  return false
              }
            })
            console.log(`Deep dive session: Found ${filteredWords.length} words for category ${deepDiveCategory}`)
          }
        } else {
          // No progress data - for new users or new decks
          if (sessionType === 'review') {
            // For new users, review session should use unseen words
            filteredWords = words
            console.log(`Review session (new user): Using all ${words.length} words`)
          } else if (sessionType === 'discovery') {
            // Discovery session uses all words for new users
            filteredWords = words
            console.log(`Discovery session (new user): Using all ${words.length} words`)
          }
        }

        // Shuffle the words for better randomization
        const shuffledWords = shuffleArray(filteredWords)
        console.log(`Shuffled ${shuffledWords.length} words for ${sessionType} session`)
        
        setLocalSessionWords(shuffledWords)
        setSessionProgress(prev => ({ ...prev, total: shuffledWords.length }))

        if (shuffledWords.length > 0) {
          setCurrentWordState(shuffledWords[0])
          setCurrentWordIndex(0)
          setShowAnswer(false) // Ensure answer is hidden for new word
          setUserAnswer('')
          setIsCorrect(false)
          
          // Load progress for the first word
          await loadCurrentWordProgress(shuffledWords[0])
          
          // Set initial card type based on session settings
          if (sessionSettings.types.length > 0) {
            const randomType = sessionSettings.types[Math.floor(Math.random() * sessionSettings.types.length)]
            console.log('Setting initial card type:', randomType, 'from available types:', sessionSettings.types)
            setCardType(randomType)
          } else {
            console.log('No session types selected for initial card, using default recognition')
            setCardType('recognition')
          }
        }
      } else {
        console.log('No words found for deck')
        setLocalSessionWords([])
      }

    } catch (error) {
      console.error('Error loading session words:', error)
    } finally {
      setLoading(false)
    }
  }, [currentDeck, sessionType, deepDiveCategory, sessionSettings.types])

  const loadCurrentWordProgress = async (word: Vocabulary) => {
    if (!word || !currentDeck) return
    
    try {
      // Get current user inside the function
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return
      
      // Get the word's progress
      const { data: progress } = await supabase
        .from('user_progress')
        .select('*')
        .eq('user_id', user.id)
        .eq('word_id', word.id)
        .eq('deck_id', currentDeck.id)
        .single()
      
      setCurrentWordProgress(progress || { again_count: 0 })
    } catch (error) {
      console.log('No progress found for word, setting default:', error)
      setCurrentWordProgress({ again_count: 0 })
    }
  }

  const speakWord = async (text: string | undefined, language?: string) => {
    if (!text) return
    
    let langCode = language
    if (language === 'auto' || !language) {
      // Auto-detect based on current deck
      langCode = currentDeck?.language_a_code || 'en'
    }
    
    await ttsService.speakText(text, langCode)
  }



  const markWordAsLeech = async (word: Vocabulary) => {
    if (!currentDeck) return

    try {
      // Get current user inside the function (like French app does)
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        console.log('No authenticated user found')
        return
      }
      
      // Get current progress
      const { data: currentProgress } = await supabase
        .from('user_progress')
        .select('*')
        .eq('user_id', user.id)
        .eq('word_id', word.id)
        .eq('deck_id', currentDeck.id)
        .single()

      const progressData = {
        user_id: user.id,
        word_id: word.id,
        deck_id: currentDeck.id,
        repetitions: currentProgress?.repetitions || 0,
        interval: currentProgress?.interval || 0,

        ease_factor: currentProgress?.ease_factor || SRS.EASE_FACTOR_DEFAULT,
        next_review_date: currentProgress?.next_review_date || new Date().toISOString(),
        again_count: 4 // Mark as leech by setting again_count to threshold
      }

      const { error } = await supabase
        .from('user_progress')
        .upsert(progressData, { onConflict: 'user_id,word_id,deck_id' })

      if (error) {
        console.error('Error marking word as leech:', error)
      } else {
        console.log('Word marked as leech:', word.language_a_word)
      }

      // Move to next word after marking as leech
      await moveToNextWord()

    } catch (error) {
      console.error('Error marking word as leech:', error)
    }
  }

  const removeWordFromLeech = async (word: Vocabulary) => {
    if (!currentDeck) return

    try {
      // Get current user inside the function (like French app does)
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        console.log('No authenticated user found')
        return
      }
      
      // Get current progress
      const { data: currentProgress } = await supabase
        .from('user_progress')
        .select('*')
        .eq('user_id', user.id)
        .eq('word_id', word.id)
        .eq('deck_id', currentDeck.id)
        .single()

      const progressData = {
        user_id: user.id,
        word_id: word.id,
        deck_id: currentDeck.id,
        repetitions: currentProgress?.repetitions || 0,
        interval: currentProgress?.interval || 0,
        ease_factor: currentProgress?.ease_factor || SRS.EASE_FACTOR_DEFAULT,
        next_review_date: currentProgress?.next_review_date || new Date().toISOString(),
        again_count: 0 // Remove from leeches by resetting again_count to 0
      }

      const { error } = await supabase
        .from('user_progress')
        .upsert(progressData, { onConflict: 'user_id,word_id,deck_id' })

      if (error) {
        console.error('Error removing word from leeches:', error)
      } else {
        console.log('Word removed from leeches:', word.language_a_word)
      }

      // Move to next word after removing from leeches
      await moveToNextWord()

    } catch (error) {
      console.error('Error removing word from leeches:', error)
    }
  }

  const handleAnswer = async (rating: 'again' | 'hard' | 'good' | 'easy' | 'learn' | 'know' | 'leech' | 'remove-leech') => {
    if (!currentWord || !currentDeck) return

    try {
      // Get current user inside the function (like French app does)
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        console.log('No authenticated user found')
        return
      }
      
      // Handle leech actions
      if (rating === 'leech') {
        await markWordAsLeech(currentWord)
        return
      }

      if (rating === 'remove-leech') {
        await removeWordFromLeech(currentWord)
        return
      }

      // Update session progress
      setSessionProgress(prev => ({
        ...prev,
        reviewed: prev.reviewed + 1,
        [rating]: prev[rating as keyof SessionProgress] + 1
      }))
      
      // Track session activity for daily summary
      if (sessionType === 'review') {
        setSessionActivity(prev => ({
          ...prev,
          reviewsDone: prev.reviewsDone + 1
        }))
      } else if (sessionType === 'discovery' && (rating === 'learn' || rating === 'know')) {
        setSessionActivity(prev => ({
          ...prev,
          newWordsLearned: prev.newWordsLearned + 1
        }))
      }

      // Handle "Again" logic - add word back to session queue for immediate review
      if (rating === 'again') {
        // Add the current word back to the end of the session queue
        const updatedSessionWords = [...sessionWords, currentWord]
        setLocalSessionWords(updatedSessionWords)
        // Update session progress total to include the added word
        setSessionProgress(prev => ({ ...prev, total: prev.total + 1 }))
        console.log('Word marked as "Again" - added back to session queue for immediate review')
        console.log('Updated session words length:', updatedSessionWords.length)
      }

      let newInterval = 0
      let newEaseFactor = SRS.EASE_FACTOR_DEFAULT
      let newRepetitions = 0
      let newAgainCount = 0
      
      // Get current progress for all session types (needed for date calculation)
      const { data: currentProgress } = await supabase
        .from('user_progress')
        .select('*')
        .eq('user_id', user.id)
        .eq('word_id', currentWord.id)
        .eq('deck_id', currentDeck.id)
        .single()

      if (sessionType === 'review') {

        if (currentProgress) {
          newAgainCount = currentProgress.again_count
          if (rating === 'again') {
            newAgainCount += 1
          }
        }

        // Calculate new interval and ease factor
        const result = calculateNextReview(
          currentProgress?.interval || 0,
          currentProgress?.ease_factor || SRS.EASE_FACTOR_DEFAULT,
          currentProgress?.repetitions || 0,
          rating as 'again' | 'hard' | 'good' | 'easy'
        )
        newInterval = result.interval
        newEaseFactor = result.easeFactor
        newRepetitions = result.repetitions

        // Log the rating for review sessions
        await logRating(user.id, currentWord.id.toString(), currentDeck.id, rating as 'again' | 'hard' | 'good' | 'easy')

      } else if (sessionType === 'discovery') {
        // Discovery session logic
        if (rating === 'know') {
          newInterval = SRS.MASTERED_INTERVAL
          newEaseFactor = SRS.EASE_FACTOR_DEFAULT
          newRepetitions = 1
        } else {
          newInterval = 0
          newEaseFactor = SRS.EASE_FACTOR_DEFAULT
          newRepetitions = 0
        }

        // Log the rating for discovery sessions
        await logRating(user.id, currentWord.id.toString(), currentDeck.id, rating as 'learn' | 'know')
      }

      // Calculate next review date based on whether this was a "Due Now" or "Due Soon" word
      let nextReviewDate = new Date()
      
      // Check if this word was originally "Due Soon" (not due today)
      const originalDueDate = new Date(currentProgress?.next_review_date || new Date())
      const wasDueSoon = originalDueDate > new Date()
      
      if (newInterval > 0) {
        if (wasDueSoon) {
          // For "Due Soon" words, calculate from the original due date to preserve spacing
          nextReviewDate = new Date(originalDueDate)
          nextReviewDate.setDate(nextReviewDate.getDate() + newInterval)
          console.log(`Due Soon word reviewed early: original due ${originalDueDate.toDateString()}, new due ${nextReviewDate.toDateString()}`)
        } else {
          // For "Due Now" words, calculate from today (normal behavior)
          nextReviewDate.setDate(nextReviewDate.getDate() + newInterval)
          console.log(`Due Now word reviewed: new due ${nextReviewDate.toDateString()}`)
        }
      }

      // Log the data being sent for debugging
      console.log('Word ID before conversion:', currentWord.id, 'Type:', typeof currentWord.id)
      
      const progressData = {
        user_id: user.id,
        word_id: currentWord.id, // ID is already a number
        deck_id: currentDeck.id,
        repetitions: newRepetitions,
        interval: newInterval,
        ease_factor: newEaseFactor,
        next_review_date: nextReviewDate.toISOString(),
        again_count: newAgainCount
      }
      
      console.log('Attempting to save progress with data:', progressData)

      // Upsert progress
      const { error } = await supabase
        .from('user_progress')
        .upsert(progressData, { onConflict: 'user_id,word_id,deck_id' })

      if (error) {
        console.error('Error saving word progress:', error)
      }

      // Move to next word
      if (rating === 'again') {
        // For "Again", use the updated session words array
        const updatedSessionWords = [...sessionWords, currentWord]
        await moveToNextWord(updatedSessionWords)
      } else {
        await moveToNextWord()
      }

    } catch (error) {
      console.error('Error handling answer:', error)
    }
  }

  const saveSessionSummary = async () => {
    if (!currentDeck) return

    try {
      // Get current user inside the function (like French app does)
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        console.log('No authenticated user found')
        return
      }
      
      const sessionData = {
        user_id: user.id,
        deck_id: currentDeck.id,
        session_type: sessionType,
        words_studied: sessionWords.length,
        correct_answers: sessionProgress.good + sessionProgress.easy + sessionProgress.know,
        session_duration: 0, // TODO: Calculate actual duration
        completed_at: new Date().toISOString()
      }
      
      console.log('Saving session summary with data:', sessionData)
      
      const { error } = await supabase
        .from('study_sessions')
        .insert(sessionData)

      if (error) {
        console.error('Error saving session summary:', error)
        console.error('Error details:', error)
      } else {
        console.log('Session summary saved successfully')
      }
      
      // Log daily summary if there was any activity
      if (sessionActivity.reviewsDone > 0 || sessionActivity.newWordsLearned > 0) {
        await DailySummaryManager.logDailySummary(
          user.id,
          sessionActivity.reviewsDone,
          sessionActivity.newWordsLearned
        )
      }
    } catch (error) {
      console.error('Error in saveSessionSummary:', error)
    }
  }

  const moveToNextWord = async (updatedSessionWords?: Vocabulary[]) => {
    const nextIndex = currentWordIndex + 1
    const currentSessionWords = updatedSessionWords || sessionWords
    
    console.log('moveToNextWord called:', {
      nextIndex,
      currentSessionWordsLength: currentSessionWords.length,
      sessionWordsLength: sessionWords.length,
      hasUpdatedWords: !!updatedSessionWords
    })
    
    // Check if there are more words in the current session (including words added back with "Again")
    if (nextIndex < currentSessionWords.length) {
      startTransition(() => {
        // All state updates happen together atomically
        setCurrentWordIndex(nextIndex)
        setCurrentWordState(currentSessionWords[nextIndex])
        setShowAnswer(false)
        setUserAnswer('')
        setIsCorrect(false)
      })
      
      // Load progress for the next word
      await loadCurrentWordProgress(currentSessionWords[nextIndex])
      
      // Set card type for next word
      if (sessionSettings.types.length > 0) {
        const randomType = sessionSettings.types[Math.floor(Math.random() * sessionSettings.types.length)]
        console.log('Setting card type for next word:', randomType, 'from available types:', sessionSettings.types)
        setCardType(randomType)
      } else {
        console.log('No session types selected, using default recognition')
        setCardType('recognition')
      }
    } else {
      // Session complete - only when we've gone through all words in the current session
      console.log('Session complete! Processed', currentSessionWords.length, 'words total')
      await saveSessionSummary()
      onBack()
    }
  }

  const currentWordData = currentWord ? {
    id: currentWord.id,
    language_a_word: currentWord.language_a_word,
    language_b_translation: currentWord.language_b_translation,
    language_a_sentence: currentWord.language_a_sentence,
    language_b_sentence: currentWord.language_b_sentence,
    created_at: currentWord.created_at,
    updated_at: currentWord.updated_at
  } : null

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading session...</div>
      </div>
    )
  }

  if (sessionWords.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
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
                  <p className="text-sm text-gray-600">{sessionType} session</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <Button 
                  onClick={handleSignOut}
                  variant="outline"
                  size="sm"
                  className="text-red-600 border-red-300 hover:bg-red-50"
                >
                  Sign Out
                </Button>
              </div>
            </div>
          </div>
        </header>

        <div className="container mx-auto p-6 max-w-4xl">
          <Card>
            <CardContent className="p-8">
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-4">No words available for this session</h2>
                <p className="text-gray-600 mb-6">
                  {sessionType === 'review' ? 'No words are due for review at this time.' :
                   sessionType === 'discovery' ? 'No unseen words available for discovery.' :
                   'No words available for the selected category.'}
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <Button onClick={onBack} variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                End Session
              </Button>
              <div className="text-sm text-gray-600">
                {currentWordIndex + 1} / {sessionWords.length}
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Button 
                onClick={handleSignOut}
                variant="outline"
                size="sm"
                className="text-red-600 border-red-300 hover:bg-red-50"
              >
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto p-6 max-w-4xl">
        {/* Session Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {sessionType.charAt(0).toUpperCase() + sessionType.slice(1)} Session
          </h1>
          <p className="text-gray-600">
            {currentDeck?.name} • {sessionWords.length} words in session
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{Math.round((sessionProgress.reviewed / sessionWords.length) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(sessionProgress.reviewed / sessionWords.length) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Dynamic Session Progress Visualization */}
        {sessionType === 'review' && (
          <div className="mb-8">
            {/* Overall Statistics */}
            <div className="grid grid-cols-6 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-700">{sessionWords.length - currentWordIndex}</div>
                <div className="text-sm text-gray-500">Remaining</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{sessionProgress.again}</div>
                <div className="text-sm text-gray-500">Again</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{sessionProgress.hard}</div>
                <div className="text-sm text-gray-500">Hard</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{sessionProgress.good}</div>
                <div className="text-sm text-gray-500">Good</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{sessionProgress.easy}</div>
                <div className="text-sm text-gray-500">Easy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{sessionWords.length}</div>
                <div className="text-sm text-gray-500">Reviewed</div>
              </div>
            </div>
          </div>
        )}

        {/* Session Type Specific Interface */}
        {sessionType === 'review' ? (
          <ReviewCard 
            word={currentWordData}
            cardType={cardType}
            showAnswer={showAnswer}
            userAnswer={userAnswer}
            setUserAnswer={setUserAnswer}
            isCorrect={isCorrect}
            onShowAnswer={() => {
              // Check if user's answer is correct before showing answer
              if (currentWordData && userAnswer.trim()) {
                let correctAnswer = ''
                if (cardType === 'recognition') {
                  correctAnswer = currentWordData.language_b_translation
                } else if (cardType === 'production') {
                  correctAnswer = currentWordData.language_a_word
                }
                
                // Case-insensitive comparison
                const isAnswerCorrect = correctAnswer.toLowerCase().trim() === userAnswer.toLowerCase().trim()
                setIsCorrect(isAnswerCorrect)
                console.log('Answer check:', {
                  userAnswer: userAnswer.trim(),
                  correctAnswer: correctAnswer.trim(),
                  isCorrect: isAnswerCorrect
                })
              }
              setShowAnswer(true)
            }}
            onAnswer={handleAnswer}
            onUserAnswer={(answer: string) => setUserAnswer(answer)}
            speakWord={speakWord}
            currentWordProgress={currentWordProgress}
            currentDeck={currentDeck}
          />
        ) : sessionType === 'discovery' ? (
          <DiscoveryCard 
            word={currentWordData}
            onAnswer={handleAnswer}
            speakWord={speakWord}
            sessionProgress={sessionProgress}
            currentDeck={currentDeck}
            sessionWords={sessionWords}
          />
        ) : (
          <DeepDiveCard 
            word={currentWordData}
            onAnswer={handleAnswer}
            speakWord={speakWord}
            currentDeck={currentDeck}
          />
        )}

        {/* Similar Words Under Card */}
        <div className="mt-12 pt-6 border-t">
          <SimilarWordsPanel 
            currentWordId={sessionType === 'review' ? (showAnswer ? (currentWord?.id ?? null) : null) : (currentWord?.id ?? null)}
            currentDeckId={currentDeck?.id ?? null}
            max={5}
          />
        </div>
      </div>
    </div>
  )
}

// Review Card Component
interface ReviewCardProps {
  word: Vocabulary | null
  cardType: 'recognition' | 'production' | 'listening'
  showAnswer: boolean
  userAnswer: string
  setUserAnswer: (value: string) => void
  isCorrect: boolean
  onShowAnswer: () => void
  onAnswer: (rating: 'again' | 'hard' | 'good' | 'easy' | 'learn' | 'know' | 'leech' | 'remove-leech') => void
  onUserAnswer: (value: string) => void
  speakWord: (text: string | undefined, language?: string) => void
  currentWordProgress: { again_count: number } | null // Add progress data
  currentDeck: VocabularyDeck | null
}

function ReviewCard({ 
  word, 
  cardType, 
  showAnswer, 
  userAnswer, 
  setUserAnswer, 
  isCorrect, 
  onShowAnswer, 
  onAnswer, 
  onUserAnswer,
  speakWord,
  currentWordProgress,
  currentDeck
}: ReviewCardProps) {
  const prompt = cardType === 'recognition' 
    ? `Translate this ${word?.language_a_word ? 'word' : 'text'}:` 
    : cardType === 'production' 
    ? `Translate this ${word?.language_b_translation ? 'word' : 'text'}:` 
    : 'Listen and translate:'
  
  const promptText = cardType === 'recognition' 
    ? word?.language_a_word 
    : cardType === 'production' 
    ? word?.language_b_translation 
    : ''

  // Auto-play audio for listening mode
  useEffect(() => {
    if (cardType === 'listening') {
      const timer = setTimeout(() => {
        speakWord(word?.language_a_word, 'auto')
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [cardType, word?.language_a_word, speakWord])

  return (
    <Card className="mb-8">
      <CardContent className="p-8">
        <div className={`flash-card ${showAnswer ? 'flipped' : ''}`} style={{ minHeight: '500px' }}>
          <div className="flash-card-inner">
            {/* Front of Card - Question */}
            <div className="flash-card-front">
              <div className="flex flex-col h-full">
                {/* Status on top */}
                <div className="text-center mb-8">
                  <p className="text-sm text-gray-500">{prompt}</p>
                </div>

                {/* Main content */}
                <div className="flex-1 flex flex-col justify-center items-center">
                  {cardType === 'listening' ? (
                    <div className="text-center space-y-6">
                      <div className="text-6xl">🎧</div>
                      <Button
                        variant="outline"
                        size="lg"
                        onClick={() => speakWord(word?.language_a_word, currentDeck?.language_a_code)}
                        className="text-xl px-8 py-4"
                      >
                        <Volume2 className="h-8 w-8 mr-3" />
                        Listen Again
                      </Button>
                    </div>
                  ) : (
                    <div className="text-center space-y-6">
                      <div className="flex items-center justify-center gap-4 mb-8">
                        <div className="text-6xl font-bold text-gray-900">
                          {promptText}
                        </div>
                        {(cardType === 'recognition' || cardType === 'production') && (
                          <Button
                            variant="ghost"
                            size="lg"
                            onClick={() => 
                              cardType === 'recognition' 
                                ? speakWord(word?.language_a_word, currentDeck?.language_a_code)
                                : speakWord(word?.language_b_translation, currentDeck?.language_b_code)
                            }
                            className="p-3"
                          >
                            <Volume2 className="h-8 w-8" />
                          </Button>
                        )}
                      </div>
                      <input
                        type="text"
                        value={userAnswer}
                        onChange={(e) => onUserAnswer(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && onShowAnswer()}
                        placeholder="Type your answer..."
                        className="w-full max-w-md p-4 border-2 border-gray-300 rounded-lg text-center text-2xl focus:border-blue-500 focus:outline-none"
                        autoFocus
                      />
                    </div>
                  )}
                </div>

                {/* Reveal Answer Button */}
                <div className="text-center mt-8">
                  <Button 
                    onClick={onShowAnswer} 
                    className="px-12 py-4 text-xl bg-blue-600 hover:bg-blue-700"
                  >
                    Reveal Answer
                  </Button>
                </div>
              </div>
            </div>

            {/* Back of Card - Answer */}
            <div className="flash-card-back">
              <div className="flex flex-col h-full">
                {/* Status on top */}
                <div className="text-center mb-6">
                  <p className={`text-2xl font-semibold ${isCorrect ? 'text-green-500' : 'text-red-500'}`}>
                    {isCorrect ? 'Correct! 🎉' : 'Not quite...'}
                  </p>
                </div>

                {/* Main content */}
                <div className="flex-1 flex flex-col justify-center items-center space-y-6">
                  {/* Language A Word with Pronunciation */}
                  <div className="flex items-center justify-center gap-4">
                    <p className="text-6xl font-bold text-gray-900">{word?.language_a_word}</p>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => speakWord(word?.language_a_word, currentDeck?.language_a_code)}
                      className="p-2"
                    >
                      <Volume2 className="h-8 w-8" />
                    </Button>
                  </div>

                  {/* Language B Translation with Pronunciation */}
                  <div className="flex items-center justify-center gap-4">
                    <p className="text-4xl font-medium text-gray-700">{word?.language_b_translation}</p>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => speakWord(word?.language_b_translation, currentDeck?.language_b_code)}
                      className="p-2"
                    >
                      <Volume2 className="h-6 w-6" />
                    </Button>
                  </div>

                  {/* Example Sentence with Pronunciation */}
                  {word?.language_a_sentence && (
                    <div className="p-6 bg-gray-50 rounded-lg">
                      <p className="text-lg text-gray-600 mb-3">Example:</p>
                      <div className="flex items-center justify-center gap-4">
                        <p className="text-xl italic">{word.language_a_sentence}</p>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => speakWord(word.language_a_sentence, currentDeck?.language_a_code)}
                        >
                          <Volume2 className="h-5 w-5" />
                        </Button>
                      </div>
                      {word.language_b_sentence && (
                        <div className="flex items-center justify-center gap-4 mt-3">
                          <p className="text-lg text-gray-500">
                            {word.language_b_sentence}
                          </p>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => speakWord(word.language_b_sentence, currentDeck?.language_b_code)}
                          >
                            <Volume2 className="h-5 w-5" />
                          </Button>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Bottom section */}
                <div className="mt-8 space-y-6">
                  {/* SRS Rating Buttons */}
                  <div className="grid grid-cols-4 gap-3">
                    <Button
                      variant="outline"
                      size="lg"
                      onClick={() => onAnswer('again')}
                      className="bg-red-50 border-red-200 text-red-700 hover:bg-red-100 text-lg"
                    >
                      Again
                    </Button>
                    <Button
                      variant="outline"
                      size="lg"
                      onClick={() => onAnswer('hard')}
                      className="bg-orange-50 border-orange-200 text-orange-700 hover:bg-orange-100 text-lg"
                    >
                      Hard
                    </Button>
                    <Button
                      variant="outline"
                      size="lg"
                      onClick={() => onAnswer('good')}
                      className="bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100 text-lg"
                    >
                      Good
                    </Button>
                    <Button
                      variant="outline"
                      size="lg"
                      onClick={() => onAnswer('easy')}
                      className="bg-green-50 border-green-200 text-green-700 hover:bg-green-100 text-lg"
                    >
                      Easy
                    </Button>
                  </div>

                  {/* Add/Remove from Leeches Option */}
                  <div className="text-center pt-6 border-t-2 border-gray-300">
                    {/* Check if word is already a leech based on user progress */}
                    {currentWordProgress && currentWordProgress.again_count >= 3 ? (
                      <Button
                        variant="outline"
                        size="lg"
                        onClick={() => onAnswer('remove-leech')}
                        className="w-full bg-green-50 border-green-200 text-green-700 hover:bg-green-100 text-xl py-4"
                      >
                        <AlertTriangle className="h-6 w-6 mr-3" />
                        Remove from Leeches
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="lg"
                        onClick={() => onAnswer('leech')}
                        className="w-full bg-red-50 border-red-200 text-red-700 hover:bg-red-100 text-xl py-4"
                      >
                        <AlertTriangle className="h-6 w-6 mr-3" />
                        Add to Leeches
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Discovery Card Component
interface DiscoveryCardProps {
  word: Vocabulary | null
  onAnswer: (rating: 'again' | 'hard' | 'good' | 'easy' | 'learn' | 'know' | 'leech' | 'remove-leech') => void
  speakWord: (text: string | undefined, language?: string) => void
  sessionProgress: SessionProgress
  currentDeck: VocabularyDeck | null
  sessionWords: Vocabulary[]
}

function DiscoveryCard({ word, onAnswer, speakWord, sessionProgress, currentDeck, sessionWords }: DiscoveryCardProps) {
  return (
    <Card className="mb-8">
      <CardContent className="p-8">
        {/* Progress Visualization */}
        <div className="mb-8">
          <div className="grid grid-cols-2 gap-4 text-center">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="text-2xl font-bold text-blue-700">{sessionWords.length - sessionProgress.reviewed}</div>
              <div className="text-sm text-blue-600">Remaining Unseen</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <div className="text-2xl font-bold text-green-700">{sessionProgress.reviewed}</div>
              <div className="text-sm text-green-600">Reviewed</div>
            </div>
          </div>
        </div>

        <div className="space-y-8">
          {/* Language A Word with Pronunciation */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-4 mb-4">
              <h1 className="text-6xl font-bold text-gray-900">{word?.language_a_word}</h1>
              <Button
                variant="ghost"
                size="lg"
                onClick={() => speakWord(word?.language_a_word, currentDeck?.language_a_code)}
                className="p-3"
              >
                <Volume2 className="h-8 w-8" />
              </Button>
            </div>
          </div>

          {/* Language B Translation with Pronunciation */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-4 mb-6">
              <p className="text-4xl font-medium text-gray-700">{word?.language_b_translation}</p>
              <Button
                variant="ghost"
                size="lg"
                onClick={() => speakWord(word?.language_b_translation, currentDeck?.language_b_code)}
                className="p-3"
              >
                <Volume2 className="h-6 w-6" />
              </Button>
            </div>
          </div>

          {/* Example Sentence with Pronunciation */}
          {word?.language_a_sentence && (
            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <div className="space-y-4">
                <div className="flex items-center justify-center gap-4">
                  <p className="text-2xl italic text-gray-800">{word.language_a_sentence}</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => speakWord(word.language_a_sentence, currentDeck?.language_a_code)}
                  >
                    <Volume2 className="h-5 w-5" />
                  </Button>
                </div>
                {word.language_b_sentence && (
                  <div className="flex items-center justify-center gap-4">
                    <p className="text-xl text-gray-600">
                      {word.language_b_sentence}
                    </p>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => speakWord(word.language_b_sentence, currentDeck?.language_b_code)}
                    >
                      <Volume2 className="h-5 w-5" />
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Choice Buttons */}
          <div className="text-center pt-6">
            <div className="flex gap-6 justify-center">
              <Button
                variant="outline"
                size="lg"
                onClick={() => onAnswer('learn')}
                className="bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100 text-xl px-12 py-6"
              >
                Learn This
              </Button>
              <Button
                size="lg"
                onClick={() => onAnswer('know')}
                className="bg-green-600 hover:bg-green-700 text-xl px-12 py-6"
              >
                I Know This
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Deep Dive Card Component
interface DeepDiveCardProps {
  word: Vocabulary | null
  onAnswer: (rating: 'again' | 'hard' | 'good' | 'easy' | 'learn' | 'know' | 'leech' | 'remove-leech') => void
  speakWord: (text: string | undefined, language?: string) => void
  currentDeck: VocabularyDeck | null
}

function DeepDiveCard({ word, onAnswer, speakWord, currentDeck }: DeepDiveCardProps) {
  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle className="text-center text-4xl font-bold">
          Deep Dive Session
        </CardTitle>
      </CardHeader>
      <CardContent className="p-8">
        <div className="space-y-8">
          {/* Language A Word */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-4 mb-4">
              <h1 className="text-6xl font-bold text-gray-900">{word?.language_a_word}</h1>
              <Button
                variant="ghost"
                size="lg"
                onClick={() => speakWord(word?.language_a_word, currentDeck?.language_a_code)}
                className="p-3"
              >
                <Volume2 className="h-8 w-8" />
              </Button>
            </div>
          </div>

          {/* Language B Translation */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-4 mb-6">
              <p className="text-4xl font-medium text-gray-700">{word?.language_b_translation}</p>
              <Button
                variant="ghost"
                size="lg"
                onClick={() => speakWord(word?.language_b_translation, currentDeck?.language_b_code)}
                className="p-3"
              >
                <Volume2 className="h-6 w-6" />
              </Button>
            </div>
          </div>

          {/* Example Sentence */}
          {word?.language_a_sentence && (
            <div className="text-center p-6 bg-gray-50 rounded-lg">
              <div className="space-y-4">
                <div className="flex items-center justify-center gap-4">
                  <p className="text-2xl italic text-gray-800">{word.language_a_sentence}</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => speakWord(word.language_a_sentence, currentDeck?.language_a_code)}
                  >
                    <Volume2 className="h-5 w-5" />
                  </Button>
                </div>
                {word.language_b_sentence && (
                  <div className="flex items-center justify-center gap-4">
                    <p className="text-xl text-gray-600">
                      {word.language_b_sentence}
                    </p>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => speakWord(word.language_b_sentence, currentDeck?.language_b_code)}
                    >
                      <Volume2 className="h-5 w-5" />
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Rating Buttons */}
          <div className="text-center pt-6">
            <div className="flex gap-4 justify-center">
              <Button
                variant="outline"
                onClick={() => onAnswer('again')}
                className="bg-red-50 border-red-200 text-red-700 hover:bg-red-100"
              >
                Again
              </Button>
              <Button
                variant="outline"
                onClick={() => onAnswer('hard')}
                className="bg-orange-50 border-orange-200 text-orange-700 hover:bg-orange-100"
              >
                Hard
              </Button>
              <Button
                variant="outline"
                onClick={() => onAnswer('good')}
                className="bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100"
              >
                Good
              </Button>
              <Button
                onClick={() => onAnswer('easy')}
                className="bg-green-600 hover:bg-green-700"
              >
                Easy
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
