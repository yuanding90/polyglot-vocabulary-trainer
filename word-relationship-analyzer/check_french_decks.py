#!/usr/bin/env python3
"""
Check what French decks exist in the vocabulary table.
This will help us understand the scope of French vocabulary data.
"""

import sys
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def check_french_decks():
    """Check what French decks exist in the database"""
    print("🔍 Checking French decks in vocabulary table...")
    print("=" * 60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Get all vocabulary decks
        decks_result = supabase.table('vocabulary_decks').select('*').execute()
        
        if not decks_result.data:
            print("❌ No vocabulary decks found!")
            return
        
        print(f"📚 Found {len(decks_result.data)} total decks:")
        print("-" * 50)
        
        french_decks = []
        for deck in decks_result.data:
            deck_name = deck['name']
            lang_a = deck.get('language_a_code', 'unknown')
            lang_b = deck.get('language_b_code', 'unknown')
            
            print(f"📖 {deck_name}")
            print(f"   Language A: {lang_a} | Language B: {lang_b}")
            print(f"   Total words: {deck.get('total_words', 'unknown')}")
            print(f"   Deck ID: {deck['id']}")
            
            # Check if this is a French deck
            if 'french' in deck_name.lower() or lang_a == 'fr' or lang_b == 'fr':
                french_decks.append(deck)
                print(f"   ✅ FRENCH DECK DETECTED")
            print()
        
        print("=" * 60)
        print(f"🇫🇷 Found {len(french_decks)} French decks:")
        
        if french_decks:
            for deck in french_decks:
                print(f"   • {deck['name']} (ID: {deck['id']})")
                
                # Get sample vocabulary from this deck
                vocab_result = supabase.table('deck_vocabulary').select(
                    'vocabulary(id, language_a_word, language_b_translation)'
                ).eq('deck_id', deck['id']).limit(3).execute()
                
                if vocab_result.data:
                    print(f"     Sample words:")
                    for item in vocab_result.data:
                        vocab = item['vocabulary']
                        print(f"       - {vocab['language_a_word']} → {vocab['language_b_translation']}")
                print()
        else:
            print("   ⚠️  No French decks found!")
            
        # Get total French vocabulary count
        if french_decks:
            french_deck_ids = [deck['id'] for deck in french_decks]
            
            # Count vocabulary in French decks
            count_result = supabase.table('deck_vocabulary').select('*', count='exact').in_('deck_id', french_deck_ids).execute()
            
            if count_result.count:
                print(f"📊 Total French vocabulary words: {count_result.count}")
            
            # Get sample French words
            sample_result = supabase.table('deck_vocabulary').select(
                'vocabulary(id, language_a_word, language_b_translation)'
            ).in_('deck_id', french_deck_ids).limit(10).execute()
            
            if sample_result.data:
                print(f"\n📝 Sample French words:")
                for item in sample_result.data:
                    vocab = item['vocabulary']
                    print(f"   ID {vocab['id']}: {vocab['language_a_word']} → {vocab['language_b_translation']}")
        
        return french_decks
        
    except Exception as e:
        print(f"❌ Error checking French decks: {e}")
        return []

if __name__ == "__main__":
    french_decks = check_french_decks()
    if french_decks:
        print(f"\n🎯 Ready to create word similarity mapping for {len(french_decks)} French decks!")
    else:
        print(f"\n⚠️  No French decks found. Please check your database setup.")
