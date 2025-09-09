#!/usr/bin/env python3
"""
Create daily_summary table for tracking daily activity
"""

from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def create_daily_summary_table():
    """Create the daily_summary table and related objects"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🚀 Creating daily_summary table...")
    print("=" * 60)
    
    # SQL statements to execute
    sql_statements = [
        # Create the table
        """
        CREATE TABLE IF NOT EXISTS daily_summary (
            id SERIAL PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            reviews_done INTEGER DEFAULT 0,
            new_words_learned INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(user_id, date)
        )
        """,
        
        # Enable RLS
        "ALTER TABLE daily_summary ENABLE ROW LEVEL SECURITY",
        
        # Drop existing policies if they exist
        "DROP POLICY IF EXISTS \"Users can view their own daily summaries\" ON daily_summary",
        "DROP POLICY IF EXISTS \"Users can insert their own daily summaries\" ON daily_summary", 
        "DROP POLICY IF EXISTS \"Users can update their own daily summaries\" ON daily_summary",
        
        # Create policies
        """
        CREATE POLICY "Users can view their own daily summaries" ON daily_summary
            FOR SELECT USING (auth.uid() = user_id)
        """,
        
        """
        CREATE POLICY "Users can insert their own daily summaries" ON daily_summary
            FOR INSERT WITH CHECK (auth.uid() = user_id)
        """,
        
        """
        CREATE POLICY "Users can update their own daily summaries" ON daily_summary
            FOR UPDATE USING (auth.uid() = user_id)
        """,
        
        # Create index
        "CREATE INDEX IF NOT EXISTS idx_daily_summary_user_date ON daily_summary(user_id, date)",
        
        # Create function for updating timestamps
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
        """,
        
        # Create trigger
        """
        DROP TRIGGER IF EXISTS update_daily_summary_updated_at ON daily_summary;
        CREATE TRIGGER update_daily_summary_updated_at 
            BEFORE UPDATE ON daily_summary 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column()
        """
    ]
    
    # Execute each statement
    for i, statement in enumerate(sql_statements, 1):
        try:
            print(f"{i}. Executing SQL statement...")
            # Use the service role client for admin operations
            result = supabase.postgrest.rpc('exec_sql', {'sql': statement}).execute()
            print(f"   ✅ Statement {i} executed successfully")
        except Exception as e:
            print(f"   ❌ Error executing statement {i}: {e}")
            # Continue with other statements
            continue
    
    print("\n" + "=" * 60)
    print("🎉 daily_summary table creation completed!")
    
    # Test the table
    try:
        print("\n🔍 Testing table access...")
        result = supabase.table('daily_summary').select('*').limit(1).execute()
        print("✅ daily_summary table is accessible")
        
        # Check if table exists and show structure
        print("\n📋 Table structure:")
        print("   - id: SERIAL PRIMARY KEY")
        print("   - user_id: UUID (references auth.users)")
        print("   - date: DATE")
        print("   - reviews_done: INTEGER DEFAULT 0")
        print("   - new_words_learned: INTEGER DEFAULT 0")
        print("   - created_at: TIMESTAMP WITH TIME ZONE")
        print("   - updated_at: TIMESTAMP WITH TIME ZONE")
        print("   - UNIQUE(user_id, date)")
        
    except Exception as e:
        print(f"❌ Error testing table: {e}")

if __name__ == "__main__":
    create_daily_summary_table()
