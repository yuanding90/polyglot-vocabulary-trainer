-- Temporarily disable RLS for testing with mock user
-- This allows the mock user to insert/update data without authentication

-- Disable RLS on user_progress table
ALTER TABLE user_progress DISABLE ROW LEVEL SECURITY;

-- Disable RLS on rating_history table  
ALTER TABLE rating_history DISABLE ROW LEVEL SECURITY;

-- Disable RLS on study_sessions table
ALTER TABLE study_sessions DISABLE ROW LEVEL SECURITY;

-- Create policies that allow the mock user to access data
-- Mock user ID: 00000000-0000-0000-0000-000000000000

-- User progress policies for mock user
DROP POLICY IF EXISTS "Users can view their own progress" ON user_progress;
DROP POLICY IF EXISTS "Users can insert their own progress" ON user_progress;
DROP POLICY IF EXISTS "Users can update their own progress" ON user_progress;

CREATE POLICY "Mock user can access progress" ON user_progress
    FOR ALL USING (user_id = '00000000-0000-0000-0000-000000000000'::uuid);

-- Rating history policies for mock user
DROP POLICY IF EXISTS "Users can view their own rating history" ON rating_history;
DROP POLICY IF EXISTS "Users can insert their own rating history" ON rating_history;

CREATE POLICY "Mock user can access rating history" ON rating_history
    FOR ALL USING (user_id = '00000000-0000-0000-0000-000000000000'::uuid);

-- Study sessions policies for mock user
DROP POLICY IF EXISTS "Users can view their own sessions" ON study_sessions;
DROP POLICY IF EXISTS "Users can insert their own sessions" ON study_sessions;

CREATE POLICY "Mock user can access study sessions" ON study_sessions
    FOR ALL USING (user_id = '00000000-0000-0000-0000-000000000000'::uuid);

-- Re-enable RLS
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE rating_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;
