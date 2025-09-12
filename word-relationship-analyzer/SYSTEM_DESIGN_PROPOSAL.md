# Word Similarity Learning System - Design Proposal

## Overview
Design a comprehensive system that integrates word similarity mappings into the vocabulary learning app to help users identify and learn confusing word pairs across all decks.

## Problem Analysis

### Current Challenges
1. **ID-less Mapping**: Current CSV uses string matching, creating potential edge cases
2. **Cross-Deck Similarities**: Similar words may exist in different decks
3. **Scalability**: Need to support future algorithm updates without impacting existing data
4. **Performance**: Efficient lookup for real-time learning assistance
5. **User Experience**: Seamless integration into existing discovery/review modes

## Approach 1: Centralized Similarity Service (Recommended)

### Backend Architecture

#### Database Schema
```sql
-- Core vocabulary reference (if not exists)
CREATE TABLE vocabulary_words (
    id SERIAL PRIMARY KEY,
    word TEXT UNIQUE NOT NULL,
    language_code VARCHAR(5) NOT NULL, -- 'fr', 'en', etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- Word similarity relationships
CREATE TABLE word_similarities (
    id SERIAL PRIMARY KEY,
    source_word_id INTEGER REFERENCES vocabulary_words(id) ON DELETE CASCADE,
    target_word_id INTEGER REFERENCES vocabulary_words(id) ON DELETE CASCADE,
    similarity_score DECIMAL(5,4), -- 0.0000 to 1.0000
    rule_types TEXT[], -- ['Rule1_Accent', 'Rule5a_Skeleton', etc.]
    algorithm_version VARCHAR(20) DEFAULT 'enhanced_v1',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_word_id, target_word_id, algorithm_version)
);

-- Indexes for performance
CREATE INDEX idx_word_similarities_source ON word_similarities(source_word_id);
CREATE INDEX idx_word_similarities_target ON word_similarities(target_word_id);
CREATE INDEX idx_vocabulary_words_word ON vocabulary_words(word);
CREATE INDEX idx_vocabulary_words_language ON vocabulary_words(language_code);
```

#### Data Migration Script
```python
# migrate_word_similarities.py
import csv
import sqlite3
from supabase import create_client

def migrate_similarities():
    # 1. Extract unique words from CSV and insert into vocabulary_words
    # 2. Create bidirectional relationships in word_similarities
    # 3. Handle cross-deck scenarios
    
    supabase = create_client(url, key)
    
    # Read CSV and process
    with open('final_enhanced_french_similarities.csv', 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            target_word = row['target_word']
            similar_words = row['similar_words'].split(', ')
            
            # Insert target word if not exists
            target_id = get_or_create_word_id(supabase, target_word, 'fr')
            
            # Insert similarity relationships
            for similar_word in similar_words:
                if similar_word:  # Skip empty strings
                    similar_id = get_or_create_word_id(supabase, similar_word, 'fr')
                    
                    # Insert bidirectional relationship
                    supabase.table('word_similarities').insert({
                        'source_word_id': target_id,
                        'target_word_id': similar_id,
                        'similarity_score': 0.85,  # Default score
                        'rule_types': row['rule_types'].split(', ') if row['rule_types'] else []
                    }).execute()
```

#### API Endpoints
```typescript
// lib/word-similarity-service.ts
export class WordSimilarityService {
  // Get similar words for a given word
  static async getSimilarWords(wordId: number): Promise<SimilarWord[]> {
    const { data, error } = await supabase
      .from('word_similarities')
      .select(`
        target_word_id,
        similarity_score,
        rule_types,
        vocabulary_words!target_word_id(word, language_code)
      `)
      .eq('source_word_id', wordId)
      .order('similarity_score', { ascending: false })
      .limit(5);
    
    return data?.map(item => ({
      wordId: item.target_word_id,
      word: item.vocabulary_words.word,
      score: item.similarity_score,
      ruleTypes: item.rule_types
    })) || [];
  }

  // Get similar words with deck context
  static async getSimilarWordsWithContext(
    wordId: number, 
    userId: string
  ): Promise<SimilarWordWithContext[]> {
    const { data, error } = await supabase
      .from('word_similarities')
      .select(`
        target_word_id,
        similarity_score,
        rule_types,
        vocabulary_words!target_word_id(
          word, 
          language_code,
          vocabulary!inner(id, deck_id, language_a_word, language_b_translation)
        )
      `)
      .eq('source_word_id', wordId)
      .order('similarity_score', { ascending: false })
      .limit(5);
    
    // Add user progress context
    return await Promise.all(data?.map(async (item) => {
      const progress = await getUserProgress(item.target_word_id, userId);
      return {
        wordId: item.target_word_id,
        word: item.vocabulary_words.word,
        translation: item.vocabulary_words.vocabulary.language_b_translation,
        deckId: item.vocabulary_words.vocabulary.deck_id,
        score: item.similarity_score,
        ruleTypes: item.rule_types,
        userProgress: progress // 'unseen', 'learning', 'mastered', etc.
      };
    }) || []);
  }
}
```

### Frontend Implementation

#### Similar Words Component
```tsx
// components/SimilarWordsPanel.tsx
interface SimilarWordsPanelProps {
  currentWord: Vocabulary;
  userId: string;
  onWordSelect?: (wordId: number) => void;
}

export function SimilarWordsPanel({ currentWord, userId, onWordSelect }: SimilarWordsPanelProps) {
  const [similarWords, setSimilarWords] = useState<SimilarWordWithContext[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSimilarWords();
  }, [currentWord.id]);

  const loadSimilarWords = async () => {
    setLoading(true);
    try {
      const similar = await WordSimilarityService.getSimilarWordsWithContext(
        currentWord.id, 
        userId
      );
      setSimilarWords(similar);
    } catch (error) {
      console.error('Error loading similar words:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="similar-words-panel">
      <h3 className="text-lg font-semibold mb-3">
        🔍 Similar Words That Might Confuse You
      </h3>
      
      {loading ? (
        <div className="flex justify-center p-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="space-y-2">
          {similarWords.map((similar) => (
            <SimilarWordCard 
              key={similar.wordId}
              similar={similar}
              currentWord={currentWord}
              onSelect={onWordSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

#### Similar Word Card Component
```tsx
// components/SimilarWordCard.tsx
interface SimilarWordCardProps {
  similar: SimilarWordWithContext;
  currentWord: Vocabulary;
  onSelect?: (wordId: number) => void;
}

export function SimilarWordCard({ similar, currentWord, onSelect }: SimilarWordCardProps) {
  const getRuleTypeIcon = (ruleTypes: string[]) => {
    if (ruleTypes.includes('Rule1_Accent')) return '🔤';
    if (ruleTypes.includes('Rule5a_Skeleton')) return '🦴';
    if (ruleTypes.includes('Rule2-4_EditDistance')) return '✏️';
    return '🔗';
  };

  const getProgressBadge = (progress: string) => {
    const badges = {
      'unseen': { text: 'New', color: 'bg-gray-100 text-gray-800' },
      'learning': { text: 'Learning', color: 'bg-yellow-100 text-yellow-800' },
      'mastered': { text: 'Mastered', color: 'bg-green-100 text-green-800' },
      'leeches': { text: 'Struggling', color: 'bg-red-100 text-red-800' }
    };
    const badge = badges[progress] || badges['unseen'];
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${badge.color}`}>
        {badge.text}
      </span>
    );
  };

  return (
    <div 
      className="border rounded-lg p-3 hover:bg-gray-50 cursor-pointer transition-colors"
      onClick={() => onSelect?.(similar.wordId)}
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
            {(similar.score * 100).toFixed(0)}%
          </span>
        </div>
      </div>
      
      <div className="text-xs text-gray-500">
        <span>Deck: {similar.deckId}</span>
        {similar.ruleTypes.length > 0 && (
          <span className="ml-2">
            Rules: {similar.ruleTypes.join(', ')}
          </span>
        )}
      </div>
    </div>
  );
}
```

#### Integration into Study Page
```tsx
// app/study/page.tsx - Add to existing study interface
export default function StudyPage() {
  // ... existing code ...

  return (
    <div className="study-container">
      <div className="main-content">
        {/* Existing flashcard content */}
        <FlashCard 
          word={currentWord}
          // ... existing props
        />
      </div>
      
      {/* New similar words sidebar */}
      <div className="sidebar">
        <SimilarWordsPanel 
          currentWord={currentWord}
          userId={user.id}
          onWordSelect={(wordId) => {
            // Optionally navigate to similar word's deck/context
            console.log('Selected similar word:', wordId);
          }}
        />
      </div>
    </div>
  );
}
```

## Approach 2: Deck-Integrated Similarity (Alternative)

### Backend Architecture
```sql
-- Add similarity columns to existing vocabulary table
ALTER TABLE vocabulary ADD COLUMN similar_words JSONB;
ALTER TABLE vocabulary ADD COLUMN similarity_scores JSONB;

-- Index for JSON queries
CREATE INDEX idx_vocabulary_similar_words ON vocabulary USING GIN (similar_words);
```

### Frontend Implementation
```tsx
// Simpler implementation using existing vocabulary structure
export function SimilarWordsPanel({ currentWord }: { currentWord: Vocabulary }) {
  const similarWords = currentWord.similar_words || [];
  
  return (
    <div className="similar-words-panel">
      {similarWords.map((similar: any) => (
        <div key={similar.wordId} className="similar-word-item">
          <span>{similar.word}</span>
          <span>{similar.translation}</span>
          <span>{similar.score}</span>
        </div>
      ))}
    </div>
  );
}
```

## Approach 3: Hybrid Caching System (Performance-Optimized)

### Backend Architecture
```sql
-- Cache table for frequently accessed similarities
CREATE TABLE similarity_cache (
    id SERIAL PRIMARY KEY,
    word_id INTEGER REFERENCES vocabulary(id),
    similar_words_cache JSONB,
    last_updated TIMESTAMP DEFAULT NOW(),
    cache_version VARCHAR(20)
);

-- Cache invalidation trigger
CREATE OR REPLACE FUNCTION invalidate_similarity_cache()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM similarity_cache 
    WHERE word_id = NEW.source_word_id OR word_id = NEW.target_word_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER similarity_cache_invalidation
    AFTER INSERT OR UPDATE OR DELETE ON word_similarities
    FOR EACH ROW EXECUTE FUNCTION invalidate_similarity_cache();
```

## User Experience Enhancements

### 1. Learning Mode Integration
- **Discovery Mode**: Show similar words as "potential confusions"
- **Review Mode**: Highlight similar words when user makes mistakes
- **Study Mode**: Include similar words in spaced repetition scheduling

### 2. Interactive Features
- **Word Comparison**: Side-by-side comparison of similar words
- **Rule Explanation**: Tooltips explaining why words are similar
- **Progress Tracking**: Track confusion patterns and learning progress

### 3. Adaptive Learning
- **Smart Scheduling**: Prioritize confusing word pairs in review
- **Difficulty Adjustment**: Adjust review frequency based on similarity scores
- **Personalized Recommendations**: Suggest similar words based on user's weak areas

## Implementation Recommendations

### Phase 1: Core Infrastructure
1. Create database schema for word similarities
2. Migrate CSV data to database
3. Implement basic API endpoints
4. Add simple similar words display

### Phase 2: Enhanced UX
1. Integrate into discovery/review modes
2. Add interactive features and explanations
3. Implement progress tracking for similar words
4. Add rule type visualizations

### Phase 3: Advanced Features
1. Implement adaptive learning algorithms
2. Add cross-deck navigation
3. Create similarity-based study modes
4. Add analytics and insights

## Technical Considerations

### Performance
- **Database Indexing**: Proper indexes for fast lookups
- **Caching**: Redis cache for frequently accessed similarities
- **Pagination**: Limit results to prevent UI overload

### Scalability
- **Algorithm Versioning**: Support multiple similarity algorithms
- **Data Partitioning**: Separate tables for different languages
- **API Rate Limiting**: Prevent abuse of similarity lookups

### Data Integrity
- **Bidirectional Relationships**: Ensure consistent similarity data
- **Validation**: Validate similarity scores and rule types
- **Backup Strategy**: Regular backups of similarity data

This system will significantly enhance the learning experience by helping users identify and overcome confusing word pairs, ultimately improving vocabulary retention and reducing learning errors.
