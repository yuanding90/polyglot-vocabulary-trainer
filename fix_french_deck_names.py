#!/usr/bin/env python3
"""
Fix French deck names to ensure proper numerical ordering
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

def fix_french_deck_names():
    """Rename French decks to ensure proper numerical ordering"""
    print("🔧 Fixing French Deck Names for Proper Ordering")
    print("=" * 60)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Define the new names with proper numerical ordering
    french_deck_renames = {
        "French 1": "French 01",
        "French 2": "French 02", 
        "French 3": "French 03",
        "French 4": "French 04",
        "French 5": "French 05",
        "French 6": "French 06",
        "French 7": "French 07",
        "French 8": "French 08",
        "French 9": "French 09",
        "French 10": "French 10",
        "French 11": "French 11",
        "French 12": "French 12",
        "French 13": "French 13",
        "French 14": "French 14",
        "French 15": "French 15",
        "French 16": "French 16"
    }
    
    # Get all French decks
    result = supabase.table('vocabulary_decks').select('*').eq('language_a_code', 'fr-FR').execute()
    french_decks = result.data
    
    print(f"📚 Found {len(french_decks)} French decks")
    
    # Update each French deck name
    updated_count = 0
    for deck in french_decks:
        old_name = deck['name']
        if old_name in french_deck_renames:
            new_name = french_deck_renames[old_name]
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
    
    print(f"\n🎉 Renamed {updated_count} French decks")

def verify_new_ordering():
    """Verify the new deck ordering"""
    print("\n🔍 Verifying New Deck Order")
    print("=" * 50)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Get all decks ordered by name
    result = supabase.table('vocabulary_decks').select('*').order('name', desc=False).execute()
    
    print("New deck order:")
    for i, deck in enumerate(result.data, 1):
        print(f"{i:2d}. {deck['name']} ({deck['language_a_code']} → {deck['language_b_code']})")

def main():
    """Main function"""
    print("🎯 Fixing French Deck Ordering")
    print("=" * 50)
    
    # Step 1: Rename French decks
    fix_french_deck_names()
    
    # Step 2: Verify the new ordering
    verify_new_ordering()
    
    print("\n🎉 French deck ordering fix complete!")

if __name__ == "__main__":
    main()

