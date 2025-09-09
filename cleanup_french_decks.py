#!/usr/bin/env python3
"""
Cleanup French Decks Script
Deletes existing French decks to recreate with proper sequential numbering
"""

from supabase import create_client, Client

# Initialize Supabase client
supabase_url = "https://ifgitxejnakfrfeiipkx.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"
supabase: Client = create_client(supabase_url, supabase_key)

def cleanup_french_decks():
    """Delete existing French decks"""
    try:
        # Get all French decks
        result = supabase.table("vocabulary_decks").select("*").eq("language_a_code", "fr-FR").execute()
        
        french_decks = result.data
        print(f"Found {len(french_decks)} French decks to delete:")
        
        for deck in french_decks:
            print(f"- {deck['name']} (ID: {deck['id']})")
        
        # Delete each French deck
        deleted_count = 0
        for deck in french_decks:
            try:
                supabase.table("vocabulary_decks").delete().eq("id", deck["id"]).execute()
                print(f"✅ Deleted: {deck['name']}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Error deleting {deck['name']}: {e}")
        
        print(f"\n🎉 Cleanup complete! Deleted {deleted_count} French decks.")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    print("🧹 Starting French Decks Cleanup")
    print("=" * 40)
    cleanup_french_decks()

