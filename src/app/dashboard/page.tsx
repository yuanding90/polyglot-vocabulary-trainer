'use client'

import { useState, useEffect, useCallback } from 'react'
import { useVocabularyStore } from '@/store/vocabulary-store'
import { supabase, VocabularyDeck } from '@/lib/supabase'
import { User } from '@supabase/supabase-js'
import { sessionQueueManager } from '@/lib/session-queues'
import { DailySummaryManager } from '@/lib/daily-summary'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { 
  BookOpen, 
  Brain, 
  Target, 
  TrendingUp, 
  Play, 
  ArrowLeft,
  LibraryBig,
  Dumbbell,
  Calendar,
  Trophy,
  Activity,
  Settings,
  Eye,
  MessageSquare,
  Ear,
  Zap,
  Clock,
  EyeOff,
  Flame,
  EyeOff as UnseenIcon,
  BookOpen as LearningIcon,
  TrendingUp as StrengtheningIcon,
  CheckCircle as MasteredIcon
} from 'lucide-react'

export default function Dashboard() {
  const { 
    currentDeck,
    setCurrentDeck,
    availableDecks,
    setAvailableDecks,
    userDeckProgress,
    setUserDeckProgress,
    sessionSettings,
    setSessionSettings,
    metrics,
    updateMetrics,
    sessionStats,
    updateSessionStats,
    setUnseenQueue,
    setReviewQueue,
    setPracticePool,
    setNearFutureQueue,
    unseenQueue,
    reviewQueue,
    practicePool,
    nearFutureQueue
  } = useVocabularyStore()

  const [loading, setLoading] = useState(true)
  const [showStudySession, setShowStudySession] = useState(false)
  const [sessionType, setSessionType] = useState<'review' | 'discovery' | 'deep-dive' | null>(null)
  const [deepDiveCategory, setDeepDiveCategory] = useState<'leeches' | 'learning' | 'strengthening' | 'consolidating' | null>(null)
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  // Deck filter state (Language A/L2 and Language B/L1)
  const [filterL2Code, setFilterL2Code] = useState<string | null>(null)
  const [filterL1Code, setFilterL1Code] = useState<string | null>(null)

  useEffect(() => {
    // Get current user first
    const getCurrentUser = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      console.log('Dashboard: Got current user:', user?.email, 'ID:', user?.id)
      setCurrentUser(user)
      if (user) {
        console.log('Dashboard: Loading dashboard data for user:', user.id)
        await loadDashboardData(user.id)
      } else {
        console.log('Dashboard: No user found, redirecting to auth')
      }
    }
    getCurrentUser()
  }, [])

  // Reload deck-specific data when current deck changes
  useEffect(() => {
    if (currentDeck && currentUser) {
      const loadCurrentDeckData = async () => {
        await loadDeckData(currentDeck.id, currentUser.id)
      }
      loadCurrentDeckData()
    }
  }, [currentDeck, currentUser])

  // Refresh data when returning from study session (focus event)
  useEffect(() => {
    const handleFocus = async () => {
      if (currentUser && currentDeck) {
        console.log('Dashboard focused, refreshing data...')
        await loadDeckData(currentDeck.id, currentUser.id)
        await loadSessionStats(currentUser.id)
      }
    }

    window.addEventListener('focus', handleFocus)
    return () => window.removeEventListener('focus', handleFocus)
  }, [currentUser, currentDeck])

  // Initialize deck filters from current deck or saved filters
  useEffect(() => {
    // On first load, prefer current deck's languages; fallback to saved filters
    const saved = (() => {
      try { return JSON.parse(localStorage.getItem('deckFilters') || 'null') } catch { return null }
    })() as { l2?: string | null; l1?: string | null } | null

    if (currentDeck) {
      setFilterL2Code(currentDeck.language_a_code || null)
      setFilterL1Code(currentDeck.language_b_code || null)
    } else if (saved) {
      setFilterL2Code(saved.l2 ?? null)
      setFilterL1Code(saved.l1 ?? null)
    }
  }, [currentDeck])

  // Persist filters
  useEffect(() => {
    const payload = { l2: filterL2Code, l1: filterL1Code }
    try { localStorage.setItem('deckFilters', JSON.stringify(payload)) } catch {}
  }, [filterL2Code, filterL1Code])

  const loadDashboardData = useCallback(async (userId: string) => {
    try {
      setLoading(true)
      
      // Load available decks
      const { data: decks, error: decksError } = await supabase
        .from('vocabulary_decks')
        .select('*')
        .eq('is_active', true)
        .order('name')

      if (decksError) throw decksError
      setAvailableDecks(decks || [])

      // Load metrics for all decks to show correct word counts
      if (decks && decks.length > 0) {
        for (const deck of decks) {
          try {
            const metrics = await sessionQueueManager.calculateMetrics(userId, deck.id)
            setUserDeckProgress(deck.id, {
              deck_id: deck.id,
              total_words: metrics.unseen + metrics.leeches + metrics.learning + metrics.strengthening + metrics.consolidating + metrics.mastered,
              mastered_words: metrics.mastered,
              learning_words: metrics.learning,
              leeches: metrics.leeches,
              unseen_words: metrics.unseen,
              strengthening_words: metrics.strengthening,
              consolidating_words: metrics.consolidating
            })
          } catch (error) {
            console.error(`Error loading metrics for deck ${deck.id}:`, error)
          }
        }
      }

      // Load current deck from localStorage
      const deckData = localStorage.getItem('selectedDeck')
      if (deckData) {
        const deck = JSON.parse(deckData)
        setCurrentDeck(deck)
        
        // Load deck data with current user
        await loadDeckData(deck.id, userId)
      }

      // Load session statistics
      await loadSessionStats(userId)

    } catch (error) {
      console.error('Error loading dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  const loadDeckData = useCallback(async (deckId: string, userId: string) => {
    try {
      console.log('Dashboard: Loading deck data for deck:', deckId, 'user:', userId, 'type:', typeof userId)
      if (!userId || userId === '00000000-0000-0000-0000-000000000000') {
        console.error('Dashboard: Invalid user ID detected:', userId)
        return
      }
      
      // Build queues
      const queues = await sessionQueueManager.buildQueues(deckId, userId)
      console.log('Built queues:', {
        unseen: queues.unseen.length,
        review: queues.review.length,
        practice: queues.practice.length,
        nearFuture: queues.nearFuture.length
      })
      
      setUnseenQueue(queues.unseen)
      setReviewQueue(queues.review)
      setPracticePool(queues.practice)
      setNearFutureQueue(queues.nearFuture)

      // Calculate metrics
      const deckMetrics = await sessionQueueManager.calculateMetrics(userId, deckId)
      console.log('Calculated metrics:', deckMetrics)
      updateMetrics(deckMetrics)

      // Update userDeckProgress with correct total words - ensure it's in sync with metrics
      const totalWords = deckMetrics.unseen + deckMetrics.leeches + deckMetrics.learning + deckMetrics.strengthening + deckMetrics.consolidating + deckMetrics.mastered
      setUserDeckProgress(deckId, {
        deck_id: deckId,
        total_words: totalWords,
        mastered_words: deckMetrics.mastered,
        learning_words: deckMetrics.learning,
        leeches: deckMetrics.leeches,
        unseen_words: deckMetrics.unseen,
        strengthening_words: deckMetrics.strengthening,
        consolidating_words: deckMetrics.consolidating
      })
      
      console.log('Updated userDeckProgress for deck:', deckId, {
        total_words: totalWords,
        mastered_words: deckMetrics.mastered,
        learning_words: deckMetrics.learning,
        leeches: deckMetrics.leeches,
        unseen_words: deckMetrics.unseen
      })
    } catch (error) {
      console.error('Error loading deck data:', error)
    }
  }, [])

  const loadSessionStats = useCallback(async (userId: string) => {
    try {
      // Use the new daily summary system
      const stats = await DailySummaryManager.getRecentActivityStats(userId)
      
      console.log('Loaded recent activity stats:', stats)
      updateSessionStats(stats)
    } catch (error) {
      console.error('Error loading session stats:', error)
    }
  }, [])

  const handleStartSession = async (type: 'review' | 'discovery' | 'deep-dive') => {
    if (!currentDeck) {
      alert('Please select a deck first!')
      setShowDeckSelection(true)
      return
    }

    // Check if session settings are configured
    if (sessionSettings.types.length === 0) {
      alert('Please select at least one learning type to continue!')
      return
    }

    // Load fresh deck data before starting session
    if (currentUser) {
      await loadDeckData(currentDeck.id, currentUser.id)
    }
    
    setSessionType(type)
    setShowStudySession(true)
    
    // Store session type and selected deep-dive category (if any), then redirect
    localStorage.setItem('sessionType', type)
    if (type === 'deep-dive' && deepDiveCategory) {
      localStorage.setItem('deepDiveCategory', deepDiveCategory)
    }
    window.location.href = '/study'
  }

  // Removed unused handleSessionEnd function

  const handleLearningTypeToggle = (type: 'recognition' | 'production' | 'listening') => {
    const newTypes = sessionSettings.types.includes(type)
      ? sessionSettings.types.filter(t => t !== type)
      : [...sessionSettings.types, type]
    
    console.log('Learning type toggled:', type, 'New types:', newTypes)
    
    setSessionSettings({
      ...sessionSettings,
      types: newTypes
    })
  }

  const handleSelectAllTypes = () => {
    setSessionSettings({
      ...sessionSettings,
      types: ['recognition', 'production', 'listening']
    })
  }

  const handleClearAllTypes = () => {
    setSessionSettings({
      ...sessionSettings,
      types: []
    })
  }

  const [showDeckSelection, setShowDeckSelection] = useState(false)

  // Removed unused goBackToDeckSelection function

  const selectDeck = async (deck: VocabularyDeck) => {
    localStorage.setItem('selectedDeck', JSON.stringify(deck))
    setCurrentDeck(deck)
    setShowDeckSelection(false)
    // Load deck data with current user and ensure UI updates
    if (currentUser) {
      await loadDeckData(deck.id, currentUser.id)
      console.log('Deck selected and data loaded:', deck.name)
    }
    // Preserve deep-dive selection across deck change
    if (deepDiveCategory) {
      localStorage.setItem('deepDiveCategory', deepDiveCategory)
    }
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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading dashboard...</div>
      </div>
    )
  }

  if (!currentDeck || showDeckSelection) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">🐰 Polyglot Vocabulary Trainer</h1>
                <p className="text-gray-600">Choose your language deck to get started</p>
              </div>
              <Button variant="outline" onClick={handleSignOut}>
                Sign Out
              </Button>
            </div>
          </div>
        </header>

        <div className="container mx-auto p-6 max-w-6xl">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Choose Your Language Deck
            </h2>
            <p className="text-lg text-gray-600">
              Select a vocabulary deck to start your learning journey
            </p>
          </div>

          {/* Deck Filter Bar */}
          <div className="mb-6 grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Learn Language (L2)</label>
              <select
                value={filterL2Code || ''}
                onChange={(e) => setFilterL2Code(e.target.value || null)}
                className="w-full p-3 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All</option>
                {Array.from(new Map(availableDecks.map(d => [d.language_a_code, d.language_a_name])).entries()).map(([code, name]) => (
                  <option key={code || 'unknown-l2'} value={code || ''}>{name} {code ? `(${code})` : ''}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Native Language (L1)</label>
              <select
                value={filterL1Code || ''}
                onChange={(e) => setFilterL1Code(e.target.value || null)}
                className="w-full p-3 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All</option>
                {Array.from(new Map(availableDecks.map(d => [d.language_b_code, d.language_b_name])).entries()).map(([code, name]) => (
                  <option key={code || 'unknown-l1'} value={code || ''}>{name} {code ? `(${code})` : ''}</option>
                ))}
              </select>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                className="w-full"
                onClick={() => { setFilterL2Code(null); setFilterL1Code(null) }}
              >
                Clear Filters
              </Button>
            </div>
          </div>

          {(() => {
            const decksFiltered = availableDecks.filter(d => (
              (!filterL2Code || (d.language_a_code || '').toLowerCase() === filterL2Code.toLowerCase()) &&
              (!filterL1Code || (d.language_b_code || '').toLowerCase() === filterL1Code.toLowerCase())
            ))

            const noneFound = decksFiltered.length === 0
            const l2Name = (availableDecks.find(d => d.language_a_code === filterL2Code)?.language_a_name) || 'Selected L2'
            const l1Name = (availableDecks.find(d => d.language_b_code === filterL1Code)?.language_b_name) || 'Selected L1'

            return noneFound ? (
              <div className="text-center py-12">
                <BookOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No decks found</h3>
                <p className="text-gray-600 max-w-xl mx-auto">
                  No decks found for {filterL2Code ? l2Name : 'any L2'} → {filterL1Code ? l1Name : 'any L1'}. This combination isn’t available yet, but it’s coming soon. Try clearing filters or selecting another pair.
                </p>
                <div className="mt-4">
                  <Button variant="outline" onClick={() => { setFilterL2Code(null); setFilterL1Code(null) }}>
                    Clear Filters
                  </Button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {decksFiltered.map((deck) => {
                  const progress = userDeckProgress[deck.id] || {
                    deck_id: deck.id,
                    total_words: 0,
                    mastered_words: 0,
                    learning_words: 0,
                    leeches: 0,
                    unseen_words: 0
                  }
                  const totalWords = progress.total_words || 0
                  const mastered = progress.mastered_words
                  const learning = progress.learning_words
                  const unseen = progress.unseen_words
                  return (
                    <Card 
                      key={`${deck.id}-${progress.total_words}-${progress.mastered_words}`} 
                      className="cursor-pointer transition-all hover:shadow-lg hover:bg-gray-50 card-enhanced"
                      onClick={() => selectDeck(deck)}
                    >
                      <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <BookOpen className="h-5 w-5 text-blue-600" />
                              <h3 className="font-semibold text-lg">{deck.name}</h3>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                deck.difficulty_level === 'beginner' ? 'bg-green-100 text-green-700' :
                                deck.difficulty_level === 'intermediate' ? 'bg-yellow-100 text-yellow-700' :
                                deck.difficulty_level === 'advanced' ? 'bg-orange-100 text-orange-700' :
                                'bg-red-100 text-red-700'
                              }`}>
                                {deck.difficulty_level}
                              </span>
                            </div>
                            <div className="space-y-4">
                              <div className="flex justify-between text-sm text-gray-600">
                                <span>Progress Overview</span>
                                <span>{mastered}/{totalWords} mastered</span>
                              </div>
                              <div className="flex h-4 bg-gray-200 rounded-full overflow-hidden">
                                <div className="bg-gray-400" style={{ width: `${(unseen / totalWords) * 100}%` }} title={`${unseen} unseen`} />
                                <div className="bg-orange-400" style={{ width: `${(learning / totalWords) * 100}%` }} title={`${learning} learning`} />
                                <div className="bg-yellow-400" style={{ width: `${((progress.strengthening_words || 0) / totalWords) * 100}%` }} title={`${progress.strengthening_words || 0} strengthening`} />
                                <div className="bg-green-500" style={{ width: `${(mastered / totalWords) * 100}%` }} title={`${mastered} mastered`} />
                              </div>
                            </div>
                          </div>
                          <div className="text-right ml-4">
                            <div className="text-2xl font-bold text-blue-600">{totalWords}</div>
                            <div className="text-sm text-gray-600">words</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            )
          })()}
        </div>
      </div>
    )
  }

  const getOverallProgress = () => {
    if (!currentDeck) return { totalWords: 0, totalMastered: 0, progressPercentage: 0 }
    
    const progress = userDeckProgress[currentDeck.id]
    if (!progress) return { totalWords: currentDeck.total_words, totalMastered: 0, progressPercentage: 0 }
    
    const totalWords = currentDeck.total_words
    const totalMastered = progress.mastered_words
    const progressPercentage = totalWords > 0 ? (totalMastered / totalWords) * 100 : 0
    
    return { totalWords, totalMastered, progressPercentage }
  }

  const { totalWords, totalMastered, progressPercentage } = getOverallProgress()

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 py-4 sm:py-6">
            <div className="min-w-0">
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900 leading-tight break-words">🐰 Polyglot Vocabulary Trainer</h1>
              <p className="text-xs sm:text-sm text-gray-600 leading-snug break-words">Master vocabulary with spaced repetition</p>
            </div>
            <div className="w-full sm:w-auto flex items-center gap-2 sm:gap-4 justify-between sm:justify-end">
              {currentUser && (
                <span className="hidden sm:inline text-sm text-gray-600">
                  Signed in as: {currentUser.email}
                </span>
              )}
              <Button 
                onClick={handleSignOut}
                variant="outline"
                className="flex items-center gap-2 text-red-600 border-red-300 hover:bg-red-50 w-full sm:w-auto"
              >
                <Settings className="h-4 w-4" />
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto p-6 max-w-6xl">
        {/* Recent Activity - At the very top */}
        <Card className="mb-6 card-enhanced">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Activity className="h-5 w-5 text-blue-600" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0 px-4 pb-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-2xl font-bold text-blue-600">{sessionStats.reviewsToday}</p>
                <p className="text-sm text-blue-700 font-medium">Today</p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">{sessionStats.reviews7Days}</p>
                <p className="text-sm text-green-700 font-medium">7 Days</p>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">{sessionStats.reviews30Days}</p>
                <p className="text-sm text-purple-700 font-medium">30 Days</p>
              </div>
              <div className="p-3 bg-orange-50 rounded-lg">
                <p className="text-2xl font-bold text-orange-600">{sessionStats.currentStreak} 🔥</p>
                <p className="text-sm text-orange-700 font-medium">Streak</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Current Deck Info */}
        <Card className="mb-8 card-enhanced">
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="w-full min-w-0">
                <h2 className="text-lg sm:text-xl font-semibold mb-1 flex items-center gap-2 leading-tight">
                  <BookOpen className="h-5 w-5 text-blue-600" />
                  Current Deck
                </h2>
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span className="text-base sm:text-lg font-medium break-words">{currentDeck.name}</span>
                  <span className="px-2 py-0.5 sm:px-3 sm:py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                    {currentDeck.difficulty_level}
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-gray-600 mt-1">
                  {currentDeck.language_a_name} → {currentDeck.language_b_name}
                </p>
              </div>
              <Button 
                onClick={() => setShowDeckSelection(true)}
                className="btn-outline flex items-center gap-2 w-full sm:w-auto"
              >
                <LibraryBig className="h-4 w-4" />
                Change Deck
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Current Deck Progress */}
        <Card className="mb-8 card-enhanced">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-600" />
              Deck Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* Progress Bar */}
            <div className="mb-6">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Overall Progress</span>
                <span>{Math.round(progressPercentage)}%</span>
              </div>
              <Progress value={progressPercentage} className="h-3" />
            </div>

            {/* Word Categories */}
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
              <div className="progress-indicator progress-unseen">
                <p className="text-2xl font-bold text-gray-600">{metrics.unseen}</p>
                <p className="text-sm text-gray-700 font-medium">Unseen</p>
              </div>
              <div className="progress-indicator progress-leeches">
                <p className="text-2xl font-bold text-red-600">{metrics.leeches}</p>
                <p className="text-sm text-red-700 font-medium">Leeches</p>
              </div>
              <div className="progress-indicator progress-learning">
                <p className="text-2xl font-bold text-orange-600">{metrics.learning}</p>
                <p className="text-sm text-orange-700 font-medium">Learning</p>
              </div>
              <div className="progress-indicator progress-strengthening">
                <p className="text-2xl font-bold text-yellow-600">{metrics.strengthening}</p>
                <p className="text-sm text-yellow-700 font-medium">Strengthening</p>
              </div>
              <div className="progress-indicator progress-consolidating">
                <p className="text-2xl font-bold text-blue-600">{metrics.consolidating}</p>
                <p className="text-sm text-blue-700 font-medium">Consolidating</p>
              </div>
              <div className="progress-indicator progress-mastered">
                <p className="text-2xl font-bold text-green-600">{metrics.mastered}</p>
                <p className="text-sm text-green-700 font-medium">Mastered</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Session Types */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="flex flex-col card-enhanced">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-green-600" />
                Discovery
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <div className="flex-1">
                <p className="text-gray-600 mb-4">
                  Learn new words from your selected deck
                </p>
                
                {/* Queue Numbers */}
                <div className="mb-4 p-4 bg-green-50 rounded-lg border border-green-200">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{unseenQueue.length}</div>
                    <div className="text-sm text-green-700 font-medium">Unseen Words</div>
                  </div>
                </div>
              </div>
              
              <Button 
                onClick={() => handleStartSession('discovery')}
                className="btn-success w-full text-lg mt-auto"
                disabled={!currentDeck || sessionSettings.types.length === 0}
              >
                <Target className="h-5 w-5 mr-2" />
                Start Discovery
              </Button>
            </CardContent>
          </Card>

          <Card className="flex flex-col card-enhanced">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Play className="h-5 w-5 text-blue-600" />
                Review
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <div className="flex-1">
                <p className="text-gray-600 mb-4">
                  Review words you&apos;ve learned using spaced repetition
                </p>
                
                {/* Queue Numbers */}
                <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  {reviewQueue.length > 0 ? (
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{reviewQueue.length}</div>
                      <div className="text-sm text-blue-700 font-medium">Due Now</div>
                    </div>
                  ) : nearFutureQueue.length > 0 ? (
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">{nearFutureQueue.length}</div>
                      <div className="text-sm text-orange-700 font-medium">Due Soon</div>
                    </div>
                  ) : (
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-400">0</div>
                      <div className="text-sm text-gray-500 font-medium">No words due</div>
                    </div>
                  )}
                </div>
              </div>
              
              <Button 
                onClick={() => handleStartSession('review')}
                className="btn-primary w-full text-lg mt-auto"
                disabled={!currentDeck || sessionSettings.types.length === 0}
              >
                <Play className="h-5 w-5 mr-2" />
                Start Review
              </Button>
            </CardContent>
          </Card>

          <Card className="flex flex-col card-enhanced">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-purple-600" />
                Deep Dive
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <div className="flex-1">
                <p className="text-gray-600 mb-4">
                  Focus on specific categories like leeches or learning words
                </p>
                {/* Deep Dive banner removed as feature is live */}
                
                <select
                  value={deepDiveCategory || ''}
                  onChange={(e) => setDeepDiveCategory(e.target.value as 'leeches' | 'learning' | 'strengthening' | 'consolidating' | null)}
                  className="w-full p-3 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  disabled={!currentDeck || sessionSettings.types.length === 0}
                >
                  <option value="">Select a category...</option>
                  <option value="leeches">Leeches (struggling words)</option>
                  <option value="learning">Learning (new words)</option>
                  <option value="strengthening">Strengthening (improving words)</option>
                  <option value="consolidating">Consolidating (mastering words)</option>
                </select>
              </div>
              
              <Button 
                onClick={() => handleStartSession('deep-dive')}
                className="btn-purple w-full text-lg mt-auto"
                disabled={!currentDeck || sessionSettings.types.length === 0 || !deepDiveCategory}
              >
                <Brain className="h-5 w-5 mr-2" />
                Start Deep Dive
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Queue Status - At the very bottom */}
        <Card className="mb-8 card-enhanced">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-600" />
              Queue Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Zap className="h-5 w-5 text-red-600" />
                  <span className="text-lg font-bold text-red-600">{reviewQueue.length}</span>
                </div>
                <p className="text-sm font-medium text-red-700">Due Now</p>
                <p className="text-xs text-red-600">Ready for review</p>
              </div>
              
              <div className="text-center p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Clock className="h-5 w-5 text-orange-600" />
                  <span className="text-lg font-bold text-orange-600">{nearFutureQueue.length}</span>
                </div>
                <p className="text-sm font-medium text-orange-700">Due Soon</p>
                <p className="text-xs text-orange-600">Coming up next</p>
              </div>
              
              <div className="text-center p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Brain className="h-5 w-5 text-blue-600" />
                  <span className="text-lg font-bold text-blue-600">{practicePool.length}</span>
                </div>
                <p className="text-sm font-medium text-blue-700">Practice</p>
                <p className="text-xs text-blue-600">Extra practice</p>
              </div>
              
              <div className="text-center p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <EyeOff className="h-5 w-5 text-gray-600" />
                  <span className="text-lg font-bold text-gray-600">{unseenQueue.length}</span>
                </div>
                <p className="text-sm font-medium text-gray-700">Unseen</p>
                <p className="text-xs text-gray-600">New words</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Learning Types Configuration - At the bottom */}
        <Card className="mb-8 card-enhanced">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-blue-600" />
              Learning Types
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Learning Type Options */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <Label className="text-base font-medium">Select Learning Types</Label>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={handleSelectAllTypes}
                      className="btn-outline"
                    >
                      Select All
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={handleClearAllTypes}
                      className="btn-outline"
                    >
                      Clear All
                    </Button>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-center space-x-3 p-4 border rounded-lg">
                    <Checkbox
                      id="recognition"
                      checked={sessionSettings.types.includes('recognition')}
                      onCheckedChange={() => handleLearningTypeToggle('recognition')}
                    />
                    <Label htmlFor="recognition" className="flex items-center gap-2 cursor-pointer flex-1">
                      <Eye className="h-5 w-5 text-blue-600" />
                      <div>
                        <div className="font-medium">Language A → Language B</div>
                        <div className="text-sm text-gray-600">Recognition</div>
                      </div>
                    </Label>
                  </div>
                  
                  <div className="flex items-center space-x-3 p-4 border rounded-lg">
                    <Checkbox
                      id="production"
                      checked={sessionSettings.types.includes('production')}
                      onCheckedChange={() => handleLearningTypeToggle('production')}
                    />
                    <Label htmlFor="production" className="flex items-center gap-2 cursor-pointer flex-1">
                      <MessageSquare className="h-5 w-5 text-green-600" />
                      <div>
                        <div className="font-medium">Language B → Language A</div>
                        <div className="text-sm text-gray-600">Production</div>
                      </div>
                    </Label>
                  </div>
                  
                  <div className="flex items-center space-x-3 p-4 border rounded-lg">
                    <Checkbox
                      id="listening"
                      checked={sessionSettings.types.includes('listening')}
                      onCheckedChange={() => handleLearningTypeToggle('listening')}
                    />
                    <Label htmlFor="listening" className="flex items-center gap-2 cursor-pointer flex-1">
                      <Ear className="h-5 w-5 text-purple-600" />
                      <div>
                        <div className="font-medium">Voice First</div>
                        <div className="text-sm text-gray-600">Listening</div>
                      </div>
                    </Label>
                  </div>
                </div>
              </div>

              {/* Status */}
              {sessionSettings.types.length === 0 && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    ⚠️ Please select at least one learning type to start sessions.
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
