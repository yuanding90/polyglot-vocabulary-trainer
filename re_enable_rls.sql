-- Re-enable RLS after migration
-- Run this after successful migration

-- Enable RLS on vocabulary_decks
ALTER TABLE vocabulary_decks ENABLE ROW LEVEL SECURITY;

-- Enable RLS on vocabulary
ALTER TABLE vocabulary ENABLE ROW LEVEL SECURITY;

-- Enable RLS on deck_vocabulary
ALTER TABLE deck_vocabulary ENABLE ROW LEVEL SECURITY;

-- Enable RLS on user_progress
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;

-- Enable RLS on study_sessions
ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;

-- Enable RLS on rating_history
ALTER TABLE rating_history ENABLE ROW LEVEL SECURITY;

-- Verify RLS is enabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename IN ('vocabulary_decks', 'vocabulary', 'deck_vocabulary', 'user_progress', 'study_sessions', 'rating_history');
