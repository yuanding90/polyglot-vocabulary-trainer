#!/usr/bin/env python3
"""
Check all tables in the Supabase database and their structure.
"""

import sys
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def check_all_supabase_tables():
    """Check all tables in the Supabase database"""
    print("🔍 Checking ALL tables in Supabase database...")
    print("=" * 80)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Get all tables by trying to query common table names
        # Note: Supabase doesn't have a direct way to list all tables via the client
        # So we'll check the tables we know exist
        
        tables_to_check = [
            'vocabulary',
            'vocabulary_decks', 
            'deck_vocabulary',
            'user_progress',
            'study_sessions',
            'rating_history',
            'daily_summary',
            'word_similarities'
        ]
        
        existing_tables = []
        
        for table_name in tables_to_check:
            try:
                # Try to get a sample from each table
                result = supabase.table(table_name).select('*').limit(1).execute()
                existing_tables.append(table_name)
                print(f"✅ {table_name} - EXISTS")
                
                # Get table info
                count_result = supabase.table(table_name).select('*', count='exact').execute()
                total_count = count_result.count if count_result.count else 0
                print(f"   📊 Total records: {total_count:,}")
                
                # Show sample data structure if available
                if result.data:
                    sample_record = result.data[0]
                    print(f"   📝 Sample columns: {list(sample_record.keys())}")
                    
                    # Show sample data for key tables
                    if table_name == 'vocabulary' and sample_record:
                        print(f"   🔍 Sample: ID {sample_record.get('id')} - '{sample_record.get('language_a_word')}' → '{sample_record.get('language_b_translation')}'")
                    elif table_name == 'vocabulary_decks' and sample_record:
                        print(f"   🔍 Sample: {sample_record.get('name')} ({sample_record.get('language_a_code')} → {sample_record.get('language_b_code')})")
                    elif table_name == 'word_similarities' and sample_record:
                        print(f"   🔍 Sample: {sample_record.get('source_word_id')} → {sample_record.get('target_word_id')} (score: {sample_record.get('similarity_score')})")
                
                print()
                
            except Exception as e:
                print(f"❌ {table_name} - NOT FOUND or ERROR: {e}")
                print()
        
        print("=" * 80)
        print(f"📊 SUMMARY:")
        print(f"   • Total tables found: {len(existing_tables)}")
        print(f"   • Tables: {', '.join(existing_tables)}")
        
        # Get detailed info about key tables
        print(f"\n🔍 DETAILED TABLE ANALYSIS:")
        print("=" * 80)
        
        # Vocabulary table
        if 'vocabulary' in existing_tables:
            print(f"\n📚 VOCABULARY TABLE:")
            vocab_result = supabase.table('vocabulary').select('*', count='exact').execute()
            print(f"   • Total vocabulary entries: {vocab_result.count:,}")
            
            # Get sample vocabulary entries
            sample_vocab = supabase.table('vocabulary').select('id, language_a_word, language_b_translation').limit(5).execute()
            if sample_vocab.data:
                print(f"   • Sample entries:")
                for vocab in sample_vocab.data:
                    print(f"     - ID {vocab['id']}: {vocab['language_a_word']} → {vocab['language_b_translation']}")
        
        # Vocabulary decks table
        if 'vocabulary_decks' in existing_tables:
            print(f"\n📖 VOCABULARY_DECKS TABLE:")
            decks_result = supabase.table('vocabulary_decks').select('*', count='exact').execute()
            print(f"   • Total decks: {decks_result.count}")
            
            # Get sample decks
            sample_decks = supabase.table('vocabulary_decks').select('id, name, language_a_code, language_b_code, total_words').limit(10).execute()
            if sample_decks.data:
                print(f"   • Sample decks:")
                for deck in sample_decks.data:
                    print(f"     - {deck['name']}: {deck['language_a_code']} → {deck['language_b_code']} ({deck['total_words']} words)")
        
        # Deck vocabulary relationships
        if 'deck_vocabulary' in existing_tables:
            print(f"\n🔗 DECK_VOCABULARY TABLE:")
            dv_result = supabase.table('deck_vocabulary').select('*', count='exact').execute()
            print(f"   • Total deck-vocabulary relationships: {dv_result.count:,}")
        
        # User progress
        if 'user_progress' in existing_tables:
            print(f"\n👤 USER_PROGRESS TABLE:")
            up_result = supabase.table('user_progress').select('*', count='exact').execute()
            print(f"   • Total user progress records: {up_result.count:,}")
        
        # Study sessions
        if 'study_sessions' in existing_tables:
            print(f"\n📊 STUDY_SESSIONS TABLE:")
            ss_result = supabase.table('study_sessions').select('*', count='exact').execute()
            print(f"   • Total study sessions: {ss_result.count:,}")
        
        # Rating history
        if 'rating_history' in existing_tables:
            print(f"\n⭐ RATING_HISTORY TABLE:")
            rh_result = supabase.table('rating_history').select('*', count='exact').execute()
            print(f"   • Total rating records: {rh_result.count:,}")
        
        # Daily summary
        if 'daily_summary' in existing_tables:
            print(f"\n📅 DAILY_SUMMARY TABLE:")
            ds_result = supabase.table('daily_summary').select('*', count='exact').execute()
            print(f"   • Total daily summaries: {ds_result.count:,}")
        
        # Word similarities (our new table)
        if 'word_similarities' in existing_tables:
            print(f"\n🔍 WORD_SIMILARITIES TABLE (NEW):")
            ws_result = supabase.table('word_similarities').select('*', count='exact').execute()
            print(f"   • Total similarity relationships: {ws_result.count:,}")
            
            if ws_result.count > 0:
                # Show sample similarities
                sample_similarities = supabase.table('word_similarities').select('source_word_id, target_word_id, similarity_score, algorithm_version').limit(5).execute()
                if sample_similarities.data:
                    print(f"   • Sample relationships:")
                    for sim in sample_similarities.data:
                        print(f"     - {sim['source_word_id']} → {sim['target_word_id']} (score: {sim['similarity_score']}, algo: {sim['algorithm_version']})")
        
        return existing_tables
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return []

if __name__ == "__main__":
    tables = check_all_supabase_tables()
    if tables:
        print(f"\n🎯 Found {len(tables)} tables in your Supabase database!")
    else:
        print(f"\n⚠️  No tables found or error occurred.")
