-- Temporarily disable RLS for migration
-- Run this before migration, then re-enable after

-- Disable RLS on vocabulary_decks
ALTER TABLE vocabulary_decks DISABLE ROW LEVEL SECURITY;

-- Disable RLS on vocabulary
ALTER TABLE vocabulary DISABLE ROW LEVEL SECURITY;

-- Disable RLS on deck_vocabulary
ALTER TABLE deck_vocabulary DISABLE ROW LEVEL SECURITY;

-- Disable RLS on user_progress
ALTER TABLE user_progress DISABLE ROW LEVEL SECURITY;

-- Disable RLS on study_sessions
ALTER TABLE study_sessions DISABLE ROW LEVEL SECURITY;

-- Disable RLS on rating_history
ALTER TABLE rating_history DISABLE ROW LEVEL SECURITY;

-- Verify RLS is disabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename IN ('vocabulary_decks', 'vocabulary', 'deck_vocabulary', 'user_progress', 'study_sessions', 'rating_history');
