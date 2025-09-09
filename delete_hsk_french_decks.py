#!/usr/bin/env python3
"""
Delete HSK Chinese to French Decks

Deletes the 5 HSK Level Chinese to French decks from Supabase.
"""

from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def create_supabase_client() -> Client:
    """Create and return Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def delete_hsk_french_decks():
    """Delete HSK Chinese to French decks from Supabase."""
    supabase = create_supabase_client()
    
    try:
        # Get all HSK decks that are Chinese to French (not the "Chinese to English" ones)
        response = supabase.table('vocabulary_decks').select('id, name, language_b_name').like('name', 'HSK Level%').neq('name', '%Chinese to English%').execute()
        hsk_decks = response.data
        
        print(f"Found {len(hsk_decks)} HSK decks to delete")
        
        for deck in hsk_decks:
            deck_id = deck['id']
            deck_name = deck['name']
            language_b = deck['language_b_name']
            
            print(f"\n🗑️  Deleting {deck_name} (ID: {deck_id}) - {language_b}")
            
            # Delete deck-vocabulary relationships first
            try:
                supabase.table('deck_vocabulary').delete().eq('deck_id', deck_id).execute()
                print(f"✅ Deleted relationships for {deck_name}")
            except Exception as e:
                print(f"⚠️  Error deleting relationships for {deck_name}: {e}")
            
            # Delete the deck
            try:
                supabase.table('vocabulary_decks').delete().eq('id', deck_id).execute()
                print(f"✅ Deleted deck {deck_name}")
            except Exception as e:
                print(f"❌ Error deleting deck {deck_name}: {e}")
        
        print(f"\n🎊 All HSK Chinese to French decks deleted!")
        
        # Verify deletion
        print("\n📋 Verification:")
        response = supabase.table('vocabulary_decks').select('name, language_a_name, language_b_name').like('name', 'HSK Level%').execute()
        remaining_decks = response.data
        
        if remaining_decks:
            print("Remaining HSK decks:")
            for deck in remaining_decks:
                print(f"- {deck['name']}: {deck['language_a_name']} to {deck['language_b_name']}")
        else:
            print("No HSK decks remaining")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    delete_hsk_french_decks()

