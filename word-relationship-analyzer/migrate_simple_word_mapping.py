#!/usr/bin/env python3
"""
Simple migration script for word similarities.
Just maps source_word_id to target_word_id without scores or rule types.
"""

import csv
import sys
import os
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def get_vocabulary_word_id(supabase, word: str) -> int:
    """Get vocabulary ID by matching language_a_word (case-insensitive)"""
    result = supabase.table('vocabulary').select('id, language_a_word').eq(
        'language_a_word', word.lower()
    ).execute()
    
    if result.data:
        return result.data[0]['id']
    else:
        raise ValueError(f"Word not found in vocabulary: {word}")

def show_vocabulary_sample(supabase, limit=10):
    """Show sample vocabulary words to understand the mapping"""
    print("📚 Sample vocabulary words in database:")
    print("-" * 50)
    
    result = supabase.table('vocabulary').select('id, language_a_word, language_b_translation').limit(limit).execute()
    
    if result.data:
        for vocab in result.data:
            print(f"ID {vocab['id']}: {vocab['language_a_word']} → {vocab['language_b_translation']}")
    else:
        print("No vocabulary found!")
    
    print("-" * 50)

def migrate_simple_word_mapping():
    """Simple migration that just maps word IDs"""
    print("🚀 Starting SIMPLE word mapping migration...")
    print("=" * 60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Show sample vocabulary first
    show_vocabulary_sample(supabase)
    
    # Path to the consolidated CSV results
    csv_file = 'consolidated_results/final_enhanced_french_similarities.csv'
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    # Track unique relationships to avoid duplicates
    unique_relationships = set()
    processed_count = 0
    skipped_count = 0
    error_count = 0
    total_relationships = 0
    
    print(f"\n📁 Reading similarities from: {csv_file}")
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    target_word = row['target_word'].strip().lower()
                    similar_words_str = row['similar_words']
                    
                    if not target_word or not similar_words_str:
                        continue
                    
                    # Get target word ID from existing vocabulary table
                    try:
                        target_id = get_vocabulary_word_id(supabase, target_word)
                        print(f"📍 Target word: {target_word} → ID {target_id}")
                    except ValueError:
                        print(f"⚠️  Skipping target word not in vocabulary: {target_word}")
                        skipped_count += 1
                        continue
                    
                    # Parse similar words
                    similar_words = [w.strip().lower() for w in similar_words_str.split(',') if w.strip()]
                    
                    # Create simple relationships
                    for similar_word in similar_words:
                        try:
                            similar_id = get_vocabulary_word_id(supabase, similar_word)
                            print(f"   🔗 Similar: {similar_word} → ID {similar_id}")
                            
                            # Create unique key for relationship (avoid duplicates)
                            source_id = min(target_id, similar_id)
                            target_id_rel = max(target_id, similar_id)
                            
                            relationship_key = f"{source_id}-{target_id_rel}"
                            
                            # Only add if not already processed
                            if relationship_key not in unique_relationships:
                                similarity_data = {
                                    'source_word_id': source_id,
                                    'target_word_id': target_id_rel,
                                    'similarity_score': 0.85,  # Default score
                                    'rule_types': ['similar'],  # Default rule type
                                    'algorithm_version': 'simple_v1'
                                }
                                
                                unique_relationships.add(relationship_key)
                                total_relationships += 1
                                
                                # Insert immediately
                                try:
                                    result = supabase.table('word_similarities').upsert(
                                        similarity_data,
                                        on_conflict='source_word_id,target_word_id,algorithm_version'
                                    ).execute()
                                    
                                    print(f"   ✅ Created relationship: {source_id} → {target_id_rel}")
                                        
                                except Exception as e:
                                    print(f"   ❌ Error inserting relationship: {e}")
                                    error_count += 1
                            
                        except ValueError:
                            print(f"   ⚠️  Skipping similar word not in vocabulary: {similar_word}")
                            skipped_count += 1
                            continue
                    
                    processed_count += 1
                    print(f"📊 Processed {processed_count} target words, {total_relationships} relationships\n")
                    
                    # Stop after processing a few examples to see the pattern
                    if processed_count >= 5:
                        print("🛑 Stopping after 5 examples to show the mapping pattern...")
                        break
                            
                except Exception as e:
                    print(f"❌ Error processing row {processed_count}: {e}")
                    error_count += 1
                    continue
        
        print("\n" + "=" * 60)
        print("🎉 Simple migration completed!")
        print(f"📊 Summary:")
        print(f"   ✅ Processed {processed_count} target words")
        print(f"   ⚠️  Skipped {skipped_count} words not in vocabulary")
        print(f"   ❌ Errors: {error_count}")
        print(f"   🔗 Total unique relationships created: {total_relationships}")
        
        # Verify migration results
        print(f"\n🔍 Verifying migration results...")
        verify_result = supabase.table('word_similarities').select('*', count='exact').execute()
        if verify_result.count:
            print(f"   📈 Total similarity relationships in database: {verify_result.count}")
            
            # Show some example relationships
            sample_result = supabase.table('word_similarities').select(`
                source_word_id,
                target_word_id,
                vocabulary!source_word_id(language_a_word),
                vocabulary!target_word_id(language_a_word)
            `).limit(5).execute()
            
            if sample_result.data:
                print(f"\n📝 Sample relationships created:")
                for rel in sample_result.data:
                    source_word = rel['vocabulary']['language_a_word'] if rel['vocabulary'] else 'Unknown'
                    target_vocab = rel.get('vocabulary', {})
                    target_word = target_vocab.get('language_a_word', 'Unknown') if target_vocab else 'Unknown'
                    print(f"   {source_word} (ID {rel['source_word_id']}) ↔ {target_word} (ID {rel['target_word_id']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Fatal error during migration: {e}")
        return False

if __name__ == "__main__":
    success = migrate_simple_word_mapping()
    if success:
        print("\n🚀 Ready to continue with full migration!")
        print("💡 This script shows how the mapping works. Run the full version to process all data.")
    else:
        print("\n🔧 Please fix errors before proceeding.")
