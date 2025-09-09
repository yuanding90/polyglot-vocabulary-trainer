-- Create daily_summary table for tracking daily activity
CREATE TABLE IF NOT EXISTS daily_summary (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    reviews_done INTEGER DEFAULT 0,
    new_words_learned INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Enable RLS
ALTER TABLE daily_summary ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view their own daily summaries" ON daily_summary
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own daily summaries" ON daily_summary
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own daily summaries" ON daily_summary
    FOR UPDATE USING (auth.uid() = user_id);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_daily_summary_user_date ON daily_summary(user_id, date);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_daily_summary_updated_at 
    BEFORE UPDATE ON daily_summary 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
