-- Migration: Add LexiqueData frequency ranking to vocabulary table
-- This adds support for mapping French word frequency rankings from LexiqueData.txt
-- to vocabulary entries for better study prioritization and frequency-based learning.

-- Add lexique_rank column to vocabulary table
ALTER TABLE vocabulary 
ADD COLUMN IF NOT EXISTS lexique_rank INTEGER;

-- Add index for performance when querying by frequency rank
CREATE INDEX IF NOT EXISTS idx_vocabulary_lexique_rank ON vocabulary(lexique_rank);

-- Add index for combined queries (language + rank)
CREATE INDEX IF NOT EXISTS idx_vocabulary_language_rank ON vocabulary(language_a_word, lexique_rank);

-- Add comment explaining the column
COMMENT ON COLUMN vocabulary.lexique_rank IS 'Frequency ranking from LexiqueData.txt (lower number = higher frequency). NULL means no ranking available.';

-- Add constraint to ensure valid ranking (positive integers)
ALTER TABLE vocabulary 
ADD CONSTRAINT chk_lexique_rank_positive 
CHECK (lexique_rank IS NULL OR lexique_rank > 0);

-- Example queries for future reference:
-- 
-- Find most frequent French words:
-- SELECT language_a_word, lexique_rank 
-- FROM vocabulary 
-- WHERE lexique_rank IS NOT NULL 
-- ORDER BY lexique_rank 
-- LIMIT 100;
--
-- Find words in a specific frequency range:
-- SELECT language_a_word, lexique_rank 
-- FROM vocabulary 
-- WHERE lexique_rank BETWEEN 1000 AND 2000 
-- ORDER BY lexique_rank;
--
-- Find unmapped words:
-- SELECT language_a_word 
-- FROM vocabulary 
-- WHERE lexique_rank IS NULL;
