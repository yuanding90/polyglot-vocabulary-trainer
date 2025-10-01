# Flash Card Issue Analysis & Resolution

## Problem Description
Review sessions were experiencing a brief flash/reveal of the back face of flash cards when advancing to subsequent words. The flash occurred on word transitions after the first card, making the answer briefly visible before the card properly showed the front face.

## Root Cause Analysis

### What Didn't Work (Overengineering Attempts)
1. **Flip suppression timers** - Created timing races and made the issue worse
2. **Lazy mounting the back face** - Still flashed during first paint
3. **CSS hardening** (visibility hidden, backface-visibility) - Didn't eliminate the issue
4. **No-animate guards** - Still flashed
5. **Synchronous flushSync resets** - Still flashed
6. **Always mounting both faces** - Still flashed

### The Real Problem
The issue was caused by the `key` prop on the `ReviewCard` component:

```jsx
// PROBLEMATIC (caused flash)
<ReviewCard 
  key={`${currentWordData?.id || 'no-word'}-${cardType}`}
  word={currentWordData}
  ...
/>
```

This `key` prop forced **complete component remounting** on every word change, which:
- Destroyed the CSS transition state
- Created a brief moment where the new component rendered with default state
- Caused the back face to flash before React applied the `showAnswer` prop

## Solution

### Simple Fix
Remove the `key` prop entirely to allow the component to update in place instead of remounting:

```jsx
// WORKING (no flash)
<ReviewCard 
  word={currentWordData}
  cardType={cardType}
  showAnswer={showAnswer}
  ...
/>
```

### Why This Works
- Component updates in place rather than being destroyed/recreated
- CSS transition state is preserved
- No timing gap between component creation and prop application
- Matches the stable behavior from previous working versions

## Key Lessons Learned

1. **React Key Props Can Cause Performance Issues**: Aggressive use of `key` props can force unnecessary remounting and break CSS transitions.

2. **Overengineering vs. Simple Solutions**: Multiple complex timing-based solutions failed, while a simple prop removal fixed the issue.

3. **Component Lifecycle Matters**: Understanding when React remounts vs. updates components is crucial for CSS-based animations.

4. **Version Comparison is Valuable**: Comparing working vs. broken versions revealed the exact difference causing the issue.

## Implementation Details

### Working Structure
```jsx
<div className={`flash-card ${showAnswer ? 'flipped' : ''}`} style={{ minHeight: '500px' }}>
  <div className="flash-card-inner">
    <div className="flash-card-front">...</div>
    <div className="flash-card-back">...</div>  // Always mounted
  </div>
</div>
```

### CSS Requirements
- Both faces always mounted
- CSS controls visibility via `flipped` class
- `backface-visibility: hidden` on both faces
- Transform-based flip animation

## Prevention
- Avoid using `key` props unless absolutely necessary for component identity
- When using `key` props, ensure they don't change unnecessarily
- Test CSS transitions thoroughly when modifying component mounting behavior
- Keep component structures simple and predictable for CSS animations

## Files Modified
- `src/app/study/page.tsx` - Removed `key` prop from `ReviewCard`
- `src/app/globals.css` - Enhanced CSS for better backface handling (kept for robustness)

## Date Resolved
September 30, 2025

## Testing
- Review sessions now work without flash on subsequent cards
- Recognition and production modes both stable
- CSS transitions work smoothly without timing issues
