#!/usr/bin/env python3
"""
Migration script using ALL French vocabulary in the database, not just the 16 decks.
This will capture more French words and increase the success rate.
"""

import csv
import sys
import os
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def get_all_french_vocabulary(supabase):
    """Get ALL French vocabulary from the database"""
    print("🔍 Getting ALL French vocabulary from database...")
    print("=" * 60)
    
    try:
        # Get all vocabulary that could be French
        # Look for words with French characteristics (accents, common French patterns)
        french_patterns = ['é', 'è', 'ê', 'ë', 'à', 'â', 'ä', 'ç', 'î', 'ï', 'ô', 'ö', 'ù', 'û', 'ü', 'ÿ']
        
        # First, get a sample to understand the data
        sample_result = supabase.table('vocabulary').select('id, language_a_word, language_b_translation').limit(10000).execute()
        
        if not sample_result.data:
            print("❌ No vocabulary found!")
            return {}
        
        print(f"📊 Analyzing {len(sample_result.data)} vocabulary entries...")
        
        # Find French words (words with French accents/patterns)
        french_words = []
        for vocab in sample_result.data:
            word = vocab['language_a_word']
            if any(pattern in word for pattern in french_patterns):
                french_words.append(vocab)
        
        print(f"🇫🇷 Found {len(french_words)} words with French accents/patterns")
        
        # Create word-to-ID mapping for all French words
        word_to_id = {}
        for vocab in french_words:
            french_word = vocab['language_a_word'].lower().strip()
            word_to_id[french_word] = vocab['id']
        
        print(f"✅ Created mapping for {len(word_to_id)} French words")
        
        # Show sample mapping
        print(f"\n📝 Sample French word mappings:")
        sample_words = list(word_to_id.items())[:10]
        for word, vocab_id in sample_words:
            print(f"   '{word}' → ID {vocab_id}")
        
        return word_to_id
        
    except Exception as e:
        print(f"❌ Error getting French vocabulary: {e}")
        return {}

def migrate_all_french_similarities():
    """Migrate word similarities using ALL French vocabulary"""
    print("🚀 Starting ALL-FRENCH vocabulary similarity migration...")
    print("=" * 60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Step 1: Get all French vocabulary
    word_to_id = get_all_french_vocabulary(supabase)
    if not word_to_id:
        return False
    
    # Step 2: Process CSV similarities
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
                        skipped_count += 1
                        if skipped_count <= 10:  # Show first 10 skipped words
                            print(f"⚠️  Skipping target word not in French vocabulary: {target_word}")
                        continue
                    
                    target_id = word_to_id[target_word]
                    print(f"📍 Target: {target_word} → ID {target_id}")
                    
                    # Parse similar words
                    similar_words = [w.strip().lower() for w in similar_words_str.split(',') if w.strip()]
                    
                    # Create relationships for French words only
                    for similar_word in similar_words:
                        if similar_word not in word_to_id:
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
                                'algorithm_version': 'all_french_v1'
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
                    if processed_count >= 5:
                        print("🛑 Stopping after 5 examples to show the mapping pattern...")
                        break
                        
                except Exception as e:
                    print(f"❌ Error processing row {processed_count}: {e}")
                    error_count += 1
                    continue
        
        print("\n" + "=" * 60)
        print("🎉 All-French migration completed!")
        print(f"📊 Summary:")
        print(f"   ✅ Processed {processed_count} French target words")
        print(f"   ⚠️  Skipped {skipped_count} words not in French vocabulary")
        print(f"   ❌ Errors: {error_count}")
        print(f"   🔗 Total unique relationships created: {total_relationships}")
        
        # Calculate success rate
        success_rate = (processed_count / (processed_count + skipped_count) * 100) if (processed_count + skipped_count) > 0 else 0
        print(f"   📈 Success rate: {success_rate:.1f}%")
        
        # Verify migration results
        print(f"\n🔍 Verifying migration results...")
        verify_result = supabase.table('word_similarities').select('*', count='exact').eq('algorithm_version', 'all_french_v1').execute()
        if verify_result.count:
            print(f"   📈 Total French similarity relationships: {verify_result.count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fatal error during migration: {e}")
        return False

if __name__ == "__main__":
    success = migrate_all_french_similarities()
    if success:
        print("\n🚀 Ready to continue with full migration!")
        print("💡 This shows the improved success rate with all French vocabulary.")
        print("🔄 Run with full processing to migrate all French similarities.")
    else:
        print("\n🔧 Please fix errors before proceeding.")
