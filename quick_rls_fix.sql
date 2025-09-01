-- Quick RLS Fix for Production
-- Run this in Supabase Dashboard > SQL Editor to fix database permissions

-- Step 1: Drop mock user policies
DROP POLICY IF EXISTS "Mock user can access progress" ON user_progress;
DROP POLICY IF EXISTS "Mock user can access rating history" ON rating_history;
DROP POLICY IF EXISTS "Mock user can access study sessions" ON study_sessions;

-- Step 2: Enable RLS on user tables
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE rating_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;

-- Step 3: Create proper user policies for user_progress
CREATE POLICY "Users can view their own progress" ON user_progress
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own progress" ON user_progress
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own progress" ON user_progress
    FOR UPDATE USING (auth.uid() = user_id);

-- Step 4: Create proper user policies for rating_history
CREATE POLICY "Users can view their own rating history" ON rating_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own rating history" ON rating_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Step 5: Create proper user policies for study_sessions
CREATE POLICY "Users can view their own sessions" ON study_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sessions" ON study_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Step 6: Verify the fix
SELECT 
    schemaname, 
    tablename, 
    CASE 
        WHEN rowsecurity THEN '✅ RLS Enabled' 
        ELSE '❌ RLS Disabled' 
    END as rls_status
FROM pg_tables 
WHERE tablename IN ('user_progress', 'study_sessions', 'rating_history');

-- Step 7: Show all policies
SELECT 
    tablename,
    policyname,
    cmd,
    CASE 
        WHEN permissive THEN 'Permissive' 
        ELSE 'Restrictive' 
    END as policy_type
FROM pg_policies 
WHERE tablename IN ('user_progress', 'study_sessions', 'rating_history')
ORDER BY tablename, policyname;
