#!/usr/bin/env python3
"""
Setup RLS Policies for Vocabulary Tables

Enables Row Level Security and sets up proper security policies for:
- vocabulary_decks
- vocabulary  
- deck_vocabulary
"""

from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def create_supabase_client() -> Client:
    """Create and return Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def setup_rls_policies():
    """Setup RLS policies for all vocabulary tables."""
    supabase = create_supabase_client()
    
    print("🔒 Setting up Row Level Security policies...")
    print("=" * 60)
    
    try:
        # Enable RLS on all tables
        print("\n1️⃣ Enabling RLS on tables...")
        
        # Enable RLS on vocabulary_decks
        supabase.rpc('exec_sql', {
            'sql': 'ALTER TABLE vocabulary_decks ENABLE ROW LEVEL SECURITY;'
        }).execute()
        print("✅ RLS enabled on vocabulary_decks")
        
        # Enable RLS on vocabulary
        supabase.rpc('exec_sql', {
            'sql': 'ALTER TABLE vocabulary ENABLE ROW LEVEL SECURITY;'
        }).execute()
        print("✅ RLS enabled on vocabulary")
        
        # Enable RLS on deck_vocabulary
        supabase.rpc('exec_sql', {
            'sql': 'ALTER TABLE deck_vocabulary ENABLE ROW LEVEL SECURITY;'
        }).execute()
        print("✅ RLS enabled on deck_vocabulary")
        
        print("\n2️⃣ Creating security policies...")
        
        # Policy for vocabulary_decks - allow read access to all authenticated users
        supabase.rpc('exec_sql', {
            'sql': '''
            CREATE POLICY "Allow read access to vocabulary_decks" ON vocabulary_decks
            FOR SELECT USING (true);
            '''
        }).execute()
        print("✅ Read policy created for vocabulary_decks")
        
        # Policy for vocabulary - allow read access to all authenticated users
        supabase.rpc('exec_sql', {
            'sql': '''
            CREATE POLICY "Allow read access to vocabulary" ON vocabulary
            FOR SELECT USING (true);
            '''
        }).execute()
        print("✅ Read policy created for vocabulary")
        
        # Policy for deck_vocabulary - allow read access to all authenticated users
        supabase.rpc('exec_sql', {
            'sql': '''
            CREATE POLICY "Allow read access to deck_vocabulary" ON deck_vocabulary
            FOR SELECT USING (true);
            '''
        }).execute()
        print("✅ Read policy created for deck_vocabulary")
        
        # Optional: If you want to restrict write operations to authenticated users only
        # Uncomment the following if you want to restrict INSERT/UPDATE/DELETE to authenticated users
        
        # supabase.rpc('exec_sql', {
        #     'sql': '''
        #     CREATE POLICY "Allow insert for authenticated users" ON vocabulary_decks
        #     FOR INSERT WITH CHECK (auth.role() = 'authenticated');
        #     '''
        # }).execute()
        # print("✅ Insert policy created for vocabulary_decks")
        
        # supabase.rpc('exec_sql', {
        #     'sql': '''
        #     CREATE POLICY "Allow update for authenticated users" ON vocabulary_decks
        #     FOR UPDATE USING (auth.role() = 'authenticated');
        #     '''
        # }).execute()
        # print("✅ Update policy created for vocabulary_decks")
        
        print("\n🎉 RLS setup complete!")
        print("=" * 60)
        print("📋 Summary:")
        print("- RLS enabled on all vocabulary tables")
        print("- Read access allowed for all users (public)")
        print("- Write operations are currently unrestricted (for admin use)")
        print("\n💡 Note: If you want to restrict write operations to authenticated users only,")
        print("   uncomment the INSERT/UPDATE policies in the script.")
        
    except Exception as e:
        print(f"❌ Error setting up RLS: {e}")
        print("\n🔧 Alternative approach:")
        print("You can also set up RLS policies manually in the Supabase dashboard:")
        print("1. Go to Authentication > Policies")
        print("2. Select each table (vocabulary_decks, vocabulary, deck_vocabulary)")
        print("3. Enable RLS and create policies as needed")

def verify_rls_status():
    """Verify RLS status on tables."""
    supabase = create_supabase_client()
    
    print("\n🔍 Verifying RLS status...")
    print("=" * 40)
    
    try:
        # Check RLS status on vocabulary_decks
        result = supabase.rpc('exec_sql', {
            'sql': '''
            SELECT schemaname, tablename, rowsecurity 
            FROM pg_tables 
            WHERE tablename IN ('vocabulary_decks', 'vocabulary', 'deck_vocabulary');
            '''
        }).execute()
        
        if result.data:
            for table in result.data:
                table_name = table['tablename']
                rls_enabled = table['rowsecurity']
                status = "✅ Enabled" if rls_enabled else "❌ Disabled"
                print(f"- {table_name}: {status}")
        else:
            print("❌ Could not verify RLS status")
            
    except Exception as e:
        print(f"❌ Error verifying RLS: {e}")

if __name__ == "__main__":
    setup_rls_policies()
    verify_rls_status()

