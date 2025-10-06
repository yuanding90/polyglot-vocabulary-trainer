#!/usr/bin/env python3
"""
Create French LexiqueData mapping tables manually using Supabase client
"""

from supabase import create_client, Client

# Supabase connection
supabase_url = "https://ifgitxejnakfrfeiipkx.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"
supabase: Client = create_client(supabase_url, supabase_key)

def create_tables_manually():
    """Create tables by testing if they exist and providing instructions."""
    
    print("🚀 CHECKING FRENCH LEXIQUE DATA MAPPING TABLES")
    print("="*60)
    
    try:
        # Test if french_lexique_words table exists
        print("🔍 Checking french_lexique_words table...")
        try:
            result = supabase.table('french_lexique_words').select('id').limit(1).execute()
            print("✅ french_lexique_words table already exists")
            lexique_table_exists = True
        except Exception as e:
            print("❌ french_lexique_words table does not exist")
            lexique_table_exists = False
        
        # Test if french_vocabulary_lexique_mapping table exists
        print("🔍 Checking french_vocabulary_lexique_mapping table...")
        try:
            result = supabase.table('french_vocabulary_lexique_mapping').select('id').limit(1).execute()
            print("✅ french_vocabulary_lexique_mapping table already exists")
            mapping_table_exists = True
        except Exception as e:
            print("❌ french_vocabulary_lexique_mapping table does not exist")
            mapping_table_exists = False
        
        if lexique_table_exists and mapping_table_exists:
            print("\n🎉 All tables already exist! Ready to proceed with mapping.")
            return True
        else:
            print("\n📋 MANUAL MIGRATION REQUIRED")
            print("="*60)
            print("The Supabase client cannot execute raw SQL directly.")
            print("Please run the following SQL in your Supabase SQL Editor:")
            print()
            print("-- Copy and paste this SQL into Supabase SQL Editor:")
            print("""
-- Table 1: French Lexique Words Registry
CREATE TABLE IF NOT EXISTS french_lexique_words (
    id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    normalized_word TEXT NOT NULL,
    frequency_rank INTEGER NOT NULL,
    frequency_score DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_french_lexique_word UNIQUE (word),
    CONSTRAINT unique_french_lexique_rank UNIQUE (frequency_rank),
    CONSTRAINT valid_french_frequency_rank CHECK (frequency_rank > 0),
    CONSTRAINT valid_french_frequency_score CHECK (frequency_score > 0)
);

-- Table 2: French Vocabulary-Lexique Mapping
CREATE TABLE IF NOT EXISTS french_vocabulary_lexique_mapping (
    id SERIAL PRIMARY KEY,
    vocabulary_id INTEGER NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
    french_lexique_word_id INTEGER NOT NULL REFERENCES french_lexique_words(id) ON DELETE CASCADE,
    mapping_type TEXT NOT NULL CHECK (mapping_type IN ('direct', 'normalized', 'fuzzy', 'manual')),
    confidence_score DECIMAL(3,2) NOT NULL DEFAULT 1.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_french_vocab_lexique_mapping UNIQUE (vocabulary_id, french_lexique_word_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_french_lexique_word ON french_lexique_words(word);
CREATE INDEX IF NOT EXISTS idx_french_lexique_normalized ON french_lexique_words(normalized_word);
CREATE INDEX IF NOT EXISTS idx_french_lexique_rank ON french_lexique_words(frequency_rank);
CREATE INDEX IF NOT EXISTS idx_french_lexique_score ON french_lexique_words(frequency_score DESC);
CREATE INDEX IF NOT EXISTS idx_french_vocab_lexique_vocab ON french_vocabulary_lexique_mapping(vocabulary_id);
CREATE INDEX IF NOT EXISTS idx_french_vocab_lexique_lexique ON french_vocabulary_lexique_mapping(french_lexique_word_id);
CREATE INDEX IF NOT EXISTS idx_french_vocab_lexique_type ON french_vocabulary_lexique_mapping(mapping_type);
CREATE INDEX IF NOT EXISTS idx_french_vocab_lexique_confidence ON french_vocabulary_lexique_mapping(confidence_score DESC);

-- Enable RLS
ALTER TABLE french_lexique_words ENABLE ROW LEVEL SECURITY;
ALTER TABLE french_vocabulary_lexique_mapping ENABLE ROW LEVEL SECURITY;

-- RLS Policies for french_lexique_words
CREATE POLICY IF NOT EXISTS french_lexique_words_read ON french_lexique_words
    FOR SELECT
    USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY IF NOT EXISTS french_lexique_words_write ON french_lexique_words
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- RLS Policies for french_vocabulary_lexique_mapping
CREATE POLICY IF NOT EXISTS french_vocab_lexique_mapping_read ON french_vocabulary_lexique_mapping
    FOR SELECT
    USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY IF NOT EXISTS french_vocab_lexique_mapping_write ON french_vocabulary_lexique_mapping
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
            """)
            print("\nAfter running the SQL, come back and run the mapping script!")
            return False
            
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

if __name__ == "__main__":
    success = create_tables_manually()
    if success:
        print("\n✅ Tables are ready! Proceeding with mapping...")
    else:
        print("\n⏳ Please run the SQL migration first, then retry.")
