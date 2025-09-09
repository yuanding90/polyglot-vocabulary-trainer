#!/usr/bin/env python3
"""
Test what happens when we simulate authenticated access
"""

from supabase import create_client
from datetime import datetime, timedelta

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def test_with_service_role_key():
    """Test with service role key if available."""
    print("🔍 Testing with service role key...")
    print("=" * 50)
    
    # Note: We don't have the service role key, but let's see what happens
    # if we try to access the data with elevated permissions
    
    # Try to create a client that might bypass RLS
    try:
        # This won't work without the service role key, but let's see the error
        service_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Try to get data
        result = service_client.table('rating_history').select('*').limit(5).execute()
        print(f"Service role access: {len(result.data) if result.data else 0} records")
        
    except Exception as e:
        print(f"Service role test failed: {e}")

def test_rls_behavior():
    """Test RLS behavior more thoroughly."""
    print("\n🔍 Testing RLS behavior...")
    print("=" * 50)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Test 1: Can we see the table structure?
    try:
        print("1. Testing table structure access...")
        result = supabase.table('rating_history').select('id').limit(1).execute()
        print(f"   ✅ Can access table structure: {len(result.data) if result.data else 0} records")
    except Exception as e:
        print(f"   ❌ Cannot access table: {e}")
    
    # Test 2: Can we see any data at all?
    try:
        print("\n2. Testing data access...")
        result = supabase.table('rating_history').select('*').limit(1).execute()
        print(f"   Data access: {len(result.data) if result.data else 0} records")
        if result.data:
            print(f"   Sample: {result.data[0]}")
    except Exception as e:
        print(f"   Data access error: {e}")
    
    # Test 3: Can we see data with specific user_id?
    try:
        print("\n3. Testing with specific user_id...")
        # Try with a UUID format
        test_user_id = "123e4567-e89b-12d3-a456-426614174000"
        result = supabase.table('rating_history').select('*').eq('user_id', test_user_id).execute()
        print(f"   With specific user_id: {len(result.data) if result.data else 0} records")
    except Exception as e:
        print(f"   Specific user_id error: {e}")
    
    # Test 4: Can we see data with any user_id?
    try:
        print("\n4. Testing with any user_id...")
        result = supabase.table('rating_history').select('user_id').limit(10).execute()
        if result.data:
            user_ids = [record['user_id'] for record in result.data]
            print(f"   Found user_ids: {user_ids[:3]}")
            
            # Try with the first real user_id
            real_user_id = user_ids[0]
            result2 = supabase.table('rating_history').select('*').eq('user_id', real_user_id).execute()
            print(f"   Records for real user: {len(result2.data) if result2.data else 0}")
        else:
            print("   No user_ids found")
    except Exception as e:
        print(f"   Any user_id error: {e}")

def test_column_names():
    """Test if there's a column name issue."""
    print("\n🔍 Testing column names...")
    print("=" * 50)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Test different column names
    columns_to_test = ['created_at', 'timestamp', 'updated_at']
    
    for column in columns_to_test:
        try:
            print(f"Testing column '{column}'...")
            result = supabase.table('rating_history').select(column).limit(1).execute()
            print(f"   ✅ Column '{column}' exists: {len(result.data) if result.data else 0} records")
        except Exception as e:
            print(f"   ❌ Column '{column}' error: {e}")

if __name__ == "__main__":
    test_rls_behavior()
    test_column_names()
    test_with_service_role_key()
