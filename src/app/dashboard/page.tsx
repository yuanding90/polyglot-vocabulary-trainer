'use client'

import { useState, useEffect } from 'react'
import { useVocabularyStore } from '@/store/vocabulary-store'
import { supabase, VocabularyDeck } from '@/lib/supabase'
import { sessionQueueManager } from '@/lib/session-queues'
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
  const [currentUser, setCurrentUser] = useState<any>(null)

  useEffect(() => {
    // Get current user first
    const getCurrentUser = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      setCurrentUser(user)
      if (user) {
        await loadDashboardData(user.id)
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

  const loadDashboardData = async (userId: string) => {
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
  }

  const loadDeckData = async (deckId: string, userId: string) => {
    try {
      console.log('Loading deck data for deck:', deckId, 'user:', userId)
      
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

      // Update userDeckProgress with correct total words
      const totalWords = deckMetrics.unseen + deckMetrics.leeches + deckMetrics.learning + deckMetrics.strengthening + deckMetrics.consolidating + deckMetrics.mastered
      setUserDeckProgress(deckId, {
        deck_id: deckId,
        total_words: totalWords,
        mastered_words: deckMetrics.mastered,
        learning_words: deckMetrics.learning,
        leeches: deckMetrics.leeches,
        unseen_words: deckMetrics.unseen
      })
    } catch (error) {
      console.error('Error loading deck data:', error)
    }
  }

  const loadSessionStats = async (userId: string) => {
    try {
      const today = new Date()
      const sevenDaysAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
      const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)

      // Get session statistics
      const { data: sessions, error } = await supabase
        .from('study_sessions')
        .select('*')
        .eq('user_id', userId)
        .gte('created_at', thirtyDaysAgo.toISOString())

      if (error) throw error

      const stats = {
        reviewsToday: 0,
        reviews7Days: 0,
        reviews30Days: 0,
        currentStreak: 0
      }

      console.log('Session stats debug:', {
        totalSessions: sessions?.length || 0,
        sessions: sessions?.slice(0, 3).map(s => ({
          created_at: s.created_at,
          words_studied: s.words_studied,
          session_type: s.session_type
        }))
      })

      sessions?.forEach(session => {
        const sessionDate = new Date(session.created_at)
        
        if (sessionDate.toDateString() === today.toDateString()) {
          stats.reviewsToday += session.words_studied
        }
        
        if (sessionDate >= sevenDaysAgo) {
          stats.reviews7Days += session.words_studied
        }
        
        if (sessionDate >= thirtyDaysAgo) {
          stats.reviews30Days += session.words_studied
        }
      })

      console.log('Calculated stats:', stats)
      updateSessionStats(stats)
    } catch (error) {
      console.error('Error loading session stats:', error)
    }
  }

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
    
    // Store session type and redirect to study session
    localStorage.setItem('sessionType', type)
    window.location.href = '/study'
  }

  const handleSessionEnd = () => {
    setShowStudySession(false)
    setSessionType(null)
    // Reload dashboard data to reflect session results
    loadDashboardData()
    // Also reload session stats
    if (currentUser) {
      loadSessionStats(currentUser.id)
    }
  }

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

  const goBackToDeckSelection = () => {
    localStorage.removeItem('selectedDeck')
    setCurrentDeck(null)
    setShowDeckSelection(true)
  }

  const selectDeck = (deck: VocabularyDeck) => {
    localStorage.setItem('selectedDeck', JSON.stringify(deck))
    setCurrentDeck(deck)
    setShowDeckSelection(false)
    // Load deck data with current user
    if (currentUser) {
      loadDeckData(deck.id, currentUser.id)
    }
  }

  const handleSignOut = async () => {
    await supabase.auth.signOut()
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

          {availableDecks.length === 0 ? (
            <div className="text-center py-12">
              <BookOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Decks Available</h3>
                              <p className="text-gray-600">
                  Vocabulary decks will appear here once they&apos;re added to the system.
                </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {availableDecks.map((deck) => {
                const progress = userDeckProgress[deck.id] || {
                  deck_id: deck.id,
                  total_words: 0,
                  mastered_words: 0,
                  learning_words: 0,
                  leeches: 0,
                  unseen_words: 0
                }
                
                // Calculate progress percentages for different states
                const totalWords = progress.total_words || deck.total_words
                const mastered = progress.mastered_words
                const learning = progress.learning_words
                const unseen = progress.unseen_words
                
                return (
                  <Card 
                    key={deck.id} 
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
                          
                          {/* Progress Bar */}
                                                      <div className="space-y-4">
                            <div className="flex justify-between text-sm text-gray-600">
                              <span>Progress Overview</span>
                              <span>{progress.mastered_words}/{totalWords} mastered</span>
                            </div>
                            
                            <div className="flex h-4 bg-gray-200 rounded-full overflow-hidden">
                              {/* Unseen */}
                              <div 
                                className="bg-gray-400"
                                style={{ width: `${(unseen / totalWords) * 100}%` }}
                                title={`${unseen} unseen`}
                              />
                              {/* Learning */}
                              <div 
                                className="bg-orange-400"
                                style={{ width: `${(learning / totalWords) * 100}%` }}
                                title={`${learning} learning`}
                              />
                              {/* Strengthening */}
                              <div 
                                className="bg-yellow-400"
                                style={{ width: `${(Math.max(0, totalWords - unseen - learning - mastered) / totalWords) * 100}%` }}
                                title="strengthening"
                              />
                              {/* Mastered */}
                              <div 
                                className="bg-green-500"
                                style={{ width: `${(mastered / totalWords) * 100}%` }}
                                title={`${mastered} mastered`}
                              />
                            </div>
                            
                            <div className="grid grid-cols-4 gap-6 mt-6">
                              <div className="text-center">
                                <UnseenIcon className="h-5 w-5 mx-auto mb-2 text-gray-400" />
                                <div className="text-xl font-bold text-gray-500">{unseen}</div>
                                <div className="text-sm text-gray-400 font-medium">Unseen</div>
                              </div>
                              <div className="text-center">
                                <LearningIcon className="h-5 w-5 mx-auto mb-2 text-orange-400" />
                                <div className="text-xl font-bold text-orange-500">{learning}</div>
                                <div className="text-sm text-gray-400 font-medium">Learning</div>
                              </div>
                              <div className="text-center">
                                <StrengtheningIcon className="h-5 w-5 mx-auto mb-2 text-yellow-400" />
                                <div className="text-xl font-bold text-yellow-500">{Math.max(0, totalWords - unseen - learning - mastered)}</div>
                                <div className="text-sm text-gray-400 font-medium">Strengthening</div>
                              </div>
                              <div className="text-center">
                                <MasteredIcon className="h-5 w-5 mx-auto mb-2 text-green-400" />
                                <div className="text-xl font-bold text-green-500">{mastered}</div>
                                <div className="text-sm text-gray-400 font-medium">Mastered</div>
                              </div>
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
          )}
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
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">🐰 Polyglot Vocabulary Trainer</h1>
              <p className="text-gray-600">Master vocabulary with spaced repetition</p>
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
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold mb-2 flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-blue-600" />
                  Current Deck
                </h2>
                <div className="flex items-center gap-3">
                  <span className="text-lg font-medium">{currentDeck.name}</span>
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                    {currentDeck.difficulty_level}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {currentDeck.language_a_name} → {currentDeck.language_b_name}
                </p>
              </div>
              <Button 
                onClick={() => setShowDeckSelection(true)}
                className="btn-outline flex items-center gap-2"
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
