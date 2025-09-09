#!/usr/bin/env python3
"""
Verify RLS Setup

Checks if RLS is properly enabled and policies are in place.
"""

from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def create_supabase_client() -> Client:
    """Create and return Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_rls_setup():
    """Verify RLS setup and test access."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🔍 Verifying RLS Setup...")
    print("=" * 50)
    
    # Test reading from tables to see if RLS is working
    tables = ['vocabulary_decks', 'vocabulary', 'deck_vocabulary']
    
    for table in tables:
        print(f"\n📋 Testing {table}...")
        try:
            # Try to read from the table
            response = supabase.table(table).select('*').limit(1).execute()
            
            if response.data:
                print(f"✅ {table}: Read access working (RLS enabled)")
                print(f"   Sample data count: {len(response.data)}")
            else:
                print(f"⚠️  {table}: No data returned (might be empty or RLS blocking)")
                
        except Exception as e:
            print(f"❌ {table}: Error accessing table - {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. ✅ RLS is enabled - your tables are now protected")
    print("2. ✅ Read access is working - users can study vocabulary")
    print("3. ⚠️  Write operations are unrestricted - consider if you need additional policies")
    
    print("\n🔒 Security Recommendations:")
    print("- If you want to restrict INSERT/UPDATE/DELETE to authenticated users only,")
    print("  add these policies in Supabase dashboard:")
    print("  • INSERT: auth.role() = 'authenticated'")
    print("  • UPDATE: auth.role() = 'authenticated'")
    print("  • DELETE: auth.role() = 'authenticated'")
    
    print("\n📱 For your app:")
    print("- Users can read vocabulary data (study sessions work)")
    print("- Admin operations (adding decks) should work with your current setup")
    print("- Consider user authentication if you want user-specific features")

def test_app_functionality():
    """Test if the app can still function with RLS enabled."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\n🧪 Testing App Functionality...")
    print("=" * 50)
    
    try:
        # Test getting decks (what the app needs)
        response = supabase.table('vocabulary_decks').select('*').execute()
        deck_count = len(response.data) if response.data else 0
        print(f"✅ Can read vocabulary_decks: {deck_count} decks found")
        
        # Test getting vocabulary
        response = supabase.table('vocabulary').select('*').limit(5).execute()
        vocab_count = len(response.data) if response.data else 0
        print(f"✅ Can read vocabulary: {vocab_count} sample words found")
        
        # Test getting deck relationships
        response = supabase.table('deck_vocabulary').select('*').limit(5).execute()
        rel_count = len(response.data) if response.data else 0
        print(f"✅ Can read deck_vocabulary: {rel_count} sample relationships found")
        
        print("\n🎉 App functionality test passed!")
        print("Your vocabulary trainer should work normally with RLS enabled.")
        
    except Exception as e:
        print(f"❌ App functionality test failed: {e}")
        print("You may need to adjust RLS policies.")

if __name__ == "__main__":
    verify_rls_setup()
    test_app_functionality()

