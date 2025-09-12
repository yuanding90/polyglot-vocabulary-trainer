# Supabase Implementation Guide - Word Similarity Service

## Simplified Architecture (Without User Tracking)

### Core Components
1. **Database Schema**: Two main tables for words and similarities
2. **Data Migration**: Import CSV similarity data into Supabase
3. **API Service**: TypeScript service for fetching similar words
4. **Frontend Components**: Simple display components

## Step-by-Step Implementation

### Step 1: Create Database Schema in Supabase

#### 1.1 Create vocabulary_words table
```sql
-- Run this in Supabase SQL Editor
CREATE TABLE vocabulary_words (
    id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    language_code VARCHAR(5) NOT NULL DEFAULT 'fr',
    normalized_word TEXT NOT NULL,
    word_length INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_word_per_language UNIQUE (word, language_code),
    CONSTRAINT valid_language_code CHECK (language_code ~ '^[a-z]{2}$')
);

-- Create indexes for performance
CREATE INDEX idx_vocabulary_words_word ON vocabulary_words(word);
CREATE INDEX idx_vocabulary_words_normalized ON vocabulary_words(normalized_word);
CREATE INDEX idx_vocabulary_words_language ON vocabulary_words(language_code);
```

#### 1.2 Create word_similarities table
```sql
-- Run this in Supabase SQL Editor
CREATE TABLE word_similarities (
    id SERIAL PRIMARY KEY,
    source_word_id INTEGER NOT NULL REFERENCES vocabulary_words(id) ON DELETE CASCADE,
    target_word_id INTEGER NOT NULL REFERENCES vocabulary_words(id) ON DELETE CASCADE,
    similarity_score DECIMAL(5,4) NOT NULL CHECK (similarity_score >= 0 AND similarity_score <= 1),
    rule_types TEXT[] NOT NULL,
    algorithm_version VARCHAR(20) NOT NULL DEFAULT 'enhanced_v1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT no_self_similarity CHECK (source_word_id != target_word_id),
    CONSTRAINT unique_similarity_per_algorithm UNIQUE (source_word_id, target_word_id, algorithm_version)
);

-- Create indexes for efficient lookups
CREATE INDEX idx_word_similarities_source ON word_similarities(source_word_id);
CREATE INDEX idx_word_similarities_target ON word_similarities(target_word_id);
CREATE INDEX idx_word_similarities_score ON word_similarities(similarity_score DESC);
CREATE INDEX idx_word_similarities_lookup ON word_similarities(source_word_id, similarity_score DESC);
```

#### 1.3 Enable Row Level Security (RLS)
```sql
-- Enable RLS on both tables
ALTER TABLE vocabulary_words ENABLE ROW LEVEL SECURITY;
ALTER TABLE word_similarities ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (since this is reference data)
CREATE POLICY "Anyone can read vocabulary words" ON vocabulary_words FOR SELECT USING (true);
CREATE POLICY "Anyone can read word similarities" ON word_similarities FOR SELECT USING (true);

-- Optional: Restrict writes to authenticated users only
CREATE POLICY "Authenticated users can insert vocabulary words" ON vocabulary_words FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Authenticated users can insert word similarities" ON word_similarities FOR INSERT WITH CHECK (auth.role() = 'authenticated');
```

### Step 2: Create Data Migration Scripts

#### 2.1 Create migration script directory
```bash
mkdir -p scripts/migration
cd scripts/migration
```

#### 2.2 Create vocabulary migration script
```python
# scripts/migration/migrate_vocabulary.py
import sqlite3
import os
from supabase import create_client
import unicodedata
from typing import Set

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def normalize_word(word: str) -> str:
    """Normalize word for accent-insensitive lookups"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', word.lower())
        if unicodedata.category(c) != 'Mn'
    )

def extract_french_words_from_csv(csv_file: str) -> Set[str]:
    """Extract all unique French words from the similarity CSV"""
    words = set()
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        import csv
        reader = csv.DictReader(f)
        
        for row in reader:
            target_word = row['target_word'].strip()
            if target_word:
                words.add(target_word.lower())
            
            similar_words_str = row['similar_words']
            if similar_words_str:
                similar_words = [w.strip().lower() for w in similar_words_str.split(',') if w.strip()]
                words.update(similar_words)
    
    return words

def migrate_vocabulary_words():
    """Migrate vocabulary words to Supabase"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Extract words from CSV
    csv_file = "../../consolidated_results/final_enhanced_french_similarities.csv"
    if not os.path.exists(csv_file):
        print(f"CSV file not found: {csv_file}")
        return
    
    print("Extracting words from CSV...")
    french_words = extract_french_words_from_csv(csv_file)
    print(f"Found {len(french_words)} unique French words")
    
    # Prepare data for insertion
    words_data = []
    for word in sorted(french_words):
        words_data.append({
            'word': word,
            'language_code': 'fr',
            'normalized_word': normalize_word(word),
            'word_length': len(word)
        })
    
    # Insert in batches
    batch_size = 1000
    for i in range(0, len(words_data), batch_size):
        batch = words_data[i:i + batch_size]
        try:
            result = supabase.table('vocabulary_words').upsert(
                batch, 
                on_conflict='word,language_code'
            ).execute()
            print(f"Inserted/updated batch {i//batch_size + 1}: {len(batch)} words")
        except Exception as e:
            print(f"Error inserting batch: {e}")
    
    print("Vocabulary migration completed!")

if __name__ == "__main__":
    migrate_vocabulary_words()
```

#### 2.3 Create similarities migration script
```python
# scripts/migration/migrate_similarities.py
import csv
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def get_word_id(supabase, word: str, language_code: str = 'fr') -> int:
    """Get word ID from vocabulary_words table"""
    result = supabase.table('vocabulary_words').select('id').eq(
        'word', word
    ).eq('language_code', language_code).execute()
    
    if result.data:
        return result.data[0]['id']
    else:
        raise ValueError(f"Word not found: {word}")

def parse_rule_types(rule_types_str: str) -> list:
    """Parse rule types from CSV"""
    if not rule_types_str or rule_types_str.strip() == '':
        return []
    return [rule.strip() for rule in rule_types_str.split(',') if rule.strip()]

def migrate_similarities():
    """Migrate word similarities to Supabase"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    csv_file = "../../consolidated_results/final_enhanced_french_similarities.csv"
    
    similarities_to_insert = []
    batch_size = 500
    processed_count = 0
    
    print("Reading similarities from CSV...")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                target_word = row['target_word'].strip().lower()
                similar_words_str = row['similar_words']
                rule_types_str = row.get('rule_types', '')
                
                if not target_word or not similar_words_str:
                    continue
                
                # Get target word ID
                target_id = get_word_id(supabase, target_word)
                rule_types = parse_rule_types(rule_types_str)
                
                # Parse similar words
                similar_words = [w.strip().lower() for w in similar_words_str.split(',') if w.strip()]
                
                # Create similarity relationships
                for similar_word in similar_words:
                    try:
                        similar_id = get_word_id(supabase, similar_word)
                        
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
                        
                    except ValueError as e:
                        print(f"Skipping similar word not in vocabulary: {similar_word}")
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
    
    print(f"Similarities migration completed! Processed {processed_count} target words")

if __name__ == "__main__":
    migrate_similarities()
```

### Step 3: Run Migration Scripts

#### 3.1 Install required Python packages
```bash
pip install supabase unicodedata
```

#### 3.2 Run vocabulary migration
```bash
cd scripts/migration
python migrate_vocabulary.py
```

#### 3.3 Run similarities migration
```bash
python migrate_similarities.py
```

### Step 4: Create TypeScript Service

#### 4.1 Create similarity service
```typescript
// lib/services/word-similarity-service.ts
import { supabase } from '@/lib/supabase'

export interface SimilarWord {
  wordId: number
  word: string
  similarityScore: number
  ruleTypes: string[]
}

export interface SimilarWordWithTranslation extends SimilarWord {
  translation: string
  deckId?: number
  deckName?: string
}

export class WordSimilarityService {
  /**
   * Get similar words for a given word ID
   */
  static async getSimilarWords(wordId: number, limit: number = 5): Promise<SimilarWord[]> {
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

      return data?.map(item => ({
        wordId: item.target_word_id,
        word: item.vocabulary_words.word,
        similarityScore: item.similarity_score,
        ruleTypes: item.rule_types || []
      })) || []

    } catch (error) {
      console.error('Error fetching similar words:', error)
      return []
    }
  }

  /**
   * Get similar words with translation and deck context
   */
  static async getSimilarWordsWithContext(
    wordId: number, 
    limit: number = 5
  ): Promise<SimilarWordWithTranslation[]> {
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

      return data?.map(item => {
        const vocab = item.vocabulary_words.vocabulary
        return {
          wordId: item.target_word_id,
          word: item.vocabulary_words.word,
          translation: vocab.language_b_translation,
          deckId: vocab.deck_id,
          deckName: vocab.vocabulary_decks.name,
          similarityScore: item.similarity_score,
          ruleTypes: item.rule_types || []
        }
      }) || []

    } catch (error) {
      console.error('Error fetching similar words with context:', error)
      return []
    }
  }

  /**
   * Get word ID by word string
   */
  static async getWordId(word: string, languageCode: string = 'fr'): Promise<number | null> {
    try {
      const { data, error } = await supabase
        .from('vocabulary_words')
        .select('id')
        .eq('word', word.toLowerCase())
        .eq('language_code', languageCode)
        .single()

      if (error) throw error
      return data?.id || null

    } catch (error) {
      console.error('Error fetching word ID:', error)
      return null
    }
  }
}
```

### Step 5: Create Frontend Components

#### 5.1 Create Similar Words Panel
```tsx
// components/SimilarWordsPanel.tsx
import React, { useState, useEffect } from 'react'
import { WordSimilarityService, SimilarWordWithTranslation } from '@/lib/services/word-similarity-service'

interface SimilarWordsPanelProps {
  currentWord: {
    id: number
    word: string
    translation: string
  }
  onWordSelect?: (wordId: number, deckId?: number) => void
  className?: string
}

export function SimilarWordsPanel({
  currentWord,
  onWordSelect,
  className = ''
}: SimilarWordsPanelProps) {
  const [similarWords, setSimilarWords] = useState<SimilarWordWithTranslation[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadSimilarWords()
  }, [currentWord.id])

  const loadSimilarWords = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const similar = await WordSimilarityService.getSimilarWordsWithContext(
        currentWord.id,
        5
      )
      setSimilarWords(similar)
    } catch (err) {
      setError('Failed to load similar words')
      console.error('Error loading similar words:', err)
    } finally {
      setLoading(false)
    }
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
          No similar words found for "{currentWord.word}"
        </div>
      </div>
    )
  }

  return (
    <div className={`similar-words-panel ${className}`}>
      <h3 className="text-lg font-semibold mb-3">
        🔍 Similar Words ({similarWords.length})
      </h3>
      
      <div className="space-y-2">
        {similarWords.map((similar) => (
          <SimilarWordCard
            key={`${similar.wordId}-${similar.deckId}`}
            similar={similar}
            currentWord={currentWord}
            onSelect={onWordSelect}
          />
        ))}
      </div>
    </div>
  )
}
```

#### 5.2 Create Similar Word Card
```tsx
// components/SimilarWordCard.tsx
import React from 'react'
import { SimilarWordWithTranslation } from '@/lib/services/word-similarity-service'

interface SimilarWordCardProps {
  similar: SimilarWordWithTranslation
  currentWord: {
    id: number
    word: string
  }
  onSelect?: (wordId: number, deckId?: number) => void
}

export function SimilarWordCard({
  similar,
  currentWord,
  onSelect
}: SimilarWordCardProps) {
  const getRuleTypeIcon = (ruleTypes: string[]): string => {
    if (ruleTypes.includes('Rule1_Accent')) return '🔤'
    if (ruleTypes.includes('Rule5a_Skeleton')) return '🦴'
    if (ruleTypes.includes('Rule2-4_EditDistance')) return '✏️'
    if (ruleTypes.includes('Rule5b_Structural')) return '🏗️'
    return '🔗'
  }

  const getSimilarityStrength = (score: number): string => {
    if (score >= 0.9) return 'Very High'
    if (score >= 0.8) return 'High'
    if (score >= 0.7) return 'Medium'
    return 'Low'
  }

  return (
    <div 
      className="border rounded-lg p-3 hover:bg-gray-50 cursor-pointer transition-colors"
      onClick={() => onSelect?.(similar.wordId, similar.deckId)}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getRuleTypeIcon(similar.ruleTypes)}</span>
          <span className="font-medium text-blue-600">{similar.word}</span>
          <span className="text-gray-500">→</span>
          <span className="text-gray-700">{similar.translation}</span>
        </div>
        <div className="text-xs text-gray-500">
          {(similar.similarityScore * 100).toFixed(0)}%
        </div>
      </div>
      
      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-3">
          {similar.deckName && <span>Deck: {similar.deckName}</span>}
          <span>Strength: {getSimilarityStrength(similar.similarityScore)}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          {similar.ruleTypes.map((rule, index) => (
            <span key={index} className="px-1 py-0.5 bg-gray-100 rounded text-xs">
              {rule.replace('Rule', '').replace('_', ' ')}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
```

### Step 6: Integrate into Study Page

#### 6.1 Update study page
```tsx
// app/study/page.tsx - Add similar words sidebar
export default function StudyPage() {
  // ... existing code ...

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
        <SimilarWordsPanel 
          currentWord={currentWord}
          onWordSelect={(wordId, deckId) => {
            // Navigate to similar word's context
            if (deckId) {
              router.push(`/study?deck=${deckId}&word=${wordId}`)
            } else {
              console.log('Selected similar word:', wordId)
            }
          }}
        />
      </div>
    </div>
  )
}
```

### Step 7: Test the Implementation

#### 7.1 Verify database data
```sql
-- Check vocabulary words count
SELECT COUNT(*) FROM vocabulary_words;

-- Check similarities count
SELECT COUNT(*) FROM word_similarities;

-- Test a query
SELECT 
  vw1.word as source_word,
  vw2.word as target_word,
  ws.similarity_score,
  ws.rule_types
FROM word_similarities ws
JOIN vocabulary_words vw1 ON ws.source_word_id = vw1.id
JOIN vocabulary_words vw2 ON ws.target_word_id = vw2.id
WHERE vw1.word = 'abandon'
LIMIT 5;
```

#### 7.2 Test API service
```typescript
// Test the service in browser console
import { WordSimilarityService } from '@/lib/services/word-similarity-service'

// Test getting word ID
const wordId = await WordSimilarityService.getWordId('abandon')
console.log('Word ID:', wordId)

// Test getting similar words
const similar = await WordSimilarityService.getSimilarWords(wordId)
console.log('Similar words:', similar)
```

## Summary

This implementation provides:

1. **✅ Clean Database Schema**: Two tables with proper relationships and indexes
2. **✅ Data Migration**: Scripts to import CSV data into Supabase
3. **✅ API Service**: TypeScript service for fetching similar words
4. **✅ Frontend Components**: Simple, clean UI components
5. **✅ Integration**: Easy integration into existing study page

The system is now ready to display similar words during study sessions, helping users identify potentially confusing word pairs across all decks.
