-- Fix word_similarities table to remove unnecessary fields
-- Keep only source_word_id and target_word_id as requested

-- Drop the existing table
DROP TABLE IF EXISTS word_similarities;

-- Recreate with minimal structure
CREATE TABLE word_similarities (
    id SERIAL PRIMARY KEY,
    source_word_id INTEGER NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
    target_word_id INTEGER NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT no_self_similarity CHECK (source_word_id != target_word_id),
    CONSTRAINT unique_similarity UNIQUE (source_word_id, target_word_id)
);

-- Performance indexes
CREATE INDEX idx_word_similarities_source ON word_similarities(source_word_id);
CREATE INDEX idx_word_similarities_target ON word_similarities(target_word_id);
CREATE INDEX idx_word_similarities_lookup ON word_similarities(source_word_id);

-- Enable RLS
ALTER TABLE word_similarities ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access
CREATE POLICY "Anyone can read word similarities" ON word_similarities FOR SELECT USING (true);
CREATE POLICY "Anyone can insert word similarities" ON word_similarities FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can update word similarities" ON word_similarities FOR UPDATE USING (true);
CREATE POLICY "Anyone can delete word similarities" ON word_similarities FOR DELETE USING (true);

-- Add comment for documentation
COMMENT ON TABLE word_similarities IS 'Simple word similarity relationships - source_word_id to target_word_id mapping only';
