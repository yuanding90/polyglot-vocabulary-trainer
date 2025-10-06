-- Temporarily disable RLS for French LexiqueData mapping tables
-- This allows us to load the data, then we'll re-enable RLS

-- Disable RLS temporarily
ALTER TABLE french_lexique_words DISABLE ROW LEVEL SECURITY;
ALTER TABLE french_vocabulary_lexique_mapping DISABLE ROW LEVEL SECURITY;
