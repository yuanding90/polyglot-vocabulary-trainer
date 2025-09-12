# Approach 1: Centralized Similarity Service - Detailed Design

## Architecture Overview

### Core Principles
- **Separation of Concerns**: Similarity data completely separate from vocabulary decks
- **ID-Based Relationships**: All relationships use unique IDs, eliminating string matching issues
- **Algorithm Agnostic**: Support multiple similarity algorithms with versioning
- **Cross-Deck Awareness**: Similar words can exist across different decks
- **Performance Optimized**: Efficient lookups with proper indexing and caching

## Database Schema Design

### 1. Vocabulary Words Registry
```sql
-- Central registry for all vocabulary words across all decks
CREATE TABLE vocabulary_words (
    id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    language_code VARCHAR(5) NOT NULL, -- 'fr', 'en', 'de', etc.
    normalized_word TEXT NOT NULL, -- For accent-insensitive lookups
    word_length INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_word_per_language UNIQUE (word, language_code),
    CONSTRAINT valid_language_code CHECK (language_code ~ '^[a-z]{2}$')
);

-- Indexes for performance
CREATE INDEX idx_vocabulary_words_word ON vocabulary_words(word);
CREATE INDEX idx_vocabulary_words_normalized ON vocabulary_words(normalized_word);
CREATE INDEX idx_vocabulary_words_language ON vocabulary_words(language_code);
CREATE INDEX idx_vocabulary_words_length ON vocabulary_words(word_length);
```

### 2. Word Similarity Relationships
```sql
-- Similarity relationships between words
CREATE TABLE word_similarities (
    id SERIAL PRIMARY KEY,
    source_word_id INTEGER NOT NULL REFERENCES vocabulary_words(id) ON DELETE CASCADE,
    target_word_id INTEGER NOT NULL REFERENCES vocabulary_words(id) ON DELETE CASCADE,
    
    -- Similarity metrics
    similarity_score DECIMAL(5,4) NOT NULL CHECK (similarity_score >= 0 AND similarity_score <= 1),
    rule_types TEXT[] NOT NULL, -- Array of rule types that matched
    confidence_level DECIMAL(3,2) DEFAULT 0.85, -- Algorithm confidence
    
    -- Algorithm metadata
    algorithm_version VARCHAR(20) NOT NULL DEFAULT 'enhanced_v1',
    algorithm_parameters JSONB, -- Store algorithm-specific parameters
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT no_self_similarity CHECK (source_word_id != target_word_id),
    CONSTRAINT unique_similarity_per_algorithm UNIQUE (source_word_id, target_word_id, algorithm_version)
);

-- Indexes for efficient lookups
CREATE INDEX idx_word_similarities_source ON word_similarities(source_word_id);
CREATE INDEX idx_word_similarities_target ON word_similarities(target_word_id);
CREATE INDEX idx_word_similarities_score ON word_similarities(similarity_score DESC);
CREATE INDEX idx_word_similarities_algorithm ON word_similarities(algorithm_version);
CREATE INDEX idx_word_similarities_rules ON word_similarities USING GIN (rule_types);

-- Composite indexes for common queries
CREATE INDEX idx_similarities_lookup ON word_similarities(source_word_id, similarity_score DESC);
CREATE INDEX idx_similarities_reverse ON word_similarities(target_word_id, similarity_score DESC);
```

### 3. Algorithm Registry
```sql
-- Track different similarity algorithms and their versions
CREATE TABLE similarity_algorithms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    parameters_schema JSONB, -- JSON schema for algorithm parameters
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_algorithm_version UNIQUE (name, version)
);

-- Insert default algorithm
INSERT INTO similarity_algorithms (name, version, description) VALUES 
('enhanced_cognitive_rules', 'v1', 'Enhanced Cognitive Rules Engine with 6 rules');
```

### 4. User Similarity Progress (Optional Enhancement)
```sql
-- Track user-specific progress with similar words
CREATE TABLE user_similarity_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    similarity_id INTEGER NOT NULL REFERENCES word_similarities(id) ON DELETE CASCADE,
    
    -- User interaction metrics
    confusion_count INTEGER DEFAULT 0,
    last_confused_at TIMESTAMP WITH TIME ZONE,
    mastery_level INTEGER DEFAULT 0 CHECK (mastery_level >= 0 AND mastery_level <= 5),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_user_similarity UNIQUE (user_id, similarity_id)
);

CREATE INDEX idx_user_similarity_progress_user ON user_similarity_progress(user_id);
CREATE INDEX idx_user_similarity_progress_similarity ON user_similarity_progress(similarity_id);
```

## Data Migration Strategy

### Phase 1: Extract and Normalize Vocabulary
```python
# scripts/migrate_vocabulary_words.py
import sqlite3
import csv
from supabase import create_client
from typing import Set, Dict
import unicodedata

class VocabularyMigrator:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase = create_client(supabase_url, supabase_key)
        self.vocab_bank_path = "/Users/ding/Desktop/Coding/Vocabulary Learning App/vocab bank"
        
    def normalize_word(self, word: str) -> str:
        """Normalize word for accent-insensitive lookups"""
        return ''.join(
            c for c in unicodedata.normalize('NFD', word.lower())
            if unicodedata.category(c) != 'Mn'
        )
    
    def extract_all_french_words(self) -> Set[str]:
        """Extract all unique French words from all databases"""
        french_databases = [
            "pre_vocab_batch_1.db", "pre_vocab_batch_2.db", "pre_vocab_batch_3.db",
            "french_vocab_batch_1.db", "french_vocab_batch_2.db", "french_vocab_batch_3.db",
            "french_vocab_batch_4.db", "french_vocab_batch_5.db", "french_vocab_batch_6.db",
            "french_vocab_batch_7.db", "french_vocab_batch_8.db", "french_vocab_batch_9.db",
            "french_vocab_batch_10.db", "french_vocab_batch_11.db", "french_vocab_batch_12.db",
            "french_vocab_batch_13.db"
        ]
        
        all_words = set()
        
        for db_file in french_databases:
            db_path = f"{self.vocab_bank_path}/{db_file}"
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT french_word FROM vocabulary WHERE french_word IS NOT NULL")
                rows = cursor.fetchall()
                conn.close()
                
                for (word,) in rows:
                    if word and word.strip():
                        all_words.add(word.strip().lower())
                        
            except Exception as e:
                print(f"Error processing {db_file}: {e}")
        
        return all_words
    
    def migrate_vocabulary_words(self):
        """Migrate all unique words to vocabulary_words table"""
        print("Extracting French words from all databases...")
        french_words = self.extract_all_french_words()
        print(f"Found {len(french_words)} unique French words")
        
        # Prepare batch insert
        batch_size = 1000
        words_to_insert = []
        
        for word in sorted(french_words):
            words_to_insert.append({
                'word': word,
                'language_code': 'fr',
                'normalized_word': self.normalize_word(word),
                'word_length': len(word)
            })
            
            if len(words_to_insert) >= batch_size:
                self.insert_word_batch(words_to_insert)
                words_to_insert = []
        
        # Insert remaining words
        if words_to_insert:
            self.insert_word_batch(words_to_insert)
        
        print("Vocabulary words migration completed")
    
    def insert_word_batch(self, words: list):
        """Insert a batch of words with conflict resolution"""
        try:
            result = self.supabase.table('vocabulary_words').upsert(
                words, 
                on_conflict='word,language_code'
            ).execute()
            print(f"Inserted/updated {len(words)} words")
        except Exception as e:
            print(f"Error inserting batch: {e}")

if __name__ == "__main__":
    migrator = VocabularyMigrator(SUPABASE_URL, SUPABASE_KEY)
    migrator.migrate_vocabulary_words()
```

### Phase 2: Migrate Similarity Relationships
```python
# scripts/migrate_word_similarities.py
import csv
from typing import Dict, List, Tuple
import re

class SimilarityMigrator:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase = create_client(supabase_url, supabase_key)
        self.word_cache: Dict[str, int] = {}
    
    def get_word_id(self, word: str, language_code: str = 'fr') -> int:
        """Get word ID with caching"""
        cache_key = f"{word}_{language_code}"
        if cache_key in self.word_cache:
            return self.word_cache[cache_key]
        
        result = self.supabase.table('vocabulary_words').select('id').eq(
            'word', word
        ).eq('language_code', language_code).execute()
        
        if result.data:
            word_id = result.data[0]['id']
            self.word_cache[cache_key] = word_id
            return word_id
        else:
            raise ValueError(f"Word not found: {word}")
    
    def parse_rule_types(self, rule_types_str: str) -> List[str]:
        """Parse rule types from CSV"""
        if not rule_types_str or rule_types_str.strip() == '':
            return []
        return [rule.strip() for rule in rule_types_str.split(',') if rule.strip()]
    
    def migrate_similarities_from_csv(self, csv_file: str):
        """Migrate similarities from CSV file"""
        print(f"Migrating similarities from {csv_file}")
        
        similarities_to_insert = []
        batch_size = 500
        processed_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    target_word = row['target_word'].strip()
                    similar_words_str = row['similar_words']
                    rule_types_str = row.get('rule_types', '')
                    
                    if not target_word or not similar_words_str:
                        continue
                    
                    # Get target word ID
                    target_id = self.get_word_id(target_word)
                    
                    # Parse similar words
                    similar_words = [w.strip() for w in similar_words_str.split(',') if w.strip()]
                    rule_types = self.parse_rule_types(rule_types_str)
                    
                    # Create similarity relationships
                    for similar_word in similar_words:
                        try:
                            similar_id = self.get_word_id(similar_word)
                            
                            # Create bidirectional relationship
                            similarity_data = {
                                'source_word_id': target_id,
                                'target_word_id': similar_id,
                                'similarity_score': 0.85,  # Default score, can be calculated
                                'rule_types': rule_types,
                                'algorithm_version': 'enhanced_v1'
                            }
                            
                            similarities_to_insert.append(similarity_data)
                            
                            # Also create reverse relationship
                            reverse_similarity_data = {
                                'source_word_id': similar_id,
                                'target_word_id': target_id,
                                'similarity_score': 0.85,
                                'rule_types': rule_types,
                                'algorithm_version': 'enhanced_v1'
                            }
                            similarities_to_insert.append(reverse_similarity_data)
                            
                        except ValueError as e:
                            print(f"Skipping similar word not in vocabulary: {similar_word}")
                            continue
                    
                    processed_count += 1
                    
                    # Batch insert
                    if len(similarities_to_insert) >= batch_size:
                        self.insert_similarity_batch(similarities_to_insert)
                        similarities_to_insert = []
                        
                except Exception as e:
                    print(f"Error processing row {processed_count}: {e}")
                    continue
        
        # Insert remaining similarities
        if similarities_to_insert:
            self.insert_similarity_batch(similarities_to_insert)
        
        print(f"Processed {processed_count} target words")
    
    def insert_similarity_batch(self, similarities: list):
        """Insert batch of similarities with conflict resolution"""
        try:
            result = self.supabase.table('word_similarities').upsert(
                similarities,
                on_conflict='source_word_id,target_word_id,algorithm_version'
            ).execute()
            print(f"Inserted/updated {len(similarities)} similarity relationships")
        except Exception as e:
            print(f"Error inserting similarity batch: {e}")

if __name__ == "__main__":
    migrator = SimilarityMigrator(SUPABASE_URL, SUPABASE_KEY)
    migrator.migrate_similarities_from_csv('consolidated_results/final_enhanced_french_similarities.csv')
```

## API Service Layer

### Core Similarity Service
```typescript
// lib/services/word-similarity-service.ts
import { supabase } from '@/lib/supabase'

export interface SimilarWord {
  wordId: number
  word: string
  translation?: string
  deckId?: number
  similarityScore: number
  ruleTypes: string[]
  userProgress?: string
  deckName?: string
}

export interface SimilarWordWithContext extends SimilarWord {
  userProgress: string
  deckName: string
  isInCurrentDeck: boolean
  lastReviewed?: string
  masteryLevel?: number
}

export class WordSimilarityService {
  private static readonly CACHE_TTL = 5 * 60 * 1000 // 5 minutes
  private static cache = new Map<string, { data: any, timestamp: number }>()

  /**
   * Get similar words for a given word ID
   */
  static async getSimilarWords(wordId: number, limit: number = 5): Promise<SimilarWord[]> {
    const cacheKey = `similar_words_${wordId}_${limit}`
    
    // Check cache first
    const cached = this.getFromCache(cacheKey)
    if (cached) return cached

    try {
      const { data, error } = await supabase
        .from('word_similarities')
        .select(`
          target_word_id,
          similarity_score,
          rule_types,
          vocabulary_words!target_word_id(
            word,
            language_code
          )
        `)
        .eq('source_word_id', wordId)
        .order('similarity_score', { ascending: false })
        .limit(limit)

      if (error) throw error

      const result = data?.map(item => ({
        wordId: item.target_word_id,
        word: item.vocabulary_words.word,
        similarityScore: item.similarity_score,
        ruleTypes: item.rule_types || []
      })) || []

      // Cache the result
      this.setCache(cacheKey, result)
      return result

    } catch (error) {
      console.error('Error fetching similar words:', error)
      return []
    }
  }

  /**
   * Get similar words with full context including deck info and user progress
   */
  static async getSimilarWordsWithContext(
    wordId: number, 
    userId: string,
    currentDeckId?: number,
    limit: number = 5
  ): Promise<SimilarWordWithContext[]> {
    const cacheKey = `similar_words_context_${wordId}_${userId}_${currentDeckId}_${limit}`
    
    // Check cache first
    const cached = this.getFromCache(cacheKey)
    if (cached) return cached

    try {
      const { data, error } = await supabase
        .from('word_similarities')
        .select(`
          target_word_id,
          similarity_score,
          rule_types,
          vocabulary_words!target_word_id(
            word,
            language_code,
            vocabulary!inner(
              id,
              deck_id,
              language_a_word,
              language_b_translation,
              vocabulary_decks!inner(name)
            )
          )
        `)
        .eq('source_word_id', wordId)
        .order('similarity_score', { ascending: false })
        .limit(limit)

      if (error) throw error

      // Get user progress for all similar words
      const similarWordIds = data?.map(item => item.target_word_id) || []
      const userProgress = await this.getUserProgressForWords(userId, similarWordIds)

      const result = await Promise.all(
        data?.map(async (item) => {
          const vocab = item.vocabulary_words.vocabulary
          const progress = userProgress[item.target_word_id] || 'unseen'
          
          return {
            wordId: item.target_word_id,
            word: item.vocabulary_words.word,
            translation: vocab.language_b_translation,
            deckId: vocab.deck_id,
            deckName: vocab.vocabulary_decks.name,
            similarityScore: item.similarity_score,
            ruleTypes: item.rule_types || [],
            userProgress: progress.status || 'unseen',
            isInCurrentDeck: currentDeckId ? vocab.deck_id === currentDeckId : false,
            lastReviewed: progress.last_reviewed,
            masteryLevel: progress.mastery_level || 0
          }
        }) || []
      )

      // Cache the result
      this.setCache(cacheKey, result)
      return result

    } catch (error) {
      console.error('Error fetching similar words with context:', error)
      return []
    }
  }

  /**
   * Get user progress for multiple words
   */
  private static async getUserProgressForWords(
    userId: string, 
    wordIds: number[]
  ): Promise<Record<number, any>> {
    if (wordIds.length === 0) return {}

    try {
      const { data, error } = await supabase
        .from('user_progress')
        .select('word_id, status, last_reviewed, mastery_level')
        .eq('user_id', userId)
        .in('word_id', wordIds)

      if (error) throw error

      const progressMap: Record<number, any> = {}
      data?.forEach(progress => {
        progressMap[progress.word_id] = progress
      })

      return progressMap
    } catch (error) {
      console.error('Error fetching user progress:', error)
      return {}
    }
  }

  /**
   * Record user confusion with similar words
   */
  static async recordSimilarityConfusion(
    userId: string,
    sourceWordId: number,
    targetWordId: number
  ): Promise<void> {
    try {
      // Find the similarity relationship
      const { data: similarity } = await supabase
        .from('word_similarities')
        .select('id')
        .eq('source_word_id', sourceWordId)
        .eq('target_word_id', targetWordId)
        .single()

      if (similarity) {
        // Upsert user similarity progress
        await supabase
          .from('user_similarity_progress')
          .upsert({
            user_id: userId,
            similarity_id: similarity.id,
            confusion_count: 1,
            last_confused_at: new Date().toISOString()
          }, {
            onConflict: 'user_id,similarity_id'
          })
          .select()
      }
    } catch (error) {
      console.error('Error recording similarity confusion:', error)
    }
  }

  /**
   * Get confusion patterns for a user
   */
  static async getUserConfusionPatterns(userId: string): Promise<any[]> {
    try {
      const { data, error } = await supabase
        .from('user_similarity_progress')
        .select(`
          confusion_count,
          last_confused_at,
          word_similarities!inner(
            similarity_score,
            rule_types,
            vocabulary_words!source_word_id(word as source_word),
            vocabulary_words!target_word_id(word as target_word)
          )
        `)
        .eq('user_id', userId)
        .gt('confusion_count', 0)
        .order('confusion_count', { ascending: false })

      if (error) throw error
      return data || []
    } catch (error) {
      console.error('Error fetching confusion patterns:', error)
      return []
    }
  }

  // Cache management methods
  private static getFromCache(key: string): any {
    const cached = this.cache.get(key)
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
      return cached.data
    }
    this.cache.delete(key)
    return null
  }

  private static setCache(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    })
  }

  /**
   * Clear cache (useful for testing or manual cache invalidation)
   */
  static clearCache(): void {
    this.cache.clear()
  }
}
```

## Frontend Components

### Enhanced Similar Words Panel
```tsx
// components/SimilarWordsPanel.tsx
import React, { useState, useEffect } from 'react'
import { WordSimilarityService, SimilarWordWithContext } from '@/lib/services/word-similarity-service'
import { SimilarWordCard } from './SimilarWordCard'
import { SimilarWordSkeleton } from './SimilarWordSkeleton'

interface SimilarWordsPanelProps {
  currentWord: {
    id: number
    word: string
    translation: string
    deckId?: number
  }
  userId: string
  onWordSelect?: (wordId: number, deckId: number) => void
  onConfusionReport?: (sourceWordId: number, targetWordId: number) => void
  className?: string
}

export function SimilarWordsPanel({
  currentWord,
  userId,
  onWordSelect,
  onConfusionReport,
  className = ''
}: SimilarWordsPanelProps) {
  const [similarWords, setSimilarWords] = useState<SimilarWordWithContext[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    loadSimilarWords()
  }, [currentWord.id])

  const loadSimilarWords = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const similar = await WordSimilarityService.getSimilarWordsWithContext(
        currentWord.id,
        userId,
        currentWord.deckId,
        showAll ? 10 : 5
      )
      setSimilarWords(similar)
    } catch (err) {
      setError('Failed to load similar words')
      console.error('Error loading similar words:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleConfusionReport = async (targetWordId: number) => {
    try {
      await WordSimilarityService.recordSimilarityConfusion(
        userId,
        currentWord.id,
        targetWordId
      )
      onConfusionReport?.(currentWord.id, targetWordId)
      
      // Show feedback
      console.log('Confusion reported successfully')
    } catch (error) {
      console.error('Error reporting confusion:', error)
    }
  }

  if (loading) {
    return (
      <div className={`similar-words-panel ${className}`}>
        <h3 className="text-lg font-semibold mb-3 flex items-center">
          <span className="mr-2">🔍</span>
          Similar Words That Might Confuse You
        </h3>
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <SimilarWordSkeleton key={i} />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`similar-words-panel ${className}`}>
        <div className="text-red-600 text-sm p-3 bg-red-50 rounded-lg">
          {error}
        </div>
      </div>
    )
  }

  if (similarWords.length === 0) {
    return (
      <div className={`similar-words-panel ${className}`}>
        <h3 className="text-lg font-semibold mb-3 flex items-center">
          <span className="mr-2">🔍</span>
          Similar Words
        </h3>
        <div className="text-gray-500 text-sm p-3 bg-gray-50 rounded-lg">
          No similar words found for "{currentWord.word}"
        </div>
      </div>
    )
  }

  const displayWords = showAll ? similarWords : similarWords.slice(0, 5)

  return (
    <div className={`similar-words-panel ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold flex items-center">
          <span className="mr-2">🔍</span>
          Similar Words That Might Confuse You
        </h3>
        <span className="text-sm text-gray-500">
          {similarWords.length} found
        </span>
      </div>
      
      <div className="space-y-2">
        {displayWords.map((similar) => (
          <SimilarWordCard
            key={`${similar.wordId}-${similar.deckId}`}
            similar={similar}
            currentWord={currentWord}
            onSelect={onWordSelect}
            onConfusionReport={handleConfusionReport}
          />
        ))}
      </div>

      {similarWords.length > 5 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="mt-3 text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          {showAll ? 'Show Less' : `Show All ${similarWords.length} Similar Words`}
        </button>
      )}
    </div>
  )
}
```

### Enhanced Similar Word Card
```tsx
// components/SimilarWordCard.tsx
import React, { useState } from 'react'
import { SimilarWordWithContext } from '@/lib/services/word-similarity-service'

interface SimilarWordCardProps {
  similar: SimilarWordWithContext
  currentWord: {
    id: number
    word: string
    deckId?: number
  }
  onSelect?: (wordId: number, deckId: number) => void
  onConfusionReport?: (targetWordId: number) => void
}

export function SimilarWordCard({
  similar,
  currentWord,
  onSelect,
  onConfusionReport
}: SimilarWordCardProps) {
  const [showDetails, setShowDetails] = useState(false)
  const [reportingConfusion, setReportingConfusion] = useState(false)

  const getRuleTypeIcon = (ruleTypes: string[]): string => {
    if (ruleTypes.includes('Rule1_Accent')) return '🔤'
    if (ruleTypes.includes('Rule5a_Skeleton')) return '🦴'
    if (ruleTypes.includes('Rule2-4_EditDistance')) return '✏️'
    if (ruleTypes.includes('Rule5b_Structural')) return '🏗️'
    return '🔗'
  }

  const getRuleTypeDescription = (ruleTypes: string[]): string => {
    const descriptions = {
      'Rule1_Accent': 'Different accents',
      'Rule5a_Skeleton': 'Same consonant skeleton',
      'Rule2-4_EditDistance': 'Similar spelling',
      'Rule5b_Structural': 'Structural similarity'
    }
    
    return ruleTypes
      .map(rule => descriptions[rule] || rule)
      .join(', ')
  }

  const getProgressBadge = (progress: string) => {
    const badges = {
      'unseen': { text: 'New', color: 'bg-gray-100 text-gray-800', icon: '🆕' },
      'learning': { text: 'Learning', color: 'bg-yellow-100 text-yellow-800', icon: '📚' },
      'mastered': { text: 'Mastered', color: 'bg-green-100 text-green-800', icon: '✅' },
      'leeches': { text: 'Struggling', color: 'bg-red-100 text-red-800', icon: '⚠️' }
    }
    const badge = badges[progress] || badges['unseen']
    return (
      <span className={`px-2 py-1 text-xs rounded-full flex items-center space-x-1 ${badge.color}`}>
        <span>{badge.icon}</span>
        <span>{badge.text}</span>
      </span>
    )
  }

  const getSimilarityStrength = (score: number): string => {
    if (score >= 0.9) return 'Very High'
    if (score >= 0.8) return 'High'
    if (score >= 0.7) return 'Medium'
    return 'Low'
  }

  const handleConfusionReport = async () => {
    if (reportingConfusion) return
    
    setReportingConfusion(true)
    try {
      await onConfusionReport?.(similar.wordId)
      // Show success feedback
    } catch (error) {
      console.error('Error reporting confusion:', error)
    } finally {
      setReportingConfusion(false)
    }
  }

  return (
    <div className="border rounded-lg p-3 hover:bg-gray-50 transition-colors">
      {/* Main content */}
      <div 
        className="cursor-pointer"
        onClick={() => onSelect?.(similar.wordId, similar.deckId)}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{getRuleTypeIcon(similar.ruleTypes)}</span>
            <span className="font-medium text-blue-600">{similar.word}</span>
            <span className="text-gray-500">→</span>
            <span className="text-gray-700">{similar.translation}</span>
          </div>
          <div className="flex items-center space-x-2">
            {getProgressBadge(similar.userProgress)}
            <span className="text-xs text-gray-500">
              {(similar.similarityScore * 100).toFixed(0)}%
            </span>
          </div>
        </div>
        
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-3">
            <span>Deck: {similar.deckName}</span>
            <span>Strength: {getSimilarityStrength(similar.similarityScore)}</span>
            {similar.isInCurrentDeck && (
              <span className="text-green-600 font-medium">Same Deck</span>
            )}
          </div>
          
          <button
            onClick={(e) => {
              e.stopPropagation()
              setShowDetails(!showDetails)
            }}
            className="text-blue-600 hover:text-blue-800"
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
          </button>
        </div>
      </div>

      {/* Expanded details */}
      {showDetails && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium text-gray-700">Why similar: </span>
              <span className="text-gray-600">{getRuleTypeDescription(similar.ruleTypes)}</span>
            </div>
            
            {similar.lastReviewed && (
              <div>
                <span className="font-medium text-gray-700">Last reviewed: </span>
                <span className="text-gray-600">
                  {new Date(similar.lastReviewed).toLocaleDateString()}
                </span>
              </div>
            )}
            
            {similar.masteryLevel > 0 && (
              <div>
                <span className="font-medium text-gray-700">Mastery level: </span>
                <span className="text-gray-600">{similar.masteryLevel}/5</span>
              </div>
            )}
          </div>
          
          <div className="mt-3 flex space-x-2">
            <button
              onClick={(e) => {
                e.stopPropagation()
                onSelect?.(similar.wordId, similar.deckId)
              }}
              className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
            >
              Study This Word
            </button>
            
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleConfusionReport()
              }}
              disabled={reportingConfusion}
              className="px-3 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors disabled:opacity-50"
            >
              {reportingConfusion ? 'Reporting...' : 'Report Confusion'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
```

## Integration Points

### Study Page Integration
```tsx
// app/study/page.tsx - Enhanced integration
export default function StudyPage() {
  const [showSimilarWords, setShowSimilarWords] = useState(true)
  
  return (
    <div className="study-container grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Main study area */}
      <div className="lg:col-span-3">
        <FlashCard 
          word={currentWord}
          onAnswer={handleAnswer}
          // ... existing props
        />
      </div>
      
      {/* Similar words sidebar */}
      <div className="lg:col-span-1">
        {showSimilarWords && (
          <SimilarWordsPanel 
            currentWord={currentWord}
            userId={user.id}
            onWordSelect={(wordId, deckId) => {
              // Navigate to similar word's context
              router.push(`/study?deck=${deckId}&word=${wordId}`)
            }}
            onConfusionReport={(sourceId, targetId) => {
              // Show feedback that confusion was recorded
              toast.success('Confusion pattern recorded')
            }}
          />
        )}
        
        <button
          onClick={() => setShowSimilarWords(!showSimilarWords)}
          className="mt-4 w-full text-sm text-gray-600 hover:text-gray-800"
        >
          {showSimilarWords ? 'Hide Similar Words' : 'Show Similar Words'}
        </button>
      </div>
    </div>
  )
}
```

## Performance Optimizations

### Database Indexing Strategy
```sql
-- Additional performance indexes
CREATE INDEX CONCURRENTLY idx_word_similarities_composite 
ON word_similarities(source_word_id, similarity_score DESC, algorithm_version);

-- Partial indexes for active algorithms
CREATE INDEX CONCURRENTLY idx_word_similarities_active_algorithm 
ON word_similarities(source_word_id, similarity_score DESC) 
WHERE algorithm_version = 'enhanced_v1';

-- Covering index for common queries
CREATE INDEX CONCURRENTLY idx_word_similarities_covering 
ON word_similarities(source_word_id) 
INCLUDE (target_word_id, similarity_score, rule_types);
```

### Caching Strategy
```typescript
// lib/cache/similarity-cache.ts
import { Redis } from 'ioredis'

export class SimilarityCache {
  private redis: Redis
  private readonly TTL = 3600 // 1 hour

  constructor() {
    this.redis = new Redis(process.env.REDIS_URL!)
  }

  async getSimilarWords(wordId: number): Promise<SimilarWord[] | null> {
    const key = `similar_words:${wordId}`
    const cached = await this.redis.get(key)
    return cached ? JSON.parse(cached) : null
  }

  async setSimilarWords(wordId: number, similarWords: SimilarWord[]): Promise<void> {
    const key = `similar_words:${wordId}`
    await this.redis.setex(key, this.TTL, JSON.stringify(similarWords))
  }

  async invalidateWord(wordId: number): Promise<void> {
    const key = `similar_words:${wordId}`
    await this.redis.del(key)
  }
}
```

This detailed design provides a robust, scalable foundation for integrating word similarity into your vocabulary learning system. The architecture supports future algorithm updates, cross-deck similarities, and provides rich user experiences while maintaining excellent performance.
