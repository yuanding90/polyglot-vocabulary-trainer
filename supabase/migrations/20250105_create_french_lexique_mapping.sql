-- Migration: Create French LexiqueData ranking mapping tables
-- This migration creates tables to map French word frequency rankings from LexiqueData.txt
-- to vocabulary entries for better study prioritization and frequency-based learning.

-- Table 1: French Lexique Words Registry
CREATE TABLE french_lexique_words (
    id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    normalized_word TEXT NOT NULL,
    frequency_rank INTEGER NOT NULL,
    frequency_score DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_french_lexique_word UNIQUE (word),
    CONSTRAINT unique_french_lexique_rank UNIQUE (frequency_rank),
    CONSTRAINT valid_french_frequency_rank CHECK (frequency_rank > 0),
    CONSTRAINT valid_french_frequency_score CHECK (frequency_score > 0)
);

-- Indexes for performance
CREATE INDEX idx_french_lexique_word ON french_lexique_words(word);
CREATE INDEX idx_french_lexique_normalized ON french_lexique_words(normalized_word);
CREATE INDEX idx_french_lexique_rank ON french_lexique_words(frequency_rank);
CREATE INDEX idx_french_lexique_score ON french_lexique_words(frequency_score DESC);

-- Table 2: French Vocabulary-Lexique Mapping
CREATE TABLE french_vocabulary_lexique_mapping (
    id SERIAL PRIMARY KEY,
    vocabulary_id INTEGER NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
    french_lexique_word_id INTEGER NOT NULL REFERENCES french_lexique_words(id) ON DELETE CASCADE,
    mapping_type TEXT NOT NULL CHECK (mapping_type IN ('direct', 'normalized', 'fuzzy', 'manual')),
    confidence_score DECIMAL(3,2) NOT NULL DEFAULT 1.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_french_vocab_lexique_mapping UNIQUE (vocabulary_id, french_lexique_word_id)
);

-- Indexes for performance
CREATE INDEX idx_french_vocab_lexique_vocab ON french_vocabulary_lexique_mapping(vocabulary_id);
CREATE INDEX idx_french_vocab_lexique_lexique ON french_vocabulary_lexique_mapping(french_lexique_word_id);
CREATE INDEX idx_french_vocab_lexique_type ON french_vocabulary_lexique_mapping(mapping_type);
CREATE INDEX idx_french_vocab_lexique_confidence ON french_vocabulary_lexique_mapping(confidence_score DESC);

-- Enable RLS
ALTER TABLE french_lexique_words ENABLE ROW LEVEL SECURITY;
ALTER TABLE french_vocabulary_lexique_mapping ENABLE ROW LEVEL SECURITY;

-- RLS Policies for french_lexique_words
CREATE POLICY french_lexique_words_read ON french_lexique_words
    FOR SELECT
    USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY french_lexique_words_write ON french_lexique_words
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- RLS Policies for french_vocabulary_lexique_mapping
CREATE POLICY french_vocab_lexique_mapping_read ON french_vocabulary_lexique_mapping
    FOR SELECT
    USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY french_vocab_lexique_mapping_write ON french_vocabulary_lexique_mapping
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Add comments explaining the tables
COMMENT ON TABLE french_lexique_words IS 'French word frequency data from LexiqueData.txt with rankings and normalized forms for mapping';
COMMENT ON TABLE french_vocabulary_lexique_mapping IS 'Mapping between vocabulary entries and French LexiqueData frequency rankings with confidence scoring';

COMMENT ON COLUMN french_lexique_words.frequency_rank IS 'Frequency ranking from LexiqueData.txt (lower number = higher frequency)';
COMMENT ON COLUMN french_lexique_words.frequency_score IS 'Frequency score from LexiqueData.txt';
COMMENT ON COLUMN french_lexique_words.normalized_word IS 'Normalized form of the word (no accents, lowercase) for matching';

COMMENT ON COLUMN french_vocabulary_lexique_mapping.mapping_type IS 'How the mapping was achieved: direct, normalized, fuzzy, or manual';
COMMENT ON COLUMN french_vocabulary_lexique_mapping.confidence_score IS 'Confidence in the mapping (1.0 = direct match, 0.8 = normalized, etc.)';

-- Example queries for future reference:
-- 
-- Find vocabulary with frequency rankings:
-- SELECT v.id, v.language_a_word, flw.frequency_rank, flw.frequency_score
-- FROM vocabulary v
-- JOIN french_vocabulary_lexique_mapping fvlm ON v.id = fvlm.vocabulary_id
-- JOIN french_lexique_words flw ON fvlm.french_lexique_word_id = flw.id
-- ORDER BY flw.frequency_rank;
--
-- Find most frequent French words in vocabulary:
-- SELECT v.language_a_word, flw.frequency_rank
-- FROM vocabulary v
-- JOIN french_vocabulary_lexique_mapping fvlm ON v.id = fvlm.vocabulary_id
-- JOIN french_lexique_words flw ON fvlm.french_lexique_word_id = flw.id
-- WHERE fvlm.mapping_type = 'direct'
-- ORDER BY flw.frequency_rank
-- LIMIT 100;
--
-- Find unmapped vocabulary:
-- SELECT v.id, v.language_a_word
-- FROM vocabulary v
-- LEFT JOIN french_vocabulary_lexique_mapping fvlm ON v.id = fvlm.vocabulary_id
-- WHERE fvlm.vocabulary_id IS NULL;
