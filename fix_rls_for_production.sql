-- Fix RLS for production - Allow authenticated users to access their own data
-- Run this to fix the database permission issues

-- First, drop the mock user policies
DROP POLICY IF EXISTS "Mock user can access progress" ON user_progress;
DROP POLICY IF EXISTS "Mock user can access rating history" ON rating_history;
DROP POLICY IF EXISTS "Mock user can access study sessions" ON study_sessions;

-- Enable RLS on all user tables
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE rating_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;

-- Create proper user policies for user_progress
CREATE POLICY "Users can view their own progress" ON user_progress
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own progress" ON user_progress
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own progress" ON user_progress
    FOR UPDATE USING (auth.uid() = user_id);

-- Create proper user policies for rating_history
CREATE POLICY "Users can view their own rating history" ON rating_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own rating history" ON rating_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Create proper user policies for study_sessions
CREATE POLICY "Users can view their own sessions" ON study_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sessions" ON study_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Verify RLS is enabled and policies are correct
SELECT 
    schemaname, 
    tablename, 
    rowsecurity,
    CASE 
        WHEN rowsecurity THEN 'RLS Enabled' 
        ELSE 'RLS Disabled' 
    END as rls_status
FROM pg_tables 
WHERE tablename IN ('user_progress', 'study_sessions', 'rating_history');

-- Show all policies for user tables
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive as is_permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename IN ('user_progress', 'study_sessions', 'rating_history')
ORDER BY tablename, policyname;
