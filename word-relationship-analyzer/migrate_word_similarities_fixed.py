#!/usr/bin/env python3
"""
Fixed migration script for word similarities.
Handles duplicate relationships and batch insertion properly.
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
    result = supabase.table('vocabulary').select('id').eq(
        'language_a_word', word.lower()
    ).execute()
    
    if result.data:
        return result.data[0]['id']
    else:
        raise ValueError(f"Word not found in vocabulary: {word}")

def parse_rule_types(rule_types_str: str) -> list:
    """Parse rule types from CSV string"""
    if not rule_types_str or rule_types_str.strip() == '':
        return []
    
    # Clean up rule types
    rules = []
    for rule in rule_types_str.split(','):
        rule = rule.strip()
        if rule:
            # Convert to standardized format
            if 'Rule5a' in rule or 'Skeleton' in rule:
                rules.append('perfect_consonant_skeleton')
            elif 'Rule5b' in rule or 'Structural' in rule:
                rules.append('deep_structural_overlap')
            elif 'Rule1' in rule or 'Accent' in rule:
                rules.append('accent_confusion')
            elif 'Rule2' in rule or 'Near' in rule:
                rules.append('near_miss')
            elif 'Rule3' in rule or 'Jumble' in rule:
                rules.append('internal_jumble')
            elif 'Rule4' in rule or 'Shell' in rule:
                rules.append('shell_match')
            else:
                rules.append(rule.lower().replace(' ', '_'))
    
    return rules

def calculate_similarity_score(rule_types: list, similarity_count: int) -> float:
    """Calculate similarity score based on rule types and count"""
    base_score = 0.75  # Default base score
    
    # Adjust score based on rule types
    if 'perfect_consonant_skeleton' in rule_types:
        base_score = 0.95
    elif 'deep_structural_overlap' in rule_types:
        base_score = 0.90
    elif 'accent_confusion' in rule_types:
        base_score = 0.85
    elif 'near_miss' in rule_types:
        base_score = 0.80
    elif 'internal_jumble' in rule_types:
        base_score = 0.75
    elif 'shell_match' in rule_types:
        base_score = 0.70
    
    # Adjust based on similarity count
    if similarity_count > 3:
        base_score += 0.05
    elif similarity_count > 1:
        base_score += 0.02
    
    return min(base_score, 1.0)

def migrate_similarities_fixed():
    """Fixed migration that handles duplicates properly"""
    print("🚀 Starting FIXED word similarities migration...")
    print("=" * 60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Path to the consolidated CSV results
    csv_file = 'consolidated_results/final_enhanced_french_similarities.csv'
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    # Use a set to track unique relationships and avoid duplicates
    unique_relationships = set()
    batch_size = 200  # Smaller batch size to avoid conflicts
    processed_count = 0
    skipped_count = 0
    error_count = 0
    total_relationships = 0
    
    print(f"📁 Reading similarities from: {csv_file}")
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    target_word = row['target_word'].strip().lower()
                    similar_words_str = row['similar_words']
                    similarity_count = int(row.get('similarity_count', 1))
                    rule_types_str = row.get('rule_types', '')
                    
                    if not target_word or not similar_words_str:
                        continue
                    
                    # Get target word ID from existing vocabulary table
                    try:
                        target_id = get_vocabulary_word_id(supabase, target_word)
                    except ValueError:
                        print(f"⚠️  Skipping target word not in vocabulary: {target_word}")
                        skipped_count += 1
                        continue
                    
                    rule_types = parse_rule_types(rule_types_str)
                    similarity_score = calculate_similarity_score(rule_types, similarity_count)
                    
                    # Parse similar words
                    similar_words = [w.strip().lower() for w in similar_words_str.split(',') if w.strip()]
                    
                    # Create similarity relationships (only forward direction to avoid duplicates)
                    for similar_word in similar_words:
                        try:
                            similar_id = get_vocabulary_word_id(supabase, similar_word)
                            
                            # Create unique key for relationship
                            # Use smaller ID first to ensure consistency
                            source_id = min(target_id, similar_id)
                            target_id_rel = max(target_id, similar_id)
                            
                            relationship_key = f"{source_id}-{target_id_rel}-enhanced_v1"
                            
                            # Only add if not already in our set
                            if relationship_key not in unique_relationships:
                                similarity_data = {
                                    'source_word_id': source_id,
                                    'target_word_id': target_id_rel,
                                    'similarity_score': similarity_score,
                                    'rule_types': rule_types,
                                    'algorithm_version': 'enhanced_v1'
                                }
                                
                                unique_relationships.add(relationship_key)
                                total_relationships += 1
                                
                                # Insert immediately to avoid batch conflicts
                                try:
                                    result = supabase.table('word_similarities').upsert(
                                        similarity_data,
                                        on_conflict='source_word_id,target_word_id,algorithm_version'
                                    ).execute()
                                    
                                    if total_relationships % 100 == 0:
                                        print(f"✅ Inserted {total_relationships} relationships...")
                                        
                                except Exception as e:
                                    print(f"❌ Error inserting relationship {source_id}->{target_id_rel}: {e}")
                                    error_count += 1
                            
                        except ValueError:
                            print(f"⚠️  Skipping similar word not in vocabulary: {similar_word}")
                            skipped_count += 1
                            continue
                    
                    processed_count += 1
                    
                    # Progress update
                    if processed_count % 50 == 0:
                        print(f"📊 Processed {processed_count} target words, {total_relationships} relationships...")
                            
                except Exception as e:
                    print(f"❌ Error processing row {processed_count}: {e}")
                    error_count += 1
                    continue
        
        print("\n" + "=" * 60)
        print("🎉 Migration completed!")
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
        
        return True
        
    except Exception as e:
        print(f"❌ Fatal error during migration: {e}")
        return False

if __name__ == "__main__":
    success = migrate_similarities_fixed()
    if success:
        print("\n🚀 Ready for Phase 3: Service Layer!")
    else:
        print("\n🔧 Please fix errors before proceeding to Phase 3.")
