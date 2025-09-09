#!/usr/bin/env python3
"""
Fix complete deck ordering to ensure proper sequence
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
supabase_url = 'https://ifgitxejnakfrfeiipkx.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM'

def fix_complete_deck_ordering():
    """Rename all decks to ensure proper sequence"""
    print("🔧 Fixing Complete Deck Ordering")
    print("=" * 60)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Define the complete desired order with prefixes
    deck_renames = {
        # 1. Chinese Financial Terms (first)
        "Chinese Financial Terms → French": "01. Chinese Financial Terms → French",
        
        # 2. Chinese Finance 1-5
        "Chinese Finance 1": "02. Chinese Finance 1",
        "Chinese Finance 2": "03. Chinese Finance 2", 
        "Chinese Finance 3": "04. Chinese Finance 3",
        "Chinese Finance 4": "05. Chinese Finance 4",
        "Chinese Finance 5": "06. Chinese Finance 5",
        
        # 3. HSK6 Level 1-5
        "HSK6 Level 1": "07. HSK6 Level 1",
        "HSK6 Level 2": "08. HSK6 Level 2",
        "HSK6 Level 3": "09. HSK6 Level 3", 
        "HSK6 Level 4": "10. HSK6 Level 4",
        "HSK6 Level 5": "11. HSK6 Level 5",
        
        # 4. French 01-16 (numerical order)
        "French 01": "12. French 01",
        "French 02": "13. French 02",
        "French 03": "14. French 03",
        "French 04": "15. French 04",
        "French 05": "16. French 05",
        "French 06": "17. French 06",
        "French 07": "18. French 07",
        "French 08": "19. French 08",
        "French 09": "20. French 09",
        "French 10": "21. French 10",
        "French 11": "22. French 11",
        "French 12": "23. French 12",
        "French 13": "24. French 13",
        "French 14": "25. French 14",
        "French 15": "26. French 15",
        "French 16": "27. French 16",
        
        # 5. French Vocabulary Batch (last)
        "French Vocabulary Batch 4 → English": "28. French Vocabulary Batch 4 → English"
    }
    
    # Get all decks
    result = supabase.table('vocabulary_decks').select('*').execute()
    all_decks = result.data
    
    print(f"📚 Found {len(all_decks)} total decks")
    
    # Update each deck name
    updated_count = 0
    for deck in all_decks:
        old_name = deck['name']
        if old_name in deck_renames:
            new_name = deck_renames[old_name]
            deck_id = deck['id']
            
            try:
                supabase.table('vocabulary_decks').update({
                    'name': new_name
                }).eq('id', deck_id).execute()
                
                print(f"✅ Renamed: {old_name} → {new_name}")
                updated_count += 1
                
            except Exception as e:
                print(f"❌ Error renaming {old_name}: {e}")
        else:
            print(f"⚠️  Skipped: {old_name} (not in rename list)")
    
    print(f"\n🎉 Renamed {updated_count} decks")

def verify_final_ordering():
    """Verify the final deck ordering"""
    print("\n🔍 Verifying Final Deck Order")
    print("=" * 50)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Get all decks ordered by name
    result = supabase.table('vocabulary_decks').select('*').order('name', desc=False).execute()
    
    print("Final deck order:")
    for i, deck in enumerate(result.data, 1):
        print(f"{i:2d}. {deck['name']} ({deck['language_a_code']} → {deck['language_b_code']})")

def main():
    """Main function"""
    print("🎯 Fixing Complete Deck Ordering")
    print("=" * 50)
    
    # Step 1: Rename all decks with proper ordering
    fix_complete_deck_ordering()
    
    # Step 2: Verify the final ordering
    verify_final_ordering()
    
    print("\n🎉 Complete deck ordering fix complete!")

if __name__ == "__main__":
    main()

