'use client'

import { useState, useEffect } from 'react'
import { useVocabularyStore } from '@/store/vocabulary-store'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  ArrowLeft,
  Volume2,
  Check,
  X,
  RotateCcw,
  Play,
  Pause,
  SkipForward,
  AlertTriangle
} from 'lucide-react'
import { 
  SRS, 
  calculateNextReview, 
  speakText, 
  getCardType, 
  checkAnswer,
  normalizeText,
  logRating,
  getRecentRatings,
  shouldRemoveFromLeech,
  getLanguageCode
} from '@/lib/utils'

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
  const { setCurrentWord, setSessionWords, sessionSettings } = useVocabularyStore()
  const [currentWordIndex, setCurrentWordIndex] = useState(0)
  const [sessionWords, setLocalSessionWords] = useState<any[]>([])
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
  const [currentWord, setCurrentWordState] = useState<any>(null)
  const [sessionType, setSessionType] = useState<'review' | 'discovery' | 'deep-dive'>('discovery')
  const [deepDiveCategory, setDeepDiveCategory] = useState<'leeches' | 'learning' | 'strengthening' | 'consolidating' | null>(null)
  const [currentDeck, setCurrentDeck] = useState<any>(null)

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
        console.log('Loaded deck from localStorage:', deck)
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
      loadSessionWords()
    }
  }, [currentDeck, sessionType])

  const onBack = () => {
    // Clear session data from localStorage
    localStorage.removeItem('sessionType')
    localStorage.removeItem('deepDiveCategory')
    window.location.href = '/dashboard'
  }

  const loadSessionWords = async () => {
    if (!currentDeck) {
      console.log('No current deck found')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      console.log('Loading session words for deck:', currentDeck.id, 'session type:', sessionType)
      
      // First, get the vocabulary IDs for this deck
      const { data: deckVocab, error: deckError } = await supabase
        .from('deck_vocabulary')
        .select('vocabulary_id')
        .eq('deck_id', currentDeck.id)
        .order('word_order')

      if (deckError) {
        console.error('Error loading deck vocabulary:', deckError)
        throw deckError
      }

      if (!deckVocab || deckVocab.length === 0) {
        console.log('No vocabulary found for deck:', currentDeck.id)
        setLocalSessionWords([])
        setLoading(false)
        return
      }

      // Extract vocabulary IDs
      const vocabIds = deckVocab.map(item => item.vocabulary_id)
      console.log('Vocabulary IDs for deck:', vocabIds)
      console.log('Vocabulary ID types:', vocabIds.map(id => typeof id))

      // Get the actual vocabulary words
      const { data: words, error: wordsError } = await supabase
        .from('vocabulary')
        .select('*')
        .in('id', vocabIds)

      if (wordsError) {
        console.error('Error loading words:', wordsError)
        throw wordsError
      }

      if (!words || words.length === 0) {
        console.log('No words found for vocabulary IDs:', vocabIds)
        setLocalSessionWords([])
        setLoading(false)
        return
      }

      console.log('Loaded words:', words.length)

      // Get user progress for this deck
      const mockUserId = '00000000-0000-0000-0000-000000000000'
      const { data: userProgress, error: progressError } = await supabase
        .from('user_progress')
        .select('*')
        .eq('user_id', mockUserId)
        .eq('deck_id', currentDeck.id)

      if (progressError) {
        console.error('Error loading user progress:', progressError)
      }

      console.log('User progress:', userProgress?.length || 0)

      // Create a map of word progress
      const progressMap = new Map()
      userProgress?.forEach(progress => {
        progressMap.set(progress.word_id, progress)
      })

      // Filter words based on session type
      let filteredWords = words

      if (sessionType === 'review') {
        // For review sessions, include words that are due for review
        filteredWords = words.filter(word => {
          const progress = progressMap.get(word.id)
          if (!progress) return false
          
          const nextReview = new Date(progress.next_review_date)
          const now = new Date()
          return nextReview <= now
        })
      } else if (sessionType === 'discovery') {
        // For discovery sessions, exclude words that have already been learned
        const learnedWordIds = userProgress?.map(p => p.word_id) || []
        filteredWords = words.filter(word => !learnedWordIds.includes(word.id))
      } else if (sessionType === 'deep-dive' && deepDiveCategory) {
        // For deep dive sessions, filter by category
        filteredWords = words.filter(word => {
          const progress = progressMap.get(word.id)
          if (!progress) return false

          switch (deepDiveCategory) {
            case 'leeches':
              return progress.again_count >= 3
            case 'learning':
              return progress.repetitions > 0 && progress.repetitions < 3
            case 'strengthening':
              return progress.repetitions >= 3 && progress.repetitions < 10
            case 'consolidating':
              return progress.repetitions >= 10
            default:
              return false
          }
        })
      }

      console.log(`Filtered words for ${sessionType}:`, filteredWords.length)

      // Shuffle the words
      const shuffledWords = [...filteredWords].sort(() => Math.random() - 0.5)
      setLocalSessionWords(shuffledWords)
      setSessionProgress(prev => ({ ...prev, total: shuffledWords.length }))

      if (shuffledWords.length > 0) {
        setCurrentWordState(shuffledWords[0])
        setCurrentWordIndex(0)
      }

    } catch (error) {
      console.error('Error loading session words:', error)
    } finally {
      setLoading(false)
    }
  }

  const speakWord = (text: string, language?: string) => {
    if (!text) return
    
    const langCode = language || getLanguageCode(currentDeck?.language_a_code || 'en')
    speakText(text, langCode)
  }

  const markWordAsLeech = async (word: any) => {
    if (!currentDeck) return

    try {
      const mockUserId = '00000000-0000-0000-0000-000000000000'
      
      // Get current progress
      const { data: currentProgress } = await supabase
        .from('user_progress')
        .select('*')
        .eq('user_id', mockUserId)
        .eq('word_id', word.id)
        .eq('deck_id', currentDeck.id)
        .single()

      const progressData = {
        user_id: mockUserId,
        word_id: parseInt(word.id),
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
      moveToNextWord()

    } catch (error) {
      console.error('Error marking word as leech:', error)
    }
  }

  const removeWordFromLeech = async (word: any) => {
    if (!currentDeck) return

    try {
      const mockUserId = '00000000-0000-0000-0000-000000000000'
      
      // Get current progress
      const { data: currentProgress } = await supabase
        .from('user_progress')
        .select('*')
        .eq('user_id', mockUserId)
        .eq('word_id', word.id)
        .eq('deck_id', currentDeck.id)
        .single()

      const progressData = {
        user_id: mockUserId,
        word_id: parseInt(word.id),
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
      moveToNextWord()

    } catch (error) {
      console.error('Error removing word from leeches:', error)
    }
  }

  const handleAnswer = async (rating: 'again' | 'hard' | 'good' | 'easy' | 'learn' | 'know' | 'leech' | 'remove-leech') => {
    if (!currentWord || !currentDeck) return

    try {
      const mockUserId = '00000000-0000-0000-0000-000000000000'
      
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

      let newInterval = 0
      let newEaseFactor = SRS.EASE_FACTOR_DEFAULT
      let newRepetitions = 0
      let newAgainCount = 0

      if (sessionType === 'review') {
        // Get current progress
        const { data: currentProgress } = await supabase
          .from('user_progress')
          .select('*')
          .eq('user_id', mockUserId)
          .eq('word_id', currentWord.id)
          .eq('deck_id', currentDeck.id)
          .single()

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
        await logRating(mockUserId, currentWord.id.toString(), currentDeck.id, rating as 'again' | 'hard' | 'good' | 'easy')

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
        await logRating(mockUserId, currentWord.id.toString(), currentDeck.id, rating as 'learn' | 'know')
      }

      const nextReviewDate = new Date()
      if (newInterval > 0) {
        nextReviewDate.setDate(nextReviewDate.getDate() + newInterval)
      }

      // Log the data being sent for debugging
      console.log('Word ID before conversion:', currentWord.id, 'Type:', typeof currentWord.id)
      
      const progressData = {
        user_id: mockUserId,
        word_id: parseInt(currentWord.id), // Convert string ID to integer for database
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
      moveToNextWord()

    } catch (error) {
      console.error('Error handling answer:', error)
    }
  }

  const saveSessionSummary = async () => {
    if (!currentDeck) return

    try {
      const mockUserId = '00000000-0000-0000-0000-000000000000'
      
      const { error } = await supabase
        .from('study_sessions')
        .insert({
          user_id: mockUserId,
          deck_id: currentDeck.id,
          session_type: sessionType,
          words_studied: sessionProgress.total,
          correct_answers: sessionProgress.good + sessionProgress.easy + sessionProgress.know,
          session_duration: 0, // TODO: Calculate actual duration
          completed_at: new Date().toISOString()
        })

      if (error) {
        console.error('Error saving session summary:', error)
      } else {
        console.log('Session summary saved successfully')
      }
    } catch (error) {
      console.error('Error in saveSessionSummary:', error)
    }
  }

  const moveToNextWord = () => {
    const nextIndex = currentWordIndex + 1
    
    if (nextIndex < sessionWords.length) {
      setCurrentWordIndex(nextIndex)
      setCurrentWordState(sessionWords[nextIndex])
      setShowAnswer(false)
      setUserAnswer('')
      setIsCorrect(false)
      
      // Set card type for next word
      if (sessionSettings.types.length > 0) {
        const randomType = sessionSettings.types[Math.floor(Math.random() * sessionSettings.types.length)]
        setCardType(randomType)
      }
    } else {
      // Session complete
      console.log('Session complete!')
      saveSessionSummary()
      onBack()
    }
  }

  const currentWordData = currentWord ? {
    id: currentWord.id,
    language_a_word: currentWord.language_a_word,
    language_b_translation: currentWord.language_b_translation,
    language_a_sentence: currentWord.language_a_sentence,
    language_b_sentence: currentWord.language_b_sentence
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
            {currentDeck?.name} • {sessionProgress.total} completed
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{Math.round((sessionProgress.reviewed / sessionProgress.total) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(sessionProgress.reviewed / sessionProgress.total) * 100}%` }}
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
                <div className="text-2xl font-bold text-purple-600">{sessionProgress.total}</div>
                <div className="text-sm text-gray-500">Reviewed</div>
              </div>
            </div>
          </div>
        )}

        {/* Session Type Specific Interface */}
        {sessionType === 'review' ? (
          <ReviewCard 
            word={currentWordData}
            currentWord={currentWord}
            cardType={cardType}
            showAnswer={showAnswer}
            userAnswer={userAnswer}
            setUserAnswer={setUserAnswer}
            isCorrect={isCorrect}
            onShowAnswer={() => setShowAnswer(true)}
            onAnswer={handleAnswer}
            onUserAnswer={(answer: string) => setUserAnswer(answer)}
            speakWord={speakWord}
            sessionSettings={sessionSettings}
          />
        ) : sessionType === 'discovery' ? (
          <DiscoveryCard 
            word={currentWordData}
            onAnswer={handleAnswer}
            speakWord={speakWord}
            sessionProgress={sessionProgress}
          />
        ) : (
          <DeepDiveCard 
            word={currentWordData}
            onAnswer={handleAnswer}
            speakWord={speakWord}
          />
        )}
      </div>
    </div>
  )
}

// Review Card Component
function ReviewCard({ 
  word, 
  currentWord,
  cardType, 
  showAnswer, 
  userAnswer, 
  setUserAnswer, 
  isCorrect, 
  onShowAnswer, 
  onAnswer, 
  onUserAnswer,
  speakWord,
  sessionSettings
}: any) {
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
                        onClick={() => speakWord(word?.language_a_word, 'auto')}
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
                        {cardType === 'recognition' && (
                          <Button
                            variant="ghost"
                            size="lg"
                            onClick={() => speakWord(word?.language_a_word, 'auto')}
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
                      onClick={() => speakWord(word?.language_a_word, 'auto')}
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
                      onClick={() => speakWord(word?.language_b_translation, 'auto')}
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
                          onClick={() => speakWord(word.language_a_sentence, 'auto')}
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
                            onClick={() => speakWord(word.language_b_sentence, 'auto')}
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
                    {currentWord?.again_count >= 4 ? (
                      <Button
                        variant="outline"
                        size="lg"
                        onClick={() => onAnswer('remove-leech')}
                        className="w-full bg-green-50 border-green-200 text-green-700 hover:bg-green-100 text-xl py-4"
                      >
                        <Check className="h-6 w-6 mr-3" />
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
function DiscoveryCard({ word, onAnswer, speakWord, sessionProgress }: any) {
  return (
    <Card className="mb-8">
      <CardContent className="p-8">
        {/* Progress Visualization */}
        <div className="mb-8">
          <div className="grid grid-cols-2 gap-4 text-center">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="text-2xl font-bold text-blue-700">{sessionProgress.total - sessionProgress.reviewed}</div>
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
                onClick={() => speakWord(word?.language_a_word, 'auto')}
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
                onClick={() => speakWord(word?.language_b_translation, 'auto')}
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
                    onClick={() => speakWord(word.language_a_sentence, 'auto')}
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
                      onClick={() => speakWord(word.language_b_sentence, 'auto')}
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
function DeepDiveCard({ word, onAnswer, speakWord }: any) {
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
                onClick={() => speakWord(word?.language_a_word, 'auto')}
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
                onClick={() => speakWord(word?.language_b_translation, 'auto')}
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
                    onClick={() => speakWord(word.language_a_sentence, 'auto')}
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
                      onClick={() => speakWord(word.language_b_sentence, 'auto')}
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
