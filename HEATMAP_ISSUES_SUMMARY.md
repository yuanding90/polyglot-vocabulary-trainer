# Vocabulary Heatmap Issues Summary

## Current Status: BROKEN - No Colors Showing

### Primary Problem
The vocabulary heatmap is displaying 14,975 French words but showing **all grey colors** instead of the expected mastery level colors (Learning/Reviewing/Mastered/Graduated/Leech).

### Evidence of User Progress vs Heatmap Mismatch

**Dashboard Metrics Show Significant Progress:**
```
Metrics calculation debug: {totalWords: 494, totalProgress: 494, leeches: 37, learning: 21, strengthening: 145, …}
Metrics calculation debug: {totalWords: 156, totalProgress: 156, leeches: 17, learning: 25, strengthening: 31, …}
Metrics calculation debug: {totalWords: 360, totalProgress: 360, leeches: 11, learning: 132, strengthening: 32, …}
```

**Heatmap API Returns Zero Progress:**
```
✅ Dashboard: Heatmap data received: {totalWords: 14975, wordsWithProgress: 0, wordsWithoutProgress: 14975, sampleData: Array(3)}
```

## Root Cause Analysis

### 1. Server Connection Issues
- **Problem**: Next.js development server not running consistently
- **Evidence**: Terminal shows multiple failed attempts to start server
- **Impact**: API debugging output not visible, making troubleshooting difficult

### 2. User Progress Data Mismatch
- **Problem**: API fetches ALL French vocabulary (14,975 words) but progress lookup fails
- **Root Cause**: Progress data is stored per `deck_id`, but API was not properly filtering by French deck IDs
- **Fix Attempted**: Modified API to filter progress by `deck_id IN (frenchDeckIds)` AND `word_id IN (vocabularyIds)`

### 3. Authentication Issues
- **Problem**: API returning 401 Unauthorized errors
- **Evidence**: Server logs show `GET /api/vocabulary-heatmap 401 in 949ms`
- **Impact**: API calls failing, no data returned

### 4. Data Mapping Problems
- **Problem**: Lexique frequency mapping may not be properly populated
- **Evidence**: API falls back to using `item.id` as frequency rank when mapping fails
- **Impact**: Heatmap may not show words in correct frequency order

## Technical Architecture Issues

### API Endpoint: `/api/vocabulary-heatmap`
**File**: `src/app/api/vocabulary-heatmap/route.ts`

**Current Flow:**
1. ✅ Fetch 16 French deck IDs from `vocabulary_decks` table
2. ✅ Loop through each deck to get vocabulary from `deck_vocabulary` table  
3. ✅ Fetch vocabulary details from `vocabulary` table (14,975 words)
4. ❌ **FAILING**: Fetch user progress from `user_progress` table
5. ❌ **FAILING**: Map progress to vocabulary by frequency position
6. ✅ Return data structure to frontend

**User Progress Query Issues:**
```typescript
// Current query - may be failing
const { data: progressResult, error: progressError } = await supabaseAdmin
  .from('user_progress')
  .select(`word_id, deck_id, interval, repetitions, again_count, next_review_date`)
  .eq('user_id', userId)
  .in('deck_id', frenchDeckIds)  // Filter by French decks
  .in('word_id', vocabularyIds)  // Filter by French vocabulary
```

### Frontend Component: `VocabularyHeatmap.tsx`
**File**: `src/components/VocabularyHeatmap.tsx`

**Current Status:**
- ✅ Canvas-based rendering working
- ✅ Layout calculation for 14,975 words working  
- ✅ Color mapping logic implemented
- ❌ **ISSUE**: Receiving all grey data from API

## Specific Technical Problems

### 1. Server Startup Issues
```bash
npm run dev
# Error: Could not read package.json: Error: ENOENT: no such file or directory
# Working directory issues - commands run from wrong directory
```

### 2. API Authentication
```bash
GET /api/vocabulary-heatmap 401 in 949ms
# JWT token verification failing
# Service role client configuration issues
```

### 3. Data Query Problems
- **Vocabulary Query**: Working (14,975 words fetched)
- **User Progress Query**: Failing (0 words with progress)
- **Frequency Mapping**: May be failing (fallback to ID-based ranking)

### 4. Database Schema Mismatches
- **Progress Storage**: User progress stored with specific `deck_id` values
- **API Logic**: Fetching ALL French vocabulary but not matching to specific deck contexts
- **Mapping Tables**: `french_lexique_words` and `french_vocabulary_lexique_mapping` may not be properly populated

## Immediate Action Items

### 1. Fix Server Connection
- [ ] Start Next.js development server properly
- [ ] Verify server is running on correct port (3001)
- [ ] Test API endpoint accessibility

### 2. Debug User Progress Query
- [ ] Add comprehensive logging to API endpoint
- [ ] Verify `user_progress` table structure and data
- [ ] Test progress query with known user ID and deck IDs
- [ ] Check if progress data exists for French decks specifically

### 3. Verify Authentication
- [ ] Fix JWT token verification in API
- [ ] Ensure service role client has proper permissions
- [ ] Test API endpoint with valid authentication

### 4. Validate Data Flow
- [ ] Confirm French deck IDs are correct
- [ ] Verify vocabulary IDs match between decks and progress
- [ ] Test frequency mapping data availability
- [ ] Validate mastery level calculation logic

## Expected vs Actual Behavior

### Expected:
- Heatmap shows 14,975 French words in frequency order
- Words with user progress display appropriate colors:
  - 🔴 Red: Leeches (again_count >= 3)
  - 🟠 Orange: Learning (interval < 7 days)
  - 🟡 Yellow: Reviewing (interval 7-30 days)
  - 🟢 Green: Strengthening (interval 30-90 days)
  - 🔵 Blue: Mastered (interval > 90 days)
  - ⚫ Black: Graduated (very high interval)
- Words without progress display light grey

### Actual:
- Heatmap shows 14,975 French words
- ALL words display light grey (no progress colors)
- API reports 0 words with progress despite dashboard showing significant progress

## Files Involved

### Backend:
- `src/app/api/vocabulary-heatmap/route.ts` - Main API endpoint
- `src/lib/session-queues.ts` - SRS mastery level logic
- `src/lib/supabase.ts` - Database client configuration

### Frontend:
- `src/components/VocabularyHeatmap.tsx` - Canvas heatmap component
- `src/app/dashboard/page.tsx` - Dashboard integration

### Database:
- `user_progress` table - User study progress
- `vocabulary_decks` table - Deck definitions
- `deck_vocabulary` table - Vocabulary-deck relationships
- `vocabulary` table - Word definitions
- `french_lexique_words` table - Frequency rankings
- `french_vocabulary_lexique_mapping` table - Vocabulary-frequency mapping

## Next Steps Priority

1. **URGENT**: Fix server startup and API authentication
2. **HIGH**: Debug user progress query to find why 0 words have progress
3. **MEDIUM**: Verify frequency mapping data is properly populated
4. **LOW**: Optimize performance and add error handling

---

**Last Updated**: January 6, 2025
**Status**: 🔴 CRITICAL - Heatmap not functional
**Blocking Issue**: User progress data not being retrieved by API
