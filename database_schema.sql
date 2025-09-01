-- Multi-Language Vocabulary Trainer Database Schema
-- This schema supports any language pair (A → B)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Vocabulary table (language-agnostic)
CREATE TABLE IF NOT EXISTS vocabulary (
    id BIGSERIAL PRIMARY KEY,
    language_a_word TEXT NOT NULL,
    language_b_translation TEXT NOT NULL,
    language_a_sentence TEXT NOT NULL,
    language_b_sentence TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vocabulary decks table with language pair information
CREATE TABLE IF NOT EXISTS vocabulary_decks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    language_a_code TEXT NOT NULL, -- e.g., 'zh', 'fr', 'en'
    language_b_code TEXT NOT NULL, -- e.g., 'fr', 'en', 'es'
    language_a_name TEXT NOT NULL, -- e.g., 'Chinese', 'French', 'English'
    language_b_name TEXT NOT NULL, -- e.g., 'French', 'English', 'Spanish'
    difficulty_level TEXT CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced', 'master')) DEFAULT 'beginner',
    total_words INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Deck vocabulary relationship table
CREATE TABLE IF NOT EXISTS deck_vocabulary (
    id BIGSERIAL PRIMARY KEY,
    deck_id UUID REFERENCES vocabulary_decks(id) ON DELETE CASCADE,
    vocabulary_id BIGINT REFERENCES vocabulary(id) ON DELETE CASCADE,
    word_order INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(deck_id, vocabulary_id)
);

-- User progress table
CREATE TABLE IF NOT EXISTS user_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    word_id BIGINT REFERENCES vocabulary(id) ON DELETE CASCADE,
    deck_id UUID REFERENCES vocabulary_decks(id) ON DELETE CASCADE,
    repetitions INTEGER DEFAULT 0,
    interval INTEGER DEFAULT 0,
    ease_factor DECIMAL(3,2) DEFAULT 2.50,
    next_review_date TIMESTAMPTZ DEFAULT NOW(),
    again_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, word_id, deck_id)
);

-- Study sessions table
CREATE TABLE IF NOT EXISTS study_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    deck_id UUID REFERENCES vocabulary_decks(id) ON DELETE CASCADE,
    session_type TEXT CHECK (session_type IN ('review', 'discovery', 'deep-dive')),
    words_studied INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    session_duration INTEGER DEFAULT 0, -- in seconds
    completed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rating history table for SRS algorithm
CREATE TABLE IF NOT EXISTS rating_history (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    word_id BIGINT REFERENCES vocabulary(id) ON DELETE CASCADE,
    deck_id UUID REFERENCES vocabulary_decks(id) ON DELETE CASCADE,
    rating TEXT CHECK (rating IN ('again', 'hard', 'good', 'easy', 'learn', 'know')),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_vocabulary_decks_language_pair ON vocabulary_decks(language_a_code, language_b_code);
CREATE INDEX IF NOT EXISTS idx_deck_vocabulary_deck_id ON deck_vocabulary(deck_id);
CREATE INDEX IF NOT EXISTS idx_deck_vocabulary_vocabulary_id ON deck_vocabulary(vocabulary_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_deck_id ON user_progress(deck_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_next_review ON user_progress(next_review_date);
CREATE INDEX IF NOT EXISTS idx_study_sessions_user_id ON study_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_study_sessions_deck_id ON study_sessions(deck_id);
CREATE INDEX IF NOT EXISTS idx_rating_history_user_word ON rating_history(user_id, word_id);
CREATE INDEX IF NOT EXISTS idx_rating_history_timestamp ON rating_history(timestamp);

-- Create unique indexes for constraints
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_progress_unique ON user_progress(user_id, word_id, deck_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_deck_vocabulary_unique ON deck_vocabulary(deck_id, vocabulary_id);

-- Row Level Security (RLS) Policies
-- Note: These will be enabled after data migration

-- Enable RLS on all tables
ALTER TABLE vocabulary ENABLE ROW LEVEL SECURITY;
ALTER TABLE vocabulary_decks ENABLE ROW LEVEL SECURITY;
ALTER TABLE deck_vocabulary ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE rating_history ENABLE ROW LEVEL SECURITY;

-- Public read policies for vocabulary and decks (no authentication required for reading)
CREATE POLICY "Public read access to vocabulary" ON vocabulary
    FOR SELECT USING (true);

CREATE POLICY "Public read access to vocabulary_decks" ON vocabulary_decks
    FOR SELECT USING (true);

CREATE POLICY "Public read access to deck_vocabulary" ON deck_vocabulary
    FOR SELECT USING (true);

-- User-specific policies for progress and sessions
CREATE POLICY "Users can view their own progress" ON user_progress
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own progress" ON user_progress
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own progress" ON user_progress
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own sessions" ON study_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sessions" ON study_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own rating history" ON rating_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own rating history" ON rating_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Function to update deck total_words
CREATE OR REPLACE FUNCTION update_deck_total_words()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE vocabulary_decks 
        SET total_words = total_words + 1 
        WHERE id = NEW.deck_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE vocabulary_decks 
        SET total_words = total_words - 1 
        WHERE id = OLD.deck_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update deck total_words
CREATE TRIGGER trigger_update_deck_total_words
    AFTER INSERT OR DELETE ON deck_vocabulary
    FOR EACH ROW
    EXECUTE FUNCTION update_deck_total_words();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER trigger_update_vocabulary_updated_at
    BEFORE UPDATE ON vocabulary
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_update_user_progress_updated_at
    BEFORE UPDATE ON user_progress
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
