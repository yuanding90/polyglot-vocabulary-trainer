-- Fix RLS policies for word_similarities table
-- Add INSERT policy for data migration

-- Drop existing policy if it exists
DROP POLICY IF EXISTS "Anyone can read word similarities" ON word_similarities;

-- Create comprehensive policies
CREATE POLICY "Anyone can read word similarities" ON word_similarities FOR SELECT USING (true);
CREATE POLICY "Anyone can insert word similarities" ON word_similarities FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can update word similarities" ON word_similarities FOR UPDATE USING (true);
CREATE POLICY "Anyone can delete word similarities" ON word_similarities FOR DELETE USING (true);

-- Add comment
COMMENT ON POLICY "Anyone can insert word similarities" ON word_similarities IS 'Allows data migration and management of similarity relationships';
