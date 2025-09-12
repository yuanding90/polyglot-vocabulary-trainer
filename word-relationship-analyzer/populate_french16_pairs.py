#!/usr/bin/env python3
"""
Populate word_similarities with unique pairs for the 16 French→English decks only.
- Uses simplified schema: source_word_id, target_word_id only
- Idempotent: canonicalize pairs and upsert with unique constraint
- Scope-restricted: only words that exist in the 16 French decks
"""

import csv
import os
from typing import Dict, Set, Tuple, List
from supabase import create_client

SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"
CSV_PATH = 'consolidated_results/final_enhanced_french_similarities.csv'

FRENCH_DECK_NAMES = [
    "12. French 01", "13. French 02", "14. French 03", "15. French 04",
    "16. French 05", "17. French 06", "18. French 07", "19. French 08",
    "20. French 09", "21. French 10", "22. French 11", "23. French 12",
    "24. French 13", "25. French 14", "26. French 15", "27. French 16"
]


def get_french_deck_ids(client) -> List[str]:
    res = client.table('vocabulary_decks').select('id,name').in_('name', FRENCH_DECK_NAMES).execute()
    if not res.data:
        return []
    return [r['id'] for r in res.data]


def get_vocab_ids_for_decks(client, deck_ids: List[str]) -> Set[int]:
    vocab_ids: Set[int] = set()
    page_size = 2000
    for deck_id in deck_ids:
        offset = 0
        while True:
            r = client.table('deck_vocabulary').select('vocabulary_id').eq('deck_id', deck_id).range(offset, offset + page_size - 1).execute()
            rows = r.data or []
            if not rows:
                break
            for row in rows:
                vid = row.get('vocabulary_id')
                if vid is not None:
                    vocab_ids.add(vid)
            if len(rows) < page_size:
                break
            offset += page_size
    return vocab_ids


def build_word_to_id_map(client, vocab_ids: Set[int]) -> Dict[str, int]:
    mapping: Dict[str, int] = {}
    ids_list = list(vocab_ids)
    for i in range(0, len(ids_list), 1000):
        chunk = ids_list[i:i+1000]
        r = client.table('vocabulary').select('id,language_a_word').in_('id', chunk).execute()
        for row in r.data or []:
            w = (row['language_a_word'] or '').strip().lower()
            if w and row['id'] is not None:
                mapping[w] = row['id']
    return mapping


def read_unique_pairs_from_csv(word_to_id: Dict[str, int]) -> Set[Tuple[int, int]]:
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    unique_pairs: Set[Tuple[int, int]] = set()
    rows = 0
    skipped_targets = 0
    skipped_similars = 0

    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows += 1
            t = (row.get('target_word') or '').strip().lower()
            s_str = row.get('similar_words') or ''
            if not t or not s_str:
                continue
            tid = word_to_id.get(t)
            if not tid:
                skipped_targets += 1
                continue
            for s in [w.strip().lower() for w in s_str.split(',') if w.strip()]:
                sid = word_to_id.get(s)
                if not sid or sid == tid:
                    if not sid:
                        skipped_similars += 1
                    continue
                a, b = (tid, sid) if tid < sid else (sid, tid)
                unique_pairs.add((a, b))

    print({
        'csv_rows': rows,
        'unique_pairs_computed': len(unique_pairs),
        'skipped_targets_not_in_decks': skipped_targets,
        'skipped_similars_not_in_decks': skipped_similars,
    })
    return unique_pairs


def chunked(iterable: List[Tuple[int, int]], size: int) -> List[List[Tuple[int, int]]]:
    return [iterable[i:i+size] for i in range(0, len(iterable), size)]


def upsert_pairs(client, pairs: Set[Tuple[int, int]], batch_size: int = 1000) -> int:
    inserted = 0
    pair_list = list(pairs)
    for batch in chunked(pair_list, batch_size):
        # Insert both directions for each pair
        payload = []
        for a, b in batch:
            payload.append({'source_word_id': a, 'target_word_id': b})
            payload.append({'source_word_id': b, 'target_word_id': a})
        try:
            client.table('word_similarities').upsert(payload, on_conflict='source_word_id,target_word_id').execute()
            inserted += len(payload)
            print(f"✅ Upserted {inserted}/{len(pair_list)*2}")
        except Exception as e:
            print(f"❌ Upsert error: {e}")
    return inserted


def main():
    print("🚀 Populating word_similarities for 16 French decks (unique pairs)...")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    deck_ids = get_french_deck_ids(client)
    print(f"Decks found: {len(deck_ids)}")
    vocab_ids = get_vocab_ids_for_decks(client, deck_ids)
    print(f"Distinct vocabulary IDs in decks: {len(vocab_ids)}")

    word_to_id = build_word_to_id_map(client, vocab_ids)
    print(f"Word→ID mapping size: {len(word_to_id)}")

    pairs = read_unique_pairs_from_csv(word_to_id)
    print(f"Unique pairs to insert: {len(pairs)}")

    inserted = upsert_pairs(client, pairs, batch_size=1000)
    print(f"Inserted (attempted): {inserted}")

    # Verify final count
    res = client.table('word_similarities').select('*', count='exact').execute()
    print(f"📈 word_similarities row count (total): {res.count}")


if __name__ == '__main__':
    main()
