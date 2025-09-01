import { supabase } from './supabase'
import { Vocabulary, UserProgress } from './supabase'
import { isDueForReview, isNearFuture, SRS } from './utils'

export interface QueueManager {
  buildQueues: (deckId: string, userId: string) => Promise<{
    unseen: Vocabulary[]
    review: Vocabulary[]
    practice: Vocabulary[]
    nearFuture: Vocabulary[]
  }>
  calculateMetrics: (userId: string, deckId: string) => Promise<{
    unseen: number
    leeches: number
    learning: number
    strengthening: number
    consolidating: number
    mastered: number
  }>
}

export class SessionQueueManager implements QueueManager {
  // Apply smart spacing for leeches to prevent fatigue
  private applyLeechSpacing(words: Vocabulary[], progressMap: Map<number, UserProgress>): Vocabulary[] {
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

  async buildQueues(deckId: string, userId: string) {
    try {
      // Get all vocabulary for the deck
      const { data: deckVocab, error: deckError } = await supabase
        .from('deck_vocabulary')
        .select('vocabulary_id')
        .eq('deck_id', deckId)
        .order('word_order')

      if (deckError) {
        console.error('Error fetching deck vocabulary:', deckError)
        return { unseen: [], review: [], practice: [], nearFuture: [] }
      }

      if (!deckVocab || deckVocab.length === 0) {
        console.log('No vocabulary found for deck:', deckId)
        return { unseen: [], review: [], practice: [], nearFuture: [] }
      }

      const vocabIds = deckVocab.map(item => item.vocabulary_id)

      // Get vocabulary words
      const { data: words, error: wordsError } = await supabase
        .from('vocabulary')
        .select('*')
        .in('id', vocabIds)

      if (wordsError) {
        console.error('Error fetching vocabulary words:', wordsError)
        return { unseen: [], review: [], practice: [], nearFuture: [] }
      }

      if (!words || words.length === 0) {
        console.log('No words found for vocabulary IDs:', vocabIds)
        return { unseen: [], review: [], practice: [], nearFuture: [] }
      }

      // Get user progress for this deck
      const { data: userProgress, error: progressError } = await supabase
        .from('user_progress')
        .select('*')
        .eq('user_id', userId)
        .eq('deck_id', deckId)

      if (progressError) {
        // Only log actual errors, not "no rows found" which is expected for new users
        // Check for various "no data" error conditions
        const isNoDataError = 
          progressError.code === 'PGRST116' || 
          progressError.message?.includes('No rows found') ||
          progressError.message?.includes('no rows returned') ||
          progressError.message?.includes('not found') ||
          Object.keys(progressError).length === 0 // Empty error object is also "no data"
        
        if (!isNoDataError) {
          console.error('Error fetching user progress:', progressError)
        }
        // Don't throw error, just use empty progress
      }

      const progressMap = new Map<number, UserProgress>(userProgress?.map(p => [p.word_id, p]) || [])

      // Build queues
      const unseen: Vocabulary[] = []
      const review: Vocabulary[] = []
      const practice: Vocabulary[] = []
      const nearFuture: Vocabulary[] = []

      words.forEach(word => {
        const progress = progressMap.get(word.id)
        
        if (!progress) {
          // No progress - unseen word
          unseen.push(word)
        } else {
          // Has progress - check if due for review
          if (isDueForReview(progress.next_review_date)) {
            review.push(word)
          } else if (isNearFuture(progress.next_review_date)) {
            nearFuture.push(word)
          } else {
            // Not due - available for practice
            practice.push(word)
          }
        }
      })

      // If no Due Now words, use Due Soon words for review
      if (review.length === 0 && nearFuture.length > 0) {
        console.log(`No Due Now words, using ${nearFuture.length} Due Soon words for review`)
        review.push(...nearFuture)
        nearFuture.length = 0 // Clear near future since we're using them
      }

      // Note: We don't move unseen words to review queue here
      // This keeps the dashboard display correct (Unseen: full count, Due Now: 0)
      // The study session will handle the logic of using unseen words for review when needed

      // Apply leech spacing to review queue
      const spacedReview = this.applyLeechSpacing(review, progressMap)

      return { unseen, review: spacedReview, practice, nearFuture }
    } catch (error) {
      console.error('Error building queues:', error)
      return { unseen: [], review: [], practice: [], nearFuture: [] }
    }
  }

  async calculateMetrics(userId: string, deckId: string) {
    try {
      // First, get the total words in the deck
      const { data: deckVocab, error: deckVocabError } = await supabase
        .from('deck_vocabulary')
        .select('vocabulary_id')
        .eq('deck_id', deckId)

      if (deckVocabError) {
        console.error('Error fetching deck vocabulary for metrics:', deckVocabError)
        return {
          unseen: 0,
          leeches: 0,
          learning: 0,
          strengthening: 0,
          consolidating: 0,
          mastered: 0
        }
      }

      const totalWords = deckVocab?.length || 0

      // If no words in deck, return all zeros
      if (totalWords === 0) {
        return {
          unseen: 0,
          leeches: 0,
          learning: 0,
          strengthening: 0,
          consolidating: 0,
          mastered: 0
        }
      }

      // Get user progress for this deck
      const { data: userProgress, error } = await supabase
        .from('user_progress')
        .select('*')
        .eq('user_id', userId)
        .eq('deck_id', deckId)

      if (error) {
        // Only log actual errors, not "no rows found" which is expected for new users
        // Check for various "no data" error conditions
        const isNoDataError = 
          error.code === 'PGRST116' || 
          error.message?.includes('No rows found') ||
          error.message?.includes('no rows returned') ||
          error.message?.includes('not found') ||
          Object.keys(error).length === 0 // Empty error object is also "no data"
        
        if (!isNoDataError) {
          console.error('Error fetching user progress for metrics:', error)
        }
        // For new users with no progress, all words are unseen
        return {
          unseen: totalWords,
          leeches: 0,
          learning: 0,
          strengthening: 0,
          consolidating: 0,
          mastered: 0
        }
      }

      const metrics = {
        unseen: 0,
        leeches: 0,
        learning: 0,
        strengthening: 0,
        consolidating: 0,
        mastered: 0
      }

      // Count words by progress state
      userProgress?.forEach(progress => {
        if (progress.again_count >= SRS.LEECH_THRESHOLD) {
          metrics.leeches++
        } else if (progress.interval < 7) {
          metrics.learning++
        } else if (progress.interval < 21) {
          metrics.strengthening++
        } else if (progress.interval < 60) {
          metrics.consolidating++
        } else {
          metrics.mastered++
        }
      })

      console.log('Metrics calculation debug:', {
        totalWords,
        totalProgress: userProgress?.length || 0,
        leeches: metrics.leeches,
        learning: metrics.learning,
        strengthening: metrics.strengthening,
        consolidating: metrics.consolidating,
        mastered: metrics.mastered,
        sampleProgress: userProgress?.slice(0, 3).map(p => ({
          interval: p.interval,
          repetitions: p.repetitions,
          again_count: p.again_count
        }))
      })

      // Calculate unseen words
      const seenWords = userProgress?.length || 0
      metrics.unseen = Math.max(0, totalWords - seenWords)

      return metrics
    } catch (error) {
      console.error('Error calculating metrics:', error)
      return {
        unseen: 0,
        leeches: 0,
        learning: 0,
        strengthening: 0,
        consolidating: 0,
        mastered: 0
      }
    }
  }
}

export const sessionQueueManager = new SessionQueueManager()
