import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Database types for multi-language vocabulary trainer
export interface Vocabulary {
  id: number
  language_a_word: string
  language_b_translation: string
  language_a_sentence: string
  language_b_sentence: string
  created_at: string
  updated_at: string
}

export interface VocabularyDeck {
  id: string
  name: string
  description: string
  language_a_code: string
  language_b_code: string
  language_a_name: string
  language_b_name: string
  difficulty_level: 'beginner' | 'intermediate' | 'advanced' | 'master'
  total_words: number
  created_at: string
  is_active: boolean
}

export interface UserProgress {
  id: string
  user_id: string
  word_id: number
  deck_id: string
  repetitions: number
  interval: number
  ease_factor: number
  next_review_date: string
  again_count: number
  created_at: string
  updated_at: string
}

export interface UserDeckProgress {
  deck_id: string
  total_words: number
  mastered_words: number
  learning_words: number
  leeches: number
  unseen_words: number
  strengthening_words?: number
  consolidating_words?: number
}

export interface StudySession {
  id: string
  user_id: string
  deck_id: string
  session_type: 'review' | 'discovery' | 'deep-dive'
  words_studied: number
  correct_answers: number
  session_duration: number
  completed_at: string
  created_at: string
}
