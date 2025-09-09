#!/usr/bin/env python3
"""
Check rating_history table structure and data
"""

from supabase import create_client, Client
import uuid

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def create_supabase_client() -> Client:
    """Create and return Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def check_rating_history_table():
    """Check rating_history table structure and data."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🔍 Checking rating_history table...")
    print("=" * 60)
    
    try:
        # Try to get a sample of data to see the structure
        print("1. Getting sample data from rating_history...")
        result = supabase.table('rating_history').select('*').limit(5).execute()
        
        if result.data:
            print(f"✅ Table exists and has {len(result.data)} sample records")
            print("\n📋 Sample data structure:")
            for i, record in enumerate(result.data):
                print(f"  Record {i+1}:")
                for key, value in record.items():
                    print(f"    {key}: {value} ({type(value).__name__})")
                print()
        else:
            print("⚠️  Table exists but has no data")
            
    except Exception as e:
        print(f"❌ Error accessing rating_history table: {e}")
        return
    
    try:
        # Get total count
        print("2. Getting total count...")
        count_result = supabase.table('rating_history').select('*', count='exact').execute()
        total_count = count_result.count
        print(f"📊 Total records in rating_history: {total_count}")
        
    except Exception as e:
        print(f"❌ Error getting count: {e}")
    
    try:
        # Check recent data
        print("\n3. Getting recent data (last 10 records)...")
        recent_result = supabase.table('rating_history').select('*').order('created_at', desc=True).limit(10).execute()
        
        if recent_result.data:
            print(f"📅 Recent {len(recent_result.data)} records:")
            for record in recent_result.data:
                print(f"  - {record.get('created_at', 'N/A')} | {record.get('rating', 'N/A')} | User: {record.get('user_id', 'N/A')[:8]}...")
        else:
            print("⚠️  No recent data found")
            
    except Exception as e:
        print(f"❌ Error getting recent data: {e}")
    
    try:
        # Check column names by trying different queries
        print("\n4. Testing column names...")
        
        # Test timestamp column
        try:
            timestamp_result = supabase.table('rating_history').select('timestamp').limit(1).execute()
            print("✅ 'timestamp' column exists")
        except Exception as e:
            print(f"❌ 'timestamp' column error: {e}")
        
        # Test created_at column
        try:
            created_at_result = supabase.table('rating_history').select('created_at').limit(1).execute()
            print("✅ 'created_at' column exists")
        except Exception as e:
            print(f"❌ 'created_at' column error: {e}")
            
    except Exception as e:
        print(f"❌ Error testing columns: {e}")
    
    try:
        # Check for data in last 30 days
        print("\n5. Checking data in last 30 days...")
        from datetime import datetime, timedelta
        
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        recent_data = supabase.table('rating_history').select('*').gte('created_at', thirty_days_ago).execute()
        
        if recent_data.data:
            print(f"📈 Found {len(recent_data.data)} records in last 30 days")
            
            # Group by date
            from collections import defaultdict
            daily_counts = defaultdict(int)
            for record in recent_data.data:
                date_str = record['created_at'][:10]  # YYYY-MM-DD
                daily_counts[date_str] += 1
            
            print("📅 Daily breakdown (last 10 days):")
            sorted_dates = sorted(daily_counts.keys(), reverse=True)[:10]
            for date in sorted_dates:
                print(f"  {date}: {daily_counts[date]} ratings")
        else:
            print("⚠️  No data found in last 30 days")
            
    except Exception as e:
        print(f"❌ Error checking recent data: {e}")

def test_rating_insertion():
    """Test if we can insert a rating record."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\n🧪 Testing rating insertion...")
    print("=" * 40)
    
    try:
        # Try to insert a test record
        test_data = {
            'user_id': '00000000-0000-0000-0000-000000000000',  # Mock user ID
            'word_id': 1,
            'deck_id': '00000000-0000-0000-0000-000000000000',  # Mock deck ID
            'rating': 'good',
            'timestamp': datetime.now().isoformat()
        }
        
        result = supabase.table('rating_history').insert(test_data).execute()
        print("✅ Successfully inserted test rating record")
        print(f"   Inserted record: {result.data}")
        
        # Clean up - delete the test record
        if result.data:
            record_id = result.data[0]['id']
            supabase.table('rating_history').delete().eq('id', record_id).execute()
            print("🧹 Cleaned up test record")
            
    except Exception as e:
        print(f"❌ Error testing insertion: {e}")

if __name__ == "__main__":
    from datetime import datetime
    check_rating_history_table()
    test_rating_insertion()
