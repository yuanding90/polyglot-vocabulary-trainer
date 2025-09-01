import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { 
  Vocabulary, 
  UserProgress, 
  VocabularyDeck, 
  UserDeckProgress
} from '@/lib/supabase'

export interface SessionSettings {
  types: ('recognition' | 'production' | 'listening')[]
}

interface VocabularyState {
  // Current session
  currentWord: Vocabulary | null
  sessionWords: Vocabulary[]
  sessionType: 'review' | 'discovery' | 'deep-dive' | null
  currentDeck: VocabularyDeck | null
  
  // Session settings
  sessionSettings: SessionSettings
  
  // Available decks
  availableDecks: VocabularyDeck[]
  userDeckProgress: Record<string, UserDeckProgress>
  
  // Progress tracking
  userProgress: Record<number, UserProgress>
  metrics: {
    unseen: number
    leeches: number
    learning: number
    strengthening: number
    consolidating: number
    mastered: number
  }
  
  // Session stats
  sessionStats: {
    reviewsToday: number
    reviews7Days: number
    reviews30Days: number
    currentStreak: number
  }

  // Session queues
  unseenQueue: Vocabulary[]
  reviewQueue: Vocabulary[]
  practicePool: Vocabulary[]
  nearFutureQueue: Vocabulary[]
  
  // Actions
  setCurrentWord: (word: Vocabulary | null) => void
  setSessionWords: (words: Vocabulary[]) => void
  setSessionType: (type: 'review' | 'discovery' | 'deep-dive' | null) => void
  setCurrentDeck: (deck: VocabularyDeck | null) => void
  setSessionSettings: (settings: SessionSettings) => void
  setAvailableDecks: (decks: VocabularyDeck[]) => void
  setUserDeckProgress: (deckId: string, progress: UserDeckProgress) => void
  setUserDeckProgressMap: (progressMap: Record<string, UserDeckProgress>) => void
  updateUserProgress: (wordId: number, progress: Partial<UserProgress>) => void
  updateMetrics: (metrics: Partial<VocabularyState['metrics']>) => void
  updateSessionStats: (stats: Partial<VocabularyState['sessionStats']>) => void
  setUnseenQueue: (words: Vocabulary[]) => void
  setReviewQueue: (words: Vocabulary[]) => void
  setPracticePool: (words: Vocabulary[]) => void
  setNearFutureQueue: (words: Vocabulary[]) => void
  resetSession: () => void
}

const defaultSessionSettings: SessionSettings = {
  types: ['recognition', 'production']
}

export const useVocabularyStore = create<VocabularyState>()(
  persist(
    (set) => ({
      // Initial state
      currentWord: null,
      sessionWords: [],
      sessionType: null,
      currentDeck: null,
      sessionSettings: defaultSessionSettings,
      availableDecks: [],
      userDeckProgress: {},
      userProgress: {},
      metrics: {
        unseen: 0,
        leeches: 0,
        learning: 0,
        strengthening: 0,
        consolidating: 0,
        mastered: 0,
      },
      sessionStats: {
        reviewsToday: 0,
        reviews7Days: 0,
        reviews30Days: 0,
        currentStreak: 0,
      },
      unseenQueue: [],
      reviewQueue: [],
      practicePool: [],
      nearFutureQueue: [],
      
      // Actions
      setCurrentWord: (word) => set({ currentWord: word }),
      setSessionWords: (words) => set({ sessionWords: words }),
      setSessionType: (type) => set({ sessionType: type }),
      setCurrentDeck: (deck) => set({ currentDeck: deck }),
      setSessionSettings: (settings) => set({ sessionSettings: settings }),
      setAvailableDecks: (decks) => set({ availableDecks: decks }),
      setUserDeckProgress: (deckId, progress) => 
        set((state) => ({
          userDeckProgress: {
            ...state.userDeckProgress,
            [deckId]: progress,
          },
        })),
      setUserDeckProgressMap: (progressMap) => 
        set({ userDeckProgress: progressMap }),
      updateUserProgress: (wordId, progress) => 
        set((state) => ({
          userProgress: {
            ...state.userProgress,
            [wordId]: { ...state.userProgress[wordId], ...progress } as UserProgress,
          },
        })),
      updateMetrics: (metrics) => 
        set((state) => ({
          metrics: { ...state.metrics, ...metrics },
        })),
      updateSessionStats: (stats) => 
        set((state) => ({
          sessionStats: { ...state.sessionStats, ...stats },
        })),
      setUnseenQueue: (words) => set({ unseenQueue: words }),
      setReviewQueue: (words) => set({ reviewQueue: words }),
      setPracticePool: (words) => set({ practicePool: words }),
      setNearFutureQueue: (words) => set({ nearFutureQueue: words }),
      resetSession: () => 
        set({
          currentWord: null,
          sessionWords: [],
          sessionType: null,
          currentDeck: null,
        }),
    }),
    {
      name: 'vocabulary-store',
      partialize: (state) => ({
        currentDeck: state.currentDeck,
        sessionSettings: state.sessionSettings,
        availableDecks: state.availableDecks,
        userDeckProgress: state.userDeckProgress,
        userProgress: state.userProgress,
        metrics: state.metrics,
        sessionStats: state.sessionStats,
      }),
    }
  )
)
