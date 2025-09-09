#!/usr/bin/env python3
"""
Test daily_summary table creation and access
"""

from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def test_daily_summary_table():
    """Test if daily_summary table exists and is accessible"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🔍 Testing daily_summary table...")
    print("=" * 60)
    
    try:
        # Test if table exists by trying to select from it
        print("1. Testing table access...")
        result = supabase.table('daily_summary').select('*').limit(1).execute()
        print("✅ daily_summary table exists and is accessible")
        
        # Check if there's any data
        if result.data:
            print(f"📊 Found {len(result.data)} existing records")
            for record in result.data:
                print(f"   - User: {record['user_id'][:8]}... | Date: {record['date']} | Reviews: {record['reviews_done']} | New Words: {record['new_words_learned']}")
        else:
            print("📊 Table is empty (no records yet)")
        
        # Test table structure by trying to insert a test record
        print("\n2. Testing table structure...")
        test_data = {
            'user_id': '123e4567-e89b-12d3-a456-426614174000',  # Test UUID
            'date': '2025-01-09',
            'reviews_done': 5,
            'new_words_learned': 3
        }
        
        try:
            insert_result = supabase.table('daily_summary').insert(test_data).execute()
            print("✅ Table structure is correct - can insert records")
            
            # Clean up test record
            if insert_result.data:
                record_id = insert_result.data[0]['id']
                supabase.table('daily_summary').delete().eq('id', record_id).execute()
                print("🧹 Cleaned up test record")
                
        except Exception as e:
            print(f"❌ Error testing table structure: {e}")
        
        print("\n3. Testing RLS policies...")
        # Try to access without authentication (should fail)
        try:
            result = supabase.table('daily_summary').select('*').execute()
            print("⚠️  RLS might not be working properly (able to access without auth)")
        except Exception as e:
            print("✅ RLS is working (properly blocked access without auth)")
        
    except Exception as e:
        print(f"❌ Error accessing daily_summary table: {e}")
        print("   The table might not have been created successfully")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 daily_summary table test completed!")
    print("\n📋 Next steps:")
    print("   1. Start the Next.js app: npm run dev")
    print("   2. Go to the dashboard")
    print("   3. Check if Recent Activity stats show correctly")
    print("   4. Do a study session to test activity tracking")
    
    return True

if __name__ == "__main__":
    test_daily_summary_table()
