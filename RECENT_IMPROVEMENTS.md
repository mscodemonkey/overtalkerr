# Recent Improvements - Natural Language & Quality Enhancements

This document summarizes the major improvements made to Overtalkerr's search and conversation features.

---

## 🎯 Natural Language Year Filtering

### What Changed
Overtalkerr now understands natural language year expressions, making searches feel more conversational and intuitive.

### Supported Expressions

| You Say | What It Searches |
|---------|------------------|
| "from 1978" | Exact year (1978) |
| "from the 70s" | 1970-1979 |
| "from the 1970s" | 1970-1979 |
| "from the 80's" | 1980-1989 |
| "this year" | Current year + last year (2-year buffer) |
| "last year" | Previous 2 years |
| "a couple of years ago" | Last 5 years |
| "a few years ago" | Last 10 years |
| "from the noughties" | 2000-2009 |
| "from the naughties" | 2000-2009 |
| "in the 10s" | 2010-2019 |
| "in the 20's" | 2020-2029 |

### Examples
```
"Download Superman from the 70s"
"Find movies from a couple of years ago"
"Get shows from the noughties"
"Download films from this year"
```

### Technical Details
- Added `parse_year_filter()` function in `unified_voice_handler.py`
- Updated `overseerr.pick_best()` to handle year range tuples instead of single years
- Added `format_year_range_for_speech()` for natural text-to-speech output
- Year ranges work inclusively (e.g., 1970-1979 includes both 1970 and 1979)

---

## 🗣️ Varied Date Phrasing

### What Changed
The voice assistant now varies how it talks about release dates, making conversations sound more natural and less robotic.

### Before
```
"I found the movie Superman, released in 1978"
"What about the movie Superman, released in 1987"
"How about the movie Superman, released in 2013"
```
*Repetitive and monotonous!*

### After
```
"I found the movie Superman from 1978"
"What about a movie from 1987, Superman"
"How about the 2013 movie Superman"
"This one? The movie Superman, that came out in 2006"
"Have I got it right this time? The movie Superman, released 1978"
```
*Natural and varied!*

### Technical Details
- Updated `build_speech_for_item()` to use randomized date phrasing
- Updated `build_speech_for_next()` with 6 varied opening phrases
- Different formats for released vs. unreleased content

---

## 🧹 Quality Filtering

### What Changed
Overtalkerr now automatically filters out low-quality search results (spam, test entries, incomplete data).

### What Gets Filtered
Results are removed if they meet ALL these criteria:
- **No votes** (voteCount = 0)
- **Low popularity** (< 1.0)
- **No poster image**

Or if they have:
- **Very short overview** (< 30 chars) AND no votes AND low popularity

### Example - Filtered Out
```json
{
  "title": "Superman",
  "overview": "A public toilet talks about its 'Superman'",
  "voteCount": 0,
  "popularity": 0.0946,
  "posterPath": null
}
```

### Example - Kept (Upcoming Blockbuster)
```json
{
  "title": "Jumanji 3",
  "overview": "The third film in the Jumanji reboot franchise. Plot TBA.",
  "voteCount": 0,
  "popularity": 5.6313,
  "posterPath": "/fgx9pr2vxBOFqI6aaEwnFYm5ygH.jpg"
}
```

### Technical Details
- Added `is_low_quality_result()` function in `enhanced_search.py`
- Integrated into `fuzzy_match_results()` pipeline
- Conservative filtering to avoid removing legitimate upcoming releases

---

## ✅ Simplified Yes/No Logic

### What Changed
Removed confusing "inverted logic" for items already in your library. Now consistently:
- **"Yes"** ALWAYS means "that's the one I want"
- **"No"** ALWAYS means "show me the next one"

### Before (Confusing!)
```
Assistant: "Superman from 1978 is in your library. Were you thinking of a different one?"
User: "No" → Meant "that's the one" (backwards!)
User: "Yes" → Showed next result (backwards!)
```

### After (Consistent!)
```
Assistant: "Superman from 1978 is already in your library, so you can watch it now. Is that the one you were thinking of?"
User: "Yes" → "In that case, enjoy the movie!" ✅
User: "No" → Shows next result ✅
```

### Technical Details
- Removed all `inverted_yes_no` flag logic
- Updated speech patterns to use consistent question format
- Simplified `handle_yes()` and `handle_no()` functions

---

## 📋 Files Modified

### Core Logic
- `unified_voice_handler.py` - Added year parsing, varied phrasing, simplified logic
- `overseerr.py` - Updated to handle year range tuples
- `enhanced_search.py` - Added quality filtering

### Documentation
- `docs/enhanced_search.md` - Added year filtering examples and table
- `VOICE_PROMPTS.md` - Updated with varied phrasing examples and year expressions
- `README.md` - Updated capabilities list

---

## 🧪 Testing

All features tested with comprehensive test suite:
- ✅ Year parsing (15 test cases, all passed)
- ✅ Year range filtering
- ✅ Quality filtering
- ✅ Varied speech phrasing

---

## 🚀 Usage Examples

### Natural Year Searches
```
"Download Superman from the 70s"
→ Searches 1970-1979

"Find movies from a couple of years ago"
→ Searches last 5 years

"Get shows from the noughties"
→ Searches 2000-2009
```

### Varied Conversations
```
User: "Download Superman"
Assistant: "I found a movie from 2025, Superman. Is that the one you want?"
User: "No"
Assistant: "What about the 2013 movie Superman?"
User: "No"
Assistant: "Have I got it right this time? The movie Superman, that came out in 1987?"
```

### Quality Filtering
Low-quality results (no votes, no poster, weird descriptions) are automatically hidden from search results.

---

## 🎉 Benefits

1. **More Natural Conversations** - Varied phrasing makes the assistant feel human
2. **Flexible Year Searches** - Say years naturally ("the 70s", "a couple years ago")
3. **Cleaner Results** - No more spam or low-quality results
4. **Less Confusion** - Consistent Yes/No logic throughout
5. **Better UX** - Users find what they want faster

---

**Last Updated:** 2025-10-17
