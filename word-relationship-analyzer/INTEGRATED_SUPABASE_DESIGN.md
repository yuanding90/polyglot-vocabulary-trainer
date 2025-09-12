# Integrated Word Similarity System - Building on Existing Supabase Schema

## Current Database Schema Analysis

Based on the existing multi-language vocabulary trainer, here are the current tables:

### Existing Tables
1. **`vocabulary`** - Core vocabulary words with language-agnostic structure
2. **`vocabulary_decks`** - Deck metadata with language pair information  
3. **`deck_vocabulary`** - Relationship between decks and vocabulary
4. **`user_progress`** - Individual user learning progress
5. **`study_sessions`** - Session tracking and analytics
6. **`rating_history`** - SRS algorithm data
7. **`daily_summary`** - Daily activity summaries

## Integrated Design: Add Similarity Tables to Existing Schema

### Step 1: Add Word Similarity Tables (Minimal Addition)

```sql
-- Add word similarity tables to existing schema
-- Run this in Supabase SQL Editor

-- Table to store word similarity relationships
CREATE TABLE word_similarities (
    id SERIAL PRIMARY KEY,
    source_word_id INTEGER NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
    target_word_id INTEGER NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
    similarity_score DECIMAL(5,4) NOT NULL CHECK (similarity_score >= 0 AND similarity_score <= 1),
    rule_types TEXT[] NOT NULL,
    algorithm_version VARCHAR(20) NOT NULL DEFAULT 'enhanced_v1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT no_self_similarity CHECK (source_word_id != target_word_id),
    CONSTRAINT unique_similarity_per_algorithm UNIQUE (source_word_id, target_word_id, algorithm_version)
);

-- Indexes for performance
CREATE INDEX idx_word_similarities_source ON word_similarities(source_word_id);
CREATE INDEX idx_word_similarities_target ON word_similarities(target_word_id);
CREATE INDEX idx_word_similarities_score ON word_similarities(similarity_score DESC);
CREATE INDEX idx_word_similarities_lookup ON word_similarities(source_word_id, similarity_score DESC);

-- Enable RLS
ALTER TABLE word_similarities ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (similarity data is reference data)
CREATE POLICY "Anyone can read word similarities" ON word_similarities FOR SELECT USING (true);
```

### Step 2: Data Migration Script (Works with Existing Tables)

```python
# scripts/migrate_word_similarities_integrated.py
import csv
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def get_vocabulary_word_id(supabase, word: str) -> int:
    """Get vocabulary ID by matching language_a_word"""
    result = supabase.table('vocabulary').select('id').eq(
        'language_a_word', word.lower()
    ).execute()
    
    if result.data:
        return result.data[0]['id']
    else:
        raise ValueError(f"Word not found in vocabulary: {word}")

def parse_rule_types(rule_types_str: str) -> list:
    """Parse rule types from CSV"""
    if not rule_types_str or rule_types_str.strip() == '':
        return []
    return [rule.strip() for rule in rule_types_str.split(',') if rule.strip()]

def migrate_similarities_to_existing_schema():
    """Migrate word similarities to existing vocabulary table"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    csv_file = "../../consolidated_results/final_enhanced_french_similarities.csv"
    
    similarities_to_insert = []
    batch_size = 500
    processed_count = 0
    skipped_count = 0
    
    print("Reading similarities from CSV and mapping to existing vocabulary...")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                target_word = row['target_word'].strip().lower()
                similar_words_str = row['similar_words']
                rule_types_str = row.get('rule_types', '')
                
                if not target_word or not similar_words_str:
                    continue
                
                # Get target word ID from existing vocabulary table
                try:
                    target_id = get_vocabulary_word_id(supabase, target_word)
                except ValueError:
                    print(f"Skipping target word not in vocabulary: {target_word}")
                    skipped_count += 1
                    continue
                
                rule_types = parse_rule_types(rule_types_str)
                
                # Parse similar words
                similar_words = [w.strip().lower() for w in similar_words_str.split(',') if w.strip()]
                
                # Create similarity relationships
                for similar_word in similar_words:
                    try:
                        similar_id = get_vocabulary_word_id(supabase, similar_word)
                        
                        # Create bidirectional relationship
                        similarity_data = {
                            'source_word_id': target_id,
                            'target_word_id': similar_id,
                            'similarity_score': 0.85,  # Default score
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
                        
                    except ValueError:
                        print(f"Skipping similar word not in vocabulary: {similar_word}")
                        skipped_count += 1
                        continue
                
                processed_count += 1
                
                # Batch insert
                if len(similarities_to_insert) >= batch_size:
                    try:
                        result = supabase.table('word_similarities').upsert(
                            similarities_to_insert,
                            on_conflict='source_word_id,target_word_id,algorithm_version'
                        ).execute()
                        print(f"Inserted batch: {len(similarities_to_insert)} relationships")
                        similarities_to_insert = []
                    except Exception as e:
                        print(f"Error inserting batch: {e}")
                        similarities_to_insert = []
                        
            except Exception as e:
                print(f"Error processing row {processed_count}: {e}")
                continue
    
    # Insert remaining similarities
    if similarities_to_insert:
        try:
            result = supabase.table('word_similarities').upsert(
                similarities_to_insert,
                on_conflict='source_word_id,target_word_id,algorithm_version'
            ).execute()
            print(f"Final batch: {len(similarities_to_insert)} relationships")
        except Exception as e:
            print(f"Error inserting final batch: {e}")
    
    print(f"Migration completed!")
    print(f"  - Processed {processed_count} target words")
    print(f"  - Skipped {skipped_count} words not in vocabulary")
    print(f"  - Total relationships: {len(similarities_to_insert)}")

if __name__ == "__main__":
    migrate_similarities_to_existing_schema()
```

### Step 3: Integrated TypeScript Service

```typescript
// lib/services/word-similarity-service.ts
import { supabase } from '@/lib/supabase'
import { Vocabulary, VocabularyDeck, UserProgress } from '@/lib/supabase'

export interface SimilarWord {
  wordId: number
  word: string
  translation: string
  similarityScore: number
  ruleTypes: string[]
  deckId?: string
  deckName?: string
  userProgress?: UserProgress
}

export class WordSimilarityService {
  /**
   * Get similar words for a vocabulary ID with full context
   */
  static async getSimilarWordsWithContext(
    vocabularyId: number, 
    userId?: string,
    limit: number = 5
  ): Promise<SimilarWord[]> {
    try {
      const { data, error } = await supabase
        .from('word_similarities')
        .select(`
          target_word_id,
          similarity_score,
          rule_types,
          vocabulary!target_word_id(
            id,
            language_a_word,
            language_b_translation,
            deck_vocabulary(
              deck_id,
              vocabulary_decks(name)
            )
          )
        `)
        .eq('source_word_id', vocabularyId)
        .order('similarity_score', { ascending: false })
        .limit(limit)

      if (error) throw error

      // Get user progress if userId provided
      let userProgressMap: Record<number, UserProgress> = {}
      if (userId) {
        const targetWordIds = data?.map(item => item.target_word_id) || []
        const { data: progressData } = await supabase
          .from('user_progress')
          .select('*')
          .eq('user_id', userId)
          .in('word_id', targetWordIds)
        
        if (progressData) {
          progressData.forEach(progress => {
            userProgressMap[progress.word_id] = progress
          })
        }
      }

      return data?.map(item => {
        const vocab = item.vocabulary
        const deckRel = vocab.deck_vocabulary?.[0] // Get first deck relationship
        const deck = deckRel?.vocabulary_decks
        
        return {
          wordId: vocab.id,
          word: vocab.language_a_word,
          translation: vocab.language_b_translation,
          similarityScore: item.similarity_score,
          ruleTypes: item.rule_types || [],
          deckId: deck?.id,
          deckName: deck?.name,
          userProgress: userProgressMap[vocab.id]
        }
      }) || []

    } catch (error) {
      console.error('Error fetching similar words with context:', error)
      return []
    }
  }

  /**
   * Get similar words across all decks for a vocabulary ID
   */
  static async getSimilarWordsAcrossDecks(
    vocabularyId: number, 
    limit: number = 5
  ): Promise<SimilarWord[]> {
    try {
      const { data, error } = await supabase
        .from('word_similarities')
        .select(`
          target_word_id,
          similarity_score,
          rule_types,
          vocabulary!target_word_id(
            id,
            language_a_word,
            language_b_translation
          )
        `)
        .eq('source_word_id', vocabularyId)
        .order('similarity_score', { ascending: false })
        .limit(limit)

      if (error) throw error

      return data?.map(item => {
        const vocab = item.vocabulary
        return {
          wordId: vocab.id,
          word: vocab.language_a_word,
          translation: vocab.language_b_translation,
          similarityScore: item.similarity_score,
          ruleTypes: item.rule_types || []
        }
      }) || []

    } catch (error) {
      console.error('Error fetching similar words:', error)
      return []
    }
  }

  /**
   * Get similar words within a specific deck
   */
  static async getSimilarWordsInDeck(
    vocabularyId: number,
    deckId: string,
    userId?: string,
    limit: number = 5
  ): Promise<SimilarWord[]> {
    try {
      // First get all similar words
      const allSimilar = await this.getSimilarWordsWithContext(vocabularyId, userId, limit * 2)
      
      // Filter to only words in the specified deck
      const similarInDeck = allSimilar.filter(similar => similar.deckId === deckId)
      
      return similarInDeck.slice(0, limit)
    } catch (error) {
      console.error('Error fetching similar words in deck:', error)
      return []
    }
  }
}
```

### Step 4: Enhanced Frontend Components

```tsx
// components/SimilarWordsPanel.tsx
import React, { useState, useEffect } from 'react'
import { WordSimilarityService, SimilarWord } from '@/lib/services/word-similarity-service'
import { Vocabulary, VocabularyDeck, UserProgress } from '@/lib/supabase'

interface SimilarWordsPanelProps {
  currentWord: Vocabulary
  currentDeck?: VocabularyDeck
  userId?: string
  onWordSelect?: (wordId: number, deckId?: string) => void
  className?: string
}

export function SimilarWordsPanel({
  currentWord,
  currentDeck,
  userId,
  onWordSelect,
  className = ''
}: SimilarWordsPanelProps) {
  const [similarWords, setSimilarWords] = useState<SimilarWord[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCrossDeck, setShowCrossDeck] = useState(false)

  useEffect(() => {
    loadSimilarWords()
  }, [currentWord.id, showCrossDeck])

  const loadSimilarWords = async () => {
    setLoading(true)
    setError(null)
    
    try {
      let similar: SimilarWord[]
      
      if (showCrossDeck) {
        // Show similar words across all decks
        similar = await WordSimilarityService.getSimilarWordsAcrossDecks(
          currentWord.id,
          5
        )
      } else if (currentDeck) {
        // Show similar words only in current deck
        similar = await WordSimilarityService.getSimilarWordsInDeck(
          currentWord.id,
          currentDeck.id,
          userId,
          5
        )
      } else {
        // Show similar words with full context
        similar = await WordSimilarityService.getSimilarWordsWithContext(
          currentWord.id,
          userId,
          5
        )
      }
      
      setSimilarWords(similar)
    } catch (err) {
      setError('Failed to load similar words')
      console.error('Error loading similar words:', err)
    } finally {
      setLoading(false)
    }
  }

  const getProgressStatus = (progress?: UserProgress): string => {
    if (!progress) return 'unseen'
    
    // Use existing SRS logic to determine status
    if (progress.again_count >= 4) return 'leeches'
    if (progress.interval < 7) return 'learning'
    if (progress.interval < 21) return 'strengthening'
    if (progress.interval < 60) return 'consolidating'
    return 'mastered'
  }

  if (loading) {
    return (
      <div className={`similar-words-panel ${className}`}>
        <h3 className="text-lg font-semibold mb-3">🔍 Similar Words</h3>
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 animate-pulse rounded"></div>
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
        <h3 className="text-lg font-semibold mb-3">🔍 Similar Words</h3>
        <div className="text-gray-500 text-sm p-3 bg-gray-50 rounded-lg">
          No similar words found for "{currentWord.language_a_word}"
        </div>
      </div>
    )
  }

  return (
    <div className={`similar-words-panel ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold">
          🔍 Similar Words ({similarWords.length})
        </h3>
        <button
          onClick={() => setShowCrossDeck(!showCrossDeck)}
          className="text-xs text-blue-600 hover:text-blue-800"
        >
          {showCrossDeck ? 'This Deck Only' : 'All Decks'}
        </button>
      </div>
      
      <div className="space-y-2">
        {similarWords.map((similar) => (
          <SimilarWordCard
            key={`${similar.wordId}-${similar.deckId}`}
            similar={similar}
            currentWord={currentWord}
            currentDeck={currentDeck}
            progressStatus={getProgressStatus(similar.userProgress)}
            onSelect={onWordSelect}
          />
        ))}
      </div>
    </div>
  )
}
```

### Step 5: Integration with Existing Study Page

```tsx
// app/study/page.tsx - Add similar words to existing study interface
export default function StudyPage() {
  // ... existing code ...

  return (
    <div className="study-container grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Main study area - existing flashcard */}
      <div className="lg:col-span-3">
        <FlashCard 
          word={currentWord}
          onAnswer={handleAnswer}
          // ... existing props
        />
      </div>
      
      {/* New similar words sidebar */}
      <div className="lg:col-span-1">
        <SimilarWordsPanel 
          currentWord={currentWord}
          currentDeck={currentDeck}
          userId={user?.id}
          onWordSelect={(wordId, deckId) => {
            if (deckId && deckId !== currentDeck?.id) {
              // Navigate to similar word in different deck
              router.push(`/study?deck=${deckId}&word=${wordId}`)
            } else {
              // Show similar word in current deck context
              console.log('Selected similar word:', wordId)
            }
          }}
        />
      </div>
    </div>
  )
}
```

## Key Advantages of This Integrated Approach

### ✅ **Builds on Existing Schema**
- Uses existing `vocabulary` table with IDs
- Integrates with existing `vocabulary_decks` and `deck_vocabulary` relationships
- Leverages existing `user_progress` for user context

### ✅ **Minimal Database Changes**
- Only adds one new table: `word_similarities`
- No changes to existing tables
- Maintains all existing functionality

### ✅ **Cross-Deck Support**
- Similar words can exist across different decks
- Users can navigate between decks to study similar words
- Maintains deck context and user progress

### ✅ **Existing Data Integration**
- Works with all existing vocabulary data
- Uses existing user progress tracking
- Integrates with existing study sessions

### ✅ **Future-Proof**
- Algorithm versioning for future similarity algorithms
- Easy to update similarity data without affecting existing tables
- Maintains backward compatibility

This integrated approach leverages your existing Supabase schema while adding powerful word similarity functionality that enhances the learning experience across all decks!
