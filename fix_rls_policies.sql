-- Fix RLS policies for French LexiqueData mapping tables
-- This allows the service role to insert data

-- Drop existing policies
DROP POLICY IF EXISTS french_lexique_words_read ON french_lexique_words;
DROP POLICY IF EXISTS french_lexique_words_write ON french_lexique_words;
DROP POLICY IF EXISTS french_vocab_lexique_mapping_read ON french_vocabulary_lexique_mapping;
DROP POLICY IF EXISTS french_vocab_lexique_mapping_write ON french_vocabulary_lexique_mapping;

-- Create new policies that allow service role to insert
CREATE POLICY french_lexique_words_all_access ON french_lexique_words
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY french_vocab_lexique_mapping_all_access ON french_vocabulary_lexique_mapping
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Allow authenticated users to read
CREATE POLICY french_lexique_words_read ON french_lexique_words
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY french_vocab_lexique_mapping_read ON french_vocabulary_lexique_mapping
    FOR SELECT
    TO authenticated
    USING (true);
