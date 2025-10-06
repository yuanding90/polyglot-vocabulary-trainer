# LexiqueData Ranking Mapping Analysis

**Strategy**: DIRECT_PLUS_NORMALIZATION
**Estimated Coverage**: 92.9%
**Direct Matches**: 898/1000 words

## SQL Migration

```sql
-- Migration: Add LexiqueData ranking to vocabulary table
-- Strategy: DIRECT_PLUS_NORMALIZATION

-- Add lexique_rank column to vocabulary table
ALTER TABLE vocabulary 
ADD COLUMN IF NOT EXISTS lexique_rank INTEGER;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_vocabulary_lexique_rank ON vocabulary(lexique_rank);

-- Add comment explaining the column
COMMENT ON COLUMN vocabulary.lexique_rank IS 'Frequency ranking from LexiqueData.txt (lower number = higher frequency)';

-- Example update statements (to be populated by mapping script):
-- UPDATE vocabulary SET lexique_rank = 2500 WHERE language_a_word = 'patrie';
-- UPDATE vocabulary SET lexique_rank = 1234 WHERE language_a_word = 'maison';

```

## Mapping Script Template

```python
#!/usr/bin/env python3
"""
LexiqueData Ranking Mapping Script
Strategy: DIRECT_PLUS_NORMALIZATION
"""

import sqlite3
import re
from typing import Dict, List, Tuple
from supabase import create_client, Client

class LexiqueRankingMapper:
    def __init__(self):
        self.supabase = create_client(supabase_url, supabase_key)
        self.lexique_data = {}
        self.conflicts = []
    
    def parse_lexique_file(self, file_path: str):
        """Parse LexiqueData.txt and extract rankings."""
        # Implementation here
        pass
    
    def fetch_vocabulary_from_supabase(self):
        """Fetch all French vocabulary from Supabase."""
        # Implementation here
        pass
    
    def apply_direct_mapping(self):
        """Apply direct word-to-word mapping."""
        # Implementation here
        pass
    
    def apply_normalization_mapping(self):
        """Apply normalized matching for remaining words."""
        # Implementation here
        pass
    
    def update_supabase_rankings(self, mappings: Dict[str, int]):
        """Update vocabulary table with lexique rankings."""
        # Implementation here
        pass
    
    def generate_conflict_report(self):
        """Generate report of mapping conflicts."""
        # Implementation here
        pass

if __name__ == "__main__":
    mapper = LexiqueRankingMapper()
    # Run mapping process
    pass

```
