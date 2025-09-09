-- Re-enable original RLS policies after testing
-- This restores the proper authentication-based policies

-- Drop mock user policies
DROP POLICY IF EXISTS "Mock user can access progress" ON user_progress;
DROP POLICY IF EXISTS "Mock user can access rating history" ON rating_history;
DROP POLICY IF EXISTS "Mock user can access study sessions" ON study_sessions;

-- Re-create original user-specific policies
CREATE POLICY "Users can view their own progress" ON user_progress
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own progress" ON user_progress
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own progress" ON user_progress
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own rating history" ON rating_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own rating history" ON rating_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own sessions" ON study_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sessions" ON study_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

