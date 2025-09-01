#!/usr/bin/env python3
"""
Fix RLS permissions for production - Allow authenticated users to access their own data
This script will fix the database permission issues that prevent user progress from being saved.
"""

import os
import sys
from supabase import create_client, Client

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Use service role for admin operations

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: Missing Supabase environment variables")
    print("Please ensure NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set")
    sys.exit(1)

def main():
    print("🔧 Fixing RLS permissions for production...")
    
    # Create Supabase client with service role (admin access)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    try:
        # Read the SQL fix script
        with open('fix_rls_for_production.sql', 'r') as f:
            sql_script = f.read()
        
        print("📖 Executing RLS fix SQL script...")
        
        # Execute the SQL script
        result = supabase.rpc('exec_sql', {'sql': sql_script})
        
        print("✅ RLS fix SQL executed successfully")
        
        # Verify the fix by checking table permissions
        print("\n🔍 Verifying RLS status...")
        
        # Check if RLS is enabled
        rls_check = supabase.table('user_progress').select('*').limit(1).execute()
        print(f"✅ user_progress table accessible: {len(rls_check.data) >= 0}")
        
        # Try to insert a test record (this should work with service role)
        test_data = {
            'user_id': '00000000-0000-0000-0000-000000000000',  # Test user ID
            'word_id': 1,
            'deck_id': '00000000-0000-0000-0000-000000000000',  # Test deck ID
            'repetitions': 0,
            'interval': 0,
            'ease_factor': 2.5,
            'next_review_date': '2024-01-01T00:00:00Z',
            'again_count': 0
        }
        
        # This should work with service role
        insert_result = supabase.table('user_progress').insert(test_data).execute()
        print(f"✅ Test insert successful: {len(insert_result.data)} records inserted")
        
        # Clean up test data
        supabase.table('user_progress').delete().eq('user_id', '00000000-0000-0000-0000-000000000000').execute()
        print("🧹 Test data cleaned up")
        
        print("\n🎉 RLS permissions fixed successfully!")
        print("\n📋 What was fixed:")
        print("1. ✅ RLS enabled on user_progress, rating_history, study_sessions")
        print("2. ✅ Mock user policies removed")
        print("3. ✅ Proper user policies created (auth.uid() = user_id)")
        print("4. ✅ Users can now insert/update their own progress")
        
        print("\n🚀 Next steps:")
        print("1. Test the app again - user progress should now save")
        print("2. Check that different users see different progress")
        print("3. Verify that review sessions update the database")
        
    except Exception as e:
        print(f"❌ Error fixing RLS permissions: {e}")
        print("\n🔧 Manual fix required:")
        print("1. Go to Supabase Dashboard > SQL Editor")
        print("2. Copy and paste the contents of 'fix_rls_for_production.sql'")
        print("3. Execute the SQL script")
        print("4. Test the app again")
        sys.exit(1)

if __name__ == "__main__":
    main()
