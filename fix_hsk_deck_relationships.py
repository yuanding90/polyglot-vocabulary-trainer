#!/usr/bin/env python3
"""
Fix HSK Deck Relationships

Adds word_order to existing HSK deck relationships.
"""

from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def create_supabase_client() -> Client:
    """Create and return Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def fix_hsk_deck_relationships():
    """Fix word_order for HSK deck relationships."""
    supabase = create_supabase_client()
    
    # Get all HSK decks
    try:
        response = supabase.table('vocabulary_decks').select('id, name').like('name', 'HSK Level%').execute()
        hsk_decks = response.data
        
        print(f"Found {len(hsk_decks)} HSK decks")
        
        for deck in hsk_decks:
            deck_id = deck['id']
            deck_name = deck['name']
            
            print(f"\n🔧 Fixing relationships for {deck_name} (ID: {deck_id})")
            
            # Get all relationships for this deck that don't have word_order
            response = supabase.table('deck_vocabulary').select('*').eq('deck_id', deck_id).is_('word_order', 'null').execute()
            relationships = response.data
            
            if not relationships:
                print(f"✅ No relationships to fix for {deck_name}")
                continue
            
            print(f"📝 Found {len(relationships)} relationships without word_order")
            
            # Update each relationship with word_order
            for i, rel in enumerate(relationships):
                try:
                    update_data = {'word_order': i + 1}
                    supabase.table('deck_vocabulary').update(update_data).eq('id', rel['id']).execute()
                    print(f"✅ Updated relationship {rel['id']} with word_order {i + 1}")
                except Exception as e:
                    print(f"❌ Error updating relationship {rel['id']}: {e}")
            
            print(f"🎉 Fixed {len(relationships)} relationships for {deck_name}")
        
        print(f"\n🎊 All HSK deck relationships fixed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_hsk_deck_relationships()

