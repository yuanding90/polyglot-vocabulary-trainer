#!/usr/bin/env python3
"""
Update HSK Decks to Chinese to French

Updates existing HSK decks from Chinese to English to Chinese to French.
"""

from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def create_supabase_client() -> Client:
    """Create and return Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def update_hsk_decks_to_french():
    """Update HSK decks from Chinese to English to Chinese to French."""
    supabase = create_supabase_client()
    
    try:
        # Get all HSK decks
        response = supabase.table('vocabulary_decks').select('id, name').like('name', 'HSK Level%').execute()
        hsk_decks = response.data
        
        print(f"Found {len(hsk_decks)} HSK decks to update")
        
        for deck in hsk_decks:
            deck_id = deck['id']
            deck_name = deck['name']
            
            print(f"\n🔄 Updating {deck_name} (ID: {deck_id}) to Chinese to French")
            
            # Update the deck to Chinese to French
            try:
                update_data = {
                    'language_b_name': 'French',
                    'language_b_code': 'fr-FR'
                }
                
                response = supabase.table('vocabulary_decks').update(update_data).eq('id', deck_id).execute()
                
                if response.data:
                    print(f"✅ Updated {deck_name} to Chinese to French")
                else:
                    print(f"❌ Failed to update {deck_name}")
                    
            except Exception as e:
                print(f"❌ Error updating {deck_name}: {e}")
        
        print(f"\n🎊 All HSK decks updated to Chinese to French!")
        
        # Verify the changes
        print("\n📋 Verification:")
        response = supabase.table('vocabulary_decks').select('name, language_a_name, language_b_name').like('name', 'HSK Level%').execute()
        for deck in response.data:
            print(f"- {deck['name']}: {deck['language_a_name']} to {deck['language_b_name']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_hsk_decks_to_french()

