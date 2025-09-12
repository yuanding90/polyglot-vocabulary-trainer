#!/usr/bin/env python3
"""
Focused migration script for French-to-English decks only.
Maps word similarities within the 16 main French vocabulary decks.
"""

import csv
import sys
import os
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def get_french_deck_ids(supabase):
    """Get IDs of the 16 main French-to-English decks"""
    # These are the 16 main French decks (French 01 through French 16)
    french_deck_names = [
        "12. French 01", "13. French 02", "14. French 03", "15. French 04",
        "16. French 05", "17. French 06", "18. French 07", "19. French 08",
        "20. French 09", "21. French 10", "22. French 11", "23. French 12",
        "24. French 13", "25. French 14", "26. French 15", "27. French 16"
    ]
    
    decks_result = supabase.table('vocabulary_decks').select('id, name').in_('name', french_deck_names).execute()
    
    if not decks_result.data:
        print("❌ No French decks found!")
        return []
    
    deck_ids = [deck['id'] for deck in decks_result.data]
    print(f"🇫🇷 Found {len(deck_ids)} French-to-English decks:")
    for deck in decks_result.data:
        print(f"   • {deck['name']} (ID: {deck['id']})")
    
    return deck_ids

def get_french_vocabulary_ids(supabase, french_deck_ids):
    """Get all vocabulary IDs from French decks"""
    print(f"\n📚 Getting vocabulary from {len(french_deck_ids)} French decks...")
    
    # Get all vocabulary IDs from French decks
    vocab_result = supabase.table('deck_vocabulary').select('vocabulary_id').in_('deck_id', french_deck_ids).execute()
    
    if not vocab_result.data:
        print("❌ No vocabulary found in French decks!")
        return set()
    
    # Create a set of French vocabulary IDs
    french_vocab_ids = set(item['vocabulary_id'] for item in vocab_result.data)
    print(f"📊 Found {len(french_vocab_ids)} unique French vocabulary words")
    
    return french_vocab_ids

def get_french_word_by_id(supabase, vocab_id):
    """Get French word from vocabulary ID"""
    result = supabase.table('vocabulary').select('id, language_a_word, language_b_translation').eq('id', vocab_id).execute()
    
    if result.data:
        return result.data[0]
    return None

def create_word_id_mapping(supabase, french_vocab_ids):
    """Create mapping from French words to vocabulary IDs"""
    print(f"\n🗺️  Creating word-to-ID mapping for {len(french_vocab_ids)} French words...")
    
    # Get all French vocabulary with their words
    vocab_result = supabase.table('vocabulary').select('id, language_a_word, language_b_translation').in_('id', list(french_vocab_ids)).execute()
    
    if not vocab_result.data:
        print("❌ No vocabulary data found!")
        return {}
    
    # Create mapping: french_word -> vocab_id
    word_to_id = {}
    for vocab in vocab_result.data:
        french_word = vocab['language_a_word'].lower().strip()
        word_to_id[french_word] = vocab['id']
    
    print(f"✅ Created mapping for {len(word_to_id)} French words")
    
    # Show sample mapping
    print(f"\n📝 Sample word mappings:")
    sample_words = list(word_to_id.items())[:5]
    for word, vocab_id in sample_words:
        print(f"   '{word}' → ID {vocab_id}")
    
    return word_to_id

def migrate_french_similarities():
    """Migrate word similarities for French decks only"""
    print("🚀 Starting FRENCH-ONLY word similarity migration...")
    print("=" * 60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Step 1: Get French deck IDs
    french_deck_ids = get_french_deck_ids(supabase)
    if not french_deck_ids:
        return False
    
    # Step 2: Get French vocabulary IDs
    french_vocab_ids = get_french_vocabulary_ids(supabase, french_deck_ids)
    if not french_vocab_ids:
        return False
    
    # Step 3: Create word-to-ID mapping
    word_to_id = create_word_id_mapping(supabase, french_vocab_ids)
    if not word_to_id:
        return False
    
    # Step 4: Process CSV similarities
    csv_file = 'consolidated_results/final_enhanced_french_similarities.csv'
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    print(f"\n📁 Processing similarities from: {csv_file}")
    
    # Track unique relationships
    unique_relationships = set()
    processed_count = 0
    skipped_count = 0
    error_count = 0
    total_relationships = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    target_word = row['target_word'].strip().lower()
                    similar_words_str = row['similar_words']
                    
                    if not target_word or not similar_words_str:
                        continue
                    
                    # Check if target word is in French vocabulary
                    if target_word not in word_to_id:
                        print(f"⚠️  Skipping target word not in French decks: {target_word}")
                        skipped_count += 1
                        continue
                    
                    target_id = word_to_id[target_word]
                    print(f"📍 Target: {target_word} → ID {target_id}")
                    
                    # Parse similar words
                    similar_words = [w.strip().lower() for w in similar_words_str.split(',') if w.strip()]
                    
                    # Create relationships only for French words
                    for similar_word in similar_words:
                        if similar_word not in word_to_id:
                            print(f"   ⚠️  Skipping similar word not in French decks: {similar_word}")
                            skipped_count += 1
                            continue
                        
                        similar_id = word_to_id[similar_word]
                        print(f"   🔗 Similar: {similar_word} → ID {similar_id}")
                        
                        # Create unique key for relationship
                        source_id = min(target_id, similar_id)
                        target_id_rel = max(target_id, similar_id)
                        
                        relationship_key = f"{source_id}-{target_id_rel}"
                        
                        # Only add if not already processed
                        if relationship_key not in unique_relationships:
                            similarity_data = {
                                'source_word_id': source_id,
                                'target_word_id': target_id_rel,
                                'similarity_score': 0.85,  # Default score
                                'rule_types': ['french_similarity'],  # Default rule type
                                'algorithm_version': 'french_decks_v1'
                            }
                            
                            unique_relationships.add(relationship_key)
                            total_relationships += 1
                            
                            # Insert immediately
                            try:
                                result = supabase.table('word_similarities').upsert(
                                    similarity_data,
                                    on_conflict='source_word_id,target_word_id,algorithm_version'
                                ).execute()
                                
                                print(f"   ✅ Created: {source_id} → {target_id_rel}")
                                    
                            except Exception as e:
                                print(f"   ❌ Error inserting relationship: {e}")
                                error_count += 1
                    
                    processed_count += 1
                    print(f"📊 Processed {processed_count} French words, {total_relationships} relationships\n")
                    
                    # Stop after processing a few examples to show the pattern
                    if processed_count >= 3:
                        print("🛑 Stopping after 3 examples to show the mapping pattern...")
                        break
                        
                except Exception as e:
                    print(f"❌ Error processing row {processed_count}: {e}")
                    error_count += 1
                    continue
        
        print("\n" + "=" * 60)
        print("🎉 French-only migration completed!")
        print(f"📊 Summary:")
        print(f"   ✅ Processed {processed_count} French target words")
        print(f"   ⚠️  Skipped {skipped_count} words not in French decks")
        print(f"   ❌ Errors: {error_count}")
        print(f"   🔗 Total unique relationships created: {total_relationships}")
        
        # Verify migration results
        print(f"\n🔍 Verifying migration results...")
        verify_result = supabase.table('word_similarities').select('*', count='exact').eq('algorithm_version', 'french_decks_v1').execute()
        if verify_result.count:
            print(f"   📈 Total French similarity relationships: {verify_result.count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fatal error during migration: {e}")
        return False

if __name__ == "__main__":
    success = migrate_french_similarities()
    if success:
        print("\n🚀 Ready to continue with full French deck migration!")
        print("💡 This script shows how the French-only mapping works.")
        print("🔄 Run with full processing to migrate all French similarities.")
    else:
        print("\n🔧 Please fix errors before proceeding.")
