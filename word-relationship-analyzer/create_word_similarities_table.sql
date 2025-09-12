-- Create word_similarities table for integrated word similarity system
-- This table stores relationships between words in the existing vocabulary table

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

-- Performance indexes
CREATE INDEX idx_word_similarities_source ON word_similarities(source_word_id);
CREATE INDEX idx_word_similarities_target ON word_similarities(target_word_id);
CREATE INDEX idx_word_similarities_score ON word_similarities(similarity_score DESC);
CREATE INDEX idx_word_similarities_lookup ON word_similarities(source_word_id, similarity_score DESC);

-- Enable RLS
ALTER TABLE word_similarities ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (similarity data is reference data)
CREATE POLICY "Anyone can read word similarities" ON word_similarities FOR SELECT USING (true);

-- Add comment for documentation
COMMENT ON TABLE word_similarities IS 'Stores word similarity relationships between vocabulary words, integrated with existing schema';
COMMENT ON COLUMN word_similarities.source_word_id IS 'ID of the source word from vocabulary table';
COMMENT ON COLUMN word_similarities.target_word_id IS 'ID of the similar word from vocabulary table';
COMMENT ON COLUMN word_similarities.similarity_score IS 'Similarity score between 0 and 1';
COMMENT ON COLUMN word_similarities.rule_types IS 'Array of rule types that triggered this similarity';
COMMENT ON COLUMN word_similarities.algorithm_version IS 'Version of the similarity algorithm used';
