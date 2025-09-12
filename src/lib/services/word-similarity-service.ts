import { supabase } from '@/lib/supabase'

export interface SimilarWord {
  wordId: number
  word: string
  translation: string
  sentence?: string
  sentenceTranslation?: string
}

let MAX_SIMILAR_WORDS = 5

export function setMaxSimilarWords(maxCount: number): void {
  const safe = Math.max(0, Math.floor(maxCount))
  MAX_SIMILAR_WORDS = safe
}

export class WordSimilarityService {
  /**
   * Get similar words for a given vocabulary ID.
   * Uses directed edges (source_word_id -> target_word_id).
   * The number returned is capped by a configurable max (default 5).
   */
  static async getSimilarWords(wordId: number, limit: number = MAX_SIMILAR_WORDS): Promise<SimilarWord[]> {
    try {
      const effectiveLimit = Math.max(0, Math.floor(limit))

      type Row = {
        target_word_id: number
        vocabulary: {
          id: number
          language_a_word: string
          language_b_translation: string
          language_a_sentence: string | null
          language_b_sentence: string | null
        } | null
      }

      const { data, error } = await supabase
        .from('word_similarities')
        .select(
          `
          target_word_id,
          vocabulary:target_word_id(
            id,
            language_a_word,
            language_b_translation,
            language_a_sentence,
            language_b_sentence
          )
        `
        )
        .eq('source_word_id', wordId)
        .limit(effectiveLimit)

      if (error) {
        console.error('getSimilarWords error:', error)
        return []
      }

      const rows: Row[] = (data as unknown as Row[]) || []
      return rows.map((row) => {
        const vocab = row.vocabulary
        return {
          wordId: vocab?.id,
          word: vocab?.language_a_word,
          translation: vocab?.language_b_translation,
          sentence: vocab?.language_a_sentence || undefined,
          sentenceTranslation: vocab?.language_b_sentence || undefined,
        } as SimilarWord
      }).filter((w: SimilarWord) => Boolean(w.wordId))
    } catch (e) {
      console.error('getSimilarWords exception:', e)
      return []
    }
  }

  /**
   * Get similar words restricted to a specific deck.
   */
  static async getSimilarWordsInDeck(wordId: number, deckId: string, limit: number = MAX_SIMILAR_WORDS): Promise<SimilarWord[]> {
    try {
      const effectiveLimit = Math.max(0, Math.floor(limit))

      // First fetch target ids for the source word
      type EdgeRow = { target_word_id: number }
      const { data: edges, error: edgeError } = await supabase
        .from('word_similarities')
        .select('target_word_id')
        .eq('source_word_id', wordId)
        .limit(200)

      if (edgeError || !edges || edges.length === 0) return []

      const targetIds = (edges as unknown as EdgeRow[]).map((e) => e.target_word_id)

      // Intersect with the deck vocabulary
      type DeckVocabRow = { vocabulary_id: number }
      const { data: deckVocab, error: deckError } = await supabase
        .from('deck_vocabulary')
        .select('vocabulary_id')
        .eq('deck_id', deckId)
        .in('vocabulary_id', targetIds)

      if (deckError || !deckVocab || deckVocab.length === 0) return []

      const allowedIds = (deckVocab as unknown as DeckVocabRow[]).map((d) => d.vocabulary_id)

      // Fetch vocabulary rows for the allowed ids
      type VocabRow = { id: number; language_a_word: string; language_b_translation: string; language_a_sentence: string | null; language_b_sentence: string | null }
      const { data: words, error: vocabError } = await supabase
        .from('vocabulary')
        .select('id, language_a_word, language_b_translation, language_a_sentence, language_b_sentence')
        .in('id', allowedIds)
        // no limit here; we slice after mapping to ensure we can always reach the cap

      if (vocabError || !words) return []

      const mapped = (words as unknown as VocabRow[]).map((v) => ({
        wordId: v.id,
        word: v.language_a_word,
        translation: v.language_b_translation,
        sentence: v.language_a_sentence || undefined,
        sentenceTranslation: v.language_b_sentence || undefined,
      } as SimilarWord))

      return mapped.slice(0, effectiveLimit)
    } catch (e) {
      console.error('getSimilarWordsInDeck exception:', e)
      return []
    }
  }
}


