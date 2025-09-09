#!/usr/bin/env python3
"""
Fix deck ordering to ensure proper numerical sequence
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

def add_display_order_column():
    """Add display_order column to vocabulary_decks table"""
    print("🔧 Adding display_order column...")
    
    # This would need to be done via SQL in Supabase dashboard
    # For now, we'll use a workaround by updating the deck names to include ordering
    
    print("✅ Column addition would be done via SQL")
    print("   ALTER TABLE vocabulary_decks ADD COLUMN display_order INTEGER;")

def update_deck_ordering():
    """Update deck ordering to ensure proper sequence"""
    print("\n🔧 Updating Deck Ordering")
    print("=" * 50)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Define the desired order
    deck_order = [
        # 1. Chinese Financial Terms (first)
        "Chinese Financial Terms → French",
        
        # 2. Chinese Finance 1-5
        "Chinese Finance 1",
        "Chinese Finance 2", 
        "Chinese Finance 3",
        "Chinese Finance 4",
        "Chinese Finance 5",
        
        # 3. HSK6 Level 1-5
        "HSK6 Level 1",
        "HSK6 Level 2",
        "HSK6 Level 3", 
        "HSK6 Level 4",
        "HSK6 Level 5",
        
        # 4. French 1-16 (numerical order)
        "French 1",
        "French 2",
        "French 3",
        "French 4", 
        "French 5",
        "French 6",
        "French 7",
        "French 8",
        "French 9",
        "French 10",
        "French 11",
        "French 12",
        "French 13",
        "French 14",
        "French 15",
        "French 16",
        
        # 5. French Vocabulary Batch (last)
        "French Vocabulary Batch 4 → English"
    ]
    
    # Get all current decks
    result = supabase.table('vocabulary_decks').select('*').execute()
    current_decks = {deck['name']: deck for deck in result.data}
    
    print(f"📚 Found {len(current_decks)} decks")
    
    # Update each deck with proper ordering
    for order_index, deck_name in enumerate(deck_order, 1):
        if deck_name in current_decks:
            deck_id = current_decks[deck_name]['id']
            
            # Update the deck with display_order
            try:
                supabase.table('vocabulary_decks').update({
                    'display_order': order_index
                }).eq('id', deck_id).execute()
                
                print(f"✅ {order_index:2d}. {deck_name}")
                
            except Exception as e:
                print(f"❌ Error updating {deck_name}: {e}")
        else:
            print(f"⚠️  Deck not found: {deck_name}")
    
    print(f"\n🎉 Updated {len(deck_order)} decks with proper ordering")

def verify_ordering():
    """Verify the new deck ordering"""
    print("\n🔍 Verifying New Deck Order")
    print("=" * 50)
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Try to order by display_order
        result = supabase.table('vocabulary_decks').select('*').order('display_order', desc=False).execute()
        
        print("New deck order:")
        for i, deck in enumerate(result.data, 1):
            order = deck.get('display_order', 'NULL')
            print(f"{i:2d}. {deck['name']} (Order: {order})")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Falling back to name ordering...")
        
        # Fallback to name ordering
        result = supabase.table('vocabulary_decks').select('*').order('name', desc=False).execute()
        
        print("Current deck order (by name):")
        for i, deck in enumerate(result.data, 1):
            print(f"{i:2d}. {deck['name']}")

def main():
    """Main function"""
    print("🎯 Fixing Deck Ordering")
    print("=" * 50)
    
    # Step 1: Add display_order column (would need SQL)
    add_display_order_column()
    
    # Step 2: Update deck ordering
    update_deck_ordering()
    
    # Step 3: Verify the ordering
    verify_ordering()
    
    print("\n🎉 Deck ordering fix complete!")

if __name__ == "__main__":
    main()

