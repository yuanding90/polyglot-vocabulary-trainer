#!/usr/bin/env python3
"""
Export French decks with AI content to local JSON files.
This script creates local copies of all French deck vocabulary and their AI Tutor content.
"""

import json
import os
from datetime import datetime
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def export_french_decks_with_ai():
    """Export all French deck vocabulary and AI content to local files"""
    print("🇫🇷 Exporting French decks with AI content...")
    print("=" * 60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Create export directory
    export_dir = "french_decks_export"
    os.makedirs(export_dir, exist_ok=True)
    
    try:
        # 1) Get French deck information
        french_deck_names = [
            "12. French 01", "13. French 02", "14. French 03", "15. French 04",
            "16. French 05", "17. French 06", "18. French 07", "19. French 08",
            "20. French 09", "21. French 10", "22. French 11", "23. French 12",
            "24. French 13", "25. French 14", "26. French 15", "27. French 16"
        ]
        
        decks_result = supabase.table('vocabulary_decks').select('*').in_('name', french_deck_names).execute()
        
        if not decks_result.data:
            print("❌ No French decks found!")
            return
        
        print(f"📚 Found {len(decks_result.data)} French decks")
        
        # 2) Export deck metadata
        deck_metadata = {
            "export_date": datetime.now().isoformat(),
            "total_decks": len(decks_result.data),
            "decks": decks_result.data
        }
        
        with open(f"{export_dir}/deck_metadata.json", 'w', encoding='utf-8') as f:
            json.dump(deck_metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported deck metadata to {export_dir}/deck_metadata.json")
        
        # 3) Get all vocabulary from French decks
        deck_ids = [deck['id'] for deck in decks_result.data]
        
        deck_vocab_result = supabase.table('deck_vocabulary').select('*').in_('deck_id', deck_ids).execute()
        
        if not deck_vocab_result.data:
            print("❌ No vocabulary found in French decks!")
            return
        
        print(f"📖 Found {len(deck_vocab_result.data)} vocabulary entries")
        
        # 4) Get all vocabulary details
        vocab_ids = list(set([entry['word_id'] for entry in deck_vocab_result.data]))
        
        vocab_result = supabase.table('vocabulary').select('*').in_('id', vocab_ids).execute()
        
        if not vocab_result.data:
            print("❌ No vocabulary details found!")
            return
        
        print(f"📝 Found {len(vocab_result.data)} vocabulary details")
        
        # Create vocabulary lookup
        vocab_by_id = {v['id']: v for v in vocab_result.data}
        
        # 5) Get AI content for all vocabulary
        ai_result = supabase.table('word_ai_content').select('*').in_('vocabulary_id', vocab_ids).eq('module_type', 'ai_tutor_pack').eq('status', 'ready').eq('is_latest', True).execute()
        
        if not ai_result.data:
            print("⚠️ No AI content found!")
            ai_content_by_id = {}
        else:
            print(f"🤖 Found {len(ai_result.data)} AI content entries")
            # Create AI content lookup (latest only)
            ai_content_by_id = {}
            for ai in ai_result.data:
                vocab_id = ai['vocabulary_id']
                if vocab_id not in ai_content_by_id:
                    ai_content_by_id[vocab_id] = ai
        
        # 6) Combine and export by deck
        deck_vocab_by_deck = {}
        for entry in deck_vocab_result.data:
            deck_id = entry['deck_id']
            if deck_id not in deck_vocab_by_deck:
                deck_vocab_by_deck[deck_id] = []
            deck_vocab_by_deck[deck_id].append(entry)
        
        # Create deck name lookup
        deck_by_id = {d['id']: d for d in decks_result.data}
        
        # Export each deck separately
        for deck_id, vocab_entries in deck_vocab_by_deck.items():
            deck_info = deck_by_id[deck_id]
            deck_name = deck_info['name']
            
            # Create deck export data
            deck_export = {
                "deck_info": deck_info,
                "vocabulary_count": len(vocab_entries),
                "words_with_ai": 0,
                "words_without_ai": 0,
                "vocabulary": []
            }
            
            for entry in vocab_entries:
                vocab_id = entry['word_id']
                vocab_detail = vocab_by_id.get(vocab_id, {})
                ai_content = ai_content_by_id.get(vocab_id, None)
                
                word_data = {
                    "vocabulary_id": vocab_id,
                    "deck_vocabulary_entry": entry,
                    "vocabulary_detail": vocab_detail,
                    "has_ai_content": ai_content is not None,
                    "ai_content": ai_content
                }
                
                deck_export["vocabulary"].append(word_data)
                
                if ai_content:
                    deck_export["words_with_ai"] += 1
                else:
                    deck_export["words_without_ai"] += 1
            
            # Save deck file
            safe_filename = deck_name.replace('.', '_').replace(' ', '_').replace(':', '_')
            filename = f"{export_dir}/{safe_filename}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(deck_export, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Exported {deck_name}: {deck_export['words_with_ai']}/{deck_export['vocabulary_count']} words have AI content")
        
        # 7) Create summary export
        summary = {
            "export_date": datetime.now().isoformat(),
            "total_decks": len(decks_result.data),
            "total_vocabulary_entries": len(deck_vocab_result.data),
            "total_unique_words": len(vocab_ids),
            "total_words_with_ai": len(ai_content_by_id),
            "total_words_without_ai": len(vocab_ids) - len(ai_content_by_id),
            "ai_coverage_percentage": round((len(ai_content_by_id) / len(vocab_ids)) * 100, 2) if vocab_ids else 0,
            "decks": []
        }
        
        for deck_id, vocab_entries in deck_vocab_by_deck.items():
            deck_info = deck_by_id[deck_id]
            words_with_ai = sum(1 for entry in vocab_entries if entry['word_id'] in ai_content_by_id)
            
            summary["decks"].append({
                "deck_id": deck_id,
                "deck_name": deck_info['name'],
                "total_words": len(vocab_entries),
                "words_with_ai": words_with_ai,
                "words_without_ai": len(vocab_entries) - words_with_ai,
                "ai_coverage_percentage": round((words_with_ai / len(vocab_entries)) * 100, 2) if vocab_entries else 0
            })
        
        with open(f"{export_dir}/export_summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported summary to {export_dir}/export_summary.json")
        
        # 8) Print final statistics
        print("\n" + "=" * 60)
        print("📊 EXPORT SUMMARY")
        print("=" * 60)
        print(f"📁 Export directory: {export_dir}/")
        print(f"📚 Total decks: {summary['total_decks']}")
        print(f"📖 Total vocabulary entries: {summary['total_vocabulary_entries']}")
        print(f"🔤 Total unique words: {summary['total_unique_words']}")
        print(f"🤖 Words with AI content: {summary['total_words_with_ai']}")
        print(f"❌ Words without AI content: {summary['total_words_without_ai']}")
        print(f"📈 AI coverage: {summary['ai_coverage_percentage']}%")
        print("\n📋 Files created:")
        print(f"   • deck_metadata.json - Deck information")
        print(f"   • export_summary.json - Overall statistics")
        for deck in summary["decks"]:
            safe_name = deck["deck_name"].replace('.', '_').replace(' ', '_').replace(':', '_')
            print(f"   • {safe_name}.json - {deck['deck_name']} vocabulary")
        
    except Exception as e:
        print(f"❌ Error during export: {str(e)}")
        raise

if __name__ == "__main__":
    export_french_decks_with_ai()
