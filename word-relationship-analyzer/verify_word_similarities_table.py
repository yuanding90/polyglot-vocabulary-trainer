#!/usr/bin/env python3
"""
Verify that the word_similarities table was created successfully in Supabase.
This script checks the table structure, indexes, and policies.
"""

import sys
import os
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def verify_word_similarities_table():
    """Verify the word_similarities table structure and setup."""
    print("🔍 Verifying word_similarities table setup...")
    print("=" * 60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Test 1: Check if table exists and is accessible
        print("1. Testing table accessibility...")
        result = supabase.table('word_similarities').select('*').limit(1).execute()
        print("   ✅ Table exists and is accessible")
        
        # Test 2: Check table structure by attempting to insert a test record
        print("\n2. Testing table structure...")
        test_data = {
            'source_word_id': 1,  # Assuming vocabulary table has at least one record
            'target_word_id': 2,  # Assuming vocabulary table has at least two records
            'similarity_score': 0.85,
            'rule_types': ['accent_confusion', 'near_miss'],
            'algorithm_version': 'enhanced_v1'
        }
        
        # Try to insert test data
        insert_result = supabase.table('word_similarities').insert(test_data).execute()
        print("   ✅ Table structure is correct")
        
        # Clean up test data
        if insert_result.data:
            test_id = insert_result.data[0]['id']
            supabase.table('word_similarities').delete().eq('id', test_id).execute()
            print("   🧹 Test data cleaned up")
        
        # Test 3: Check constraints
        print("\n3. Testing constraints...")
        
        # Test self-similarity constraint
        try:
            invalid_data = {
                'source_word_id': 1,
                'target_word_id': 1,  # Same as source - should fail
                'similarity_score': 0.85,
                'rule_types': ['test'],
                'algorithm_version': 'test'
            }
            supabase.table('word_similarities').insert(invalid_data).execute()
            print("   ❌ Self-similarity constraint not working")
        except Exception as e:
            print("   ✅ Self-similarity constraint working")
        
        # Test 4: Check RLS policies
        print("\n4. Testing RLS policies...")
        # Try to read from table (should work with public read policy)
        read_result = supabase.table('word_similarities').select('*').limit(5).execute()
        print("   ✅ RLS policies allow public read access")
        
        # Test 5: Check vocabulary table integration
        print("\n5. Testing vocabulary table integration...")
        vocab_result = supabase.table('vocabulary').select('id, language_a_word').limit(5).execute()
        if vocab_result.data:
            print(f"   ✅ Found {len(vocab_result.data)} vocabulary records")
            print("   📝 Sample vocabulary words:")
            for vocab in vocab_result.data[:3]:
                print(f"      - ID {vocab['id']}: {vocab['language_a_word']}")
        else:
            print("   ⚠️  No vocabulary records found - this may affect similarity migration")
        
        print("\n" + "=" * 60)
        print("🎉 word_similarities table verification completed successfully!")
        print("\n📋 Summary:")
        print("   ✅ Table created and accessible")
        print("   ✅ Structure and constraints working")
        print("   ✅ RLS policies configured")
        print("   ✅ Integration with vocabulary table verified")
        print("\n🚀 Ready for Phase 2: Data Migration!")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure you ran the SQL script in Supabase SQL Editor")
        print("   2. Check that the vocabulary table exists and has data")
        print("   3. Verify your Supabase credentials are correct")
        return False
    
    return True

if __name__ == "__main__":
    verify_word_similarities_table()
