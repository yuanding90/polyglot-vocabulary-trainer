#!/usr/bin/env python3
"""
Run SQL migration directly using Supabase client
"""

from supabase import create_client, Client

# Supabase connection
supabase_url = "https://ifgitxejnakfrfeiipkx.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"
supabase: Client = create_client(supabase_url, supabase_key)

def run_migration():
    """Run the French LexiqueData mapping migration."""
    
    print("🚀 RUNNING FRENCH LEXIQUE DATA MAPPING MIGRATION")
    print("="*60)
    
    migration_sql = """
-- Table 1: French Lexique Words Registry
CREATE TABLE IF NOT EXISTS french_lexique_words (
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

-- Table 2: French Vocabulary-Lexique Mapping
CREATE TABLE IF NOT EXISTS french_vocabulary_lexique_mapping (
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
"""
    
    try:
        # Execute the migration SQL
        print("📝 Creating French LexiqueData mapping tables...")
        result = supabase.rpc('exec_sql', {'sql': migration_sql}).execute()
        print("✅ Migration executed successfully")
        
        # Create indexes
        print("📊 Creating indexes...")
        
        index_sqls = [
            "CREATE INDEX IF NOT EXISTS idx_french_lexique_word ON french_lexique_words(word);",
            "CREATE INDEX IF NOT EXISTS idx_french_lexique_normalized ON french_lexique_words(normalized_word);",
            "CREATE INDEX IF NOT EXISTS idx_french_lexique_rank ON french_lexique_words(frequency_rank);",
            "CREATE INDEX IF NOT EXISTS idx_french_lexique_score ON french_lexique_words(frequency_score DESC);",
            "CREATE INDEX IF NOT EXISTS idx_french_vocab_lexique_vocab ON french_vocabulary_lexique_mapping(vocabulary_id);",
            "CREATE INDEX IF NOT EXISTS idx_french_vocab_lexique_lexique ON french_vocabulary_lexique_mapping(french_lexique_word_id);",
            "CREATE INDEX IF NOT EXISTS idx_french_vocab_lexique_type ON french_vocabulary_lexique_mapping(mapping_type);",
            "CREATE INDEX IF NOT EXISTS idx_french_vocab_lexique_confidence ON french_vocabulary_lexique_mapping(confidence_score DESC);"
        ]
        
        for index_sql in index_sqls:
            supabase.rpc('exec_sql', {'sql': index_sql}).execute()
        
        print("✅ Indexes created successfully")
        
        # Enable RLS
        print("🔒 Enabling Row Level Security...")
        
        rls_sqls = [
            "ALTER TABLE french_lexique_words ENABLE ROW LEVEL SECURITY;",
            "ALTER TABLE french_vocabulary_lexique_mapping ENABLE ROW LEVEL SECURITY;"
        ]
        
        for rls_sql in rls_sqls:
            supabase.rpc('exec_sql', {'sql': rls_sql}).execute()
        
        print("✅ RLS enabled successfully")
        
        # Verify tables were created
        print("\n🔍 Verifying table creation...")
        
        # Check if tables exist
        tables_response = supabase.table('french_lexique_words').select('id').limit(1).execute()
        if tables_response.data is not None:
            print("✅ french_lexique_words table created successfully")
        
        mapping_response = supabase.table('french_vocabulary_lexique_mapping').select('id').limit(1).execute()
        if mapping_response.data is not None:
            print("✅ french_vocabulary_lexique_mapping table created successfully")
        
        print("\n🎉 Migration completed successfully!")
        print("📋 Created tables:")
        print("   - french_lexique_words")
        print("   - french_vocabulary_lexique_mapping")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n✅ Ready to proceed with mapping process!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
