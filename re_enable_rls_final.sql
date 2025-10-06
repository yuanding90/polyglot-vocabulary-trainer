-- Re-enable RLS for French LexiqueData mapping tables with proper policies
-- Now that data is loaded, we can enable security

-- Re-enable RLS
ALTER TABLE french_lexique_words ENABLE ROW LEVEL SECURITY;
ALTER TABLE french_vocabulary_lexique_mapping ENABLE ROW LEVEL SECURITY;

-- Create proper policies for service role (full access)
CREATE POLICY french_lexique_words_service_role ON french_lexique_words
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY french_vocab_lexique_mapping_service_role ON french_vocabulary_lexique_mapping
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Create policies for authenticated users (read-only)
CREATE POLICY french_lexique_words_read ON french_lexique_words
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY french_vocab_lexique_mapping_read ON french_vocabulary_lexique_mapping
    FOR SELECT
    TO authenticated
    USING (true);
