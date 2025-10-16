# Overtalkerr Voice Prompts Reference

This document contains all voice prompts and error messages used in Overtalkerr, organized by scenario for easy review and tweaking.

---

## 🎯 Welcome & Help Messages

### Launch/Welcome
**When:** User opens the skill
```
Welcome to Overtalkerr! You can say things like, download the movie Jurassic World,
or download the upcoming TV show Robin Hood. You can also request specific seasons,
like download season 2 of Breaking Bad. What would you like to download?
```

### Help Intent
**When:** User asks for help
```
You can say things like: download the movie Jurassic World from 2015, or download
the upcoming TV show Robin Hood. You can also specify seasons for TV shows, like
download season 2 of Breaking Bad. What would you like to download?
```

### Fallback/Didn't Understand
**When:** User says something the system doesn't recognize
```
Sorry, I didn't understand that. You can say things like, download the movie
Jurassic World from 2015. What would you like to download?
```

### Goodbye
**When:** User says cancel, stop, or exit
```
Goodbye!
```

---

## 🔍 Search & Results

### Missing Title
**When:** User doesn't provide a title
```
Please tell me the title. For example, say download the movie Jurassic World from 2015.
```

### Search Result (First Match)
**When:** Found a match and presenting the first result

**With year:**
```
I found the [movie/TV show] [title], released in [year]. [Availability Status]. Is that the one you want?
```

**Without year:**
```
I found the [movie/TV show] [title]. [Availability Status]. Is that the one you want?
```

**Availability Status Messages:**
- Already available: `This is already in your library`
- Partially available: `This is partially in your library`
- Being downloaded: `This is currently being downloaded`
- Pending approval: `This has already been requested and is pending approval`
- Not yet released: `That hasn't been released yet`
- Not available: *(no additional message)*

**Special Handling for Unreleased Content:**
- If unreleased and not in library: Changes "released in [year]" to "releasing in [year]"
- Changes confirmation question from "Is that the one you want?" to "Would you like to request it anyway?"

### Next Alternative (After "No")
**When:** User says "no" and we show the next result

**With year:**
```
What about the [movie/TV show] [title], released in [year]?
```

**Without year:**
```
What about the [movie/TV show] [title]?
```

### No Results - With Year Filter
**When:** Search finds nothing with a specific year
```
I couldn't find any matches for '[title]' from [year]. Try rephrasing or removing the year filter.
```

### No Results - Without Year Filter
**When:** Search finds nothing (no year specified)
```
I couldn't find any matches for '[title]'. Try rephrasing or being more specific.
```

### No Results - But Found Results From Other Years
**When:** Search with year filter finds nothing, but results exist from other years
```
I couldn't find '[title]' from [year], but I found results from other years. Would you like to hear them?
```
**User says "Yes":** Present the first result from other years
**User says "No":** `Okay. Try searching again with a different year or without the year.`

### Partial Match Suggestion (Did You Mean)
**When:** Search returns results but none match closely enough (fuzzy matching filters them out)
```
I couldn't find '[title]'. Did you mean '[suggested_title]'?
```
**User says "Yes":** Present the suggested result
**User says "No":** `Okay. Try searching again with a different title.`

### Out of Alternatives
**When:** User says "no" but there are no more results
```
That's all I could find. Would you like to search for something else?
```

---

## ✅ Confirmation & Request Submission

### No Active Search
**When:** User says "yes" but there's no active search session
```
I don't have an active search. Please say a title to start a new download request.
```

### Run Out of Alternatives (Yes on empty)
**When:** Internal error - user confirms but index is out of range
```
I've run out of alternatives. Please start a new search.
```

### Missing Media ID
**When:** Can't determine the media ID from the result
```
Sorry, I couldn't determine the media ID. Please try a different title.
```

### Already in Library
**When:** User confirms but media is already fully available
```
[title] is already in your library! You can watch it now.
```

### Already Being Downloaded
**When:** User confirms but media is currently being processed
```
[title] is already being downloaded. It should be available soon!
```

### Already Requested (Pending)
**When:** User confirms but request is pending approval
```
[title] has already been requested and is waiting for approval.
```

### Partially Available (Information)
**When:** User confirms and some content exists (continues to allow request)
```
[title] is partially in your library. Some content may already be available.
```
*(Note: This message is informational; the request continues)*

### Request Successful - Movie (Already Released)
**When:** Request submitted successfully for a movie that's already released
```
Okay! I've requested [title]. It should be available soon.
```

### Request Successful - Movie (Not Yet Released)
**When:** Request submitted successfully for a movie that hasn't been released yet
```
Okay! I've requested [title]. It'll be downloaded once it's released, which we're expecting to be on [October 20th] (or [October 20th, 2026] if different year).
```

### Request Successful - TV Show with Season (Already Released)
**When:** Request submitted successfully for a specific TV season that's already released
```
Okay! I've requested season [number] of [title]. It should be available soon.
```

### Request Successful - TV Show with Season (Not Yet Released)
**When:** Request submitted successfully for a specific TV season that hasn't been released yet
```
Okay! I've requested season [number] of [title]. It'll be downloaded once it's released, which we're expecting to be on [October 20th] (or [October 20th, 2026] if different year).
```

### Already Requested (Backend Duplicate Detection)
**When:** Backend reports the request already exists
```
That media has already been requested!
```

---

## ⚠️ Error Messages

### Connection Error
**When:** Cannot connect to Overseerr/Jellyseerr/Ombi
```
Sorry, I couldn't connect to the media server. Please try again later.
```

### Connection Error (During Request)
**When:** Connection lost while submitting request
```
Sorry, I couldn't connect to the media server. Your request wasn't submitted.
```

### Authentication Error
**When:** API key is invalid or expired
```
Sorry, there's an authentication problem with the media server. Please contact the administrator.
```

### Search Error
**When:** Search API call fails (not connection or auth)
```
Sorry, I encountered an error searching for that title. Please try again.
```

### Request Creation Error
**When:** Request submission fails (not connection error)
```
Sorry, I couldn't create the request. Please try again later.
```

---

## 📝 Reprompts

Reprompts are used when the session stays open and the user doesn't respond:

- After welcome/help/fallback: `What would you like to download?`
- After presenting a search result: `Is that the one you want?`
- After presenting next alternative: `Is that the one?`
- After running out of results: `What would you like to download?`
- After missing title: `Please tell me the title. For example, say download the movie Jurassic World from 2015.`

---

## 💡 Suggested Improvements

### Implemented Features:
✅ **Year range flexibility**: Offers results from other years when year filter yields no results
✅ **Partial match suggestions**: "Did you mean [similar title]?" using fuzzy matching
✅ **Release date context**: "That hasn't been released yet. Would you like to request it anyway?"

### Potential Future Enhancements:
1. **More specific connection errors**: Distinguish between timeout, DNS failure, and refused connection
2. **Quality preferences**: Allow users to specify 4K, HD, etc.
3. **Request status check**: "What's the status of my request for [title]?"
4. **Cancel request**: "Cancel my request for [title]"
5. **Watchlist management**: "Add [title] to my watchlist"
6. **Recent additions**: "What's new in my library?"

### Tone Adjustments:
- Consider making error messages less apologetic for issues outside user control
- Add enthusiasm to successful requests: "Great choice!" or "You got it!"
- Provide more actionable next steps in error messages

---

## 🎬 Example Conversations

### Happy Path - Movie Request
```
User: "Download the movie Superman"
Alexa: "I found the movie Superman, released in 1978. Is that the one you want?"
User: "Yes"
Alexa: "Okay! I've requested Superman. It should be available soon."
```

### With Year Filter - No Results
```
User: "Download Superman from 1977"
Alexa: "I couldn't find any matches for 'Superman' from 1977. Try rephrasing or removing the year filter."
```

### Multiple Results - User Says No
```
User: "Download Robin Hood"
Alexa: "I found the movie Robin Hood, released in 2018. Is that the one you want?"
User: "No"
Alexa: "What about the movie Robin Hood, released in 2010?"
User: "No"
Alexa: "What about the TV show Robin Hood, released in 2006?"
User: "Yes"
Alexa: "Okay! I've requested Robin Hood. It should be available soon."
```

### TV Show with Season
```
User: "Download season 2 of Breaking Bad"
Alexa: "I found the TV show Breaking Bad, released in 2008. Is that the one you want?"
User: "Yes"
Alexa: "Okay! I've requested season 2 of Breaking Bad. It should be available soon."
```

### Already in Library
```
User: "Download The Godfather"
Alexa: "I found the movie The Godfather, released in 1972. This is already in your library. Is that the one you want?"
User: "Yes"
Alexa: "The Godfather is already in your library! You can watch it now."
```

### Year Filter with Alternate Years Available
```
User: "Download Superman from 1977"
Alexa: "I couldn't find 'Superman' from 1977, but I found results from other years. Would you like to hear them?"
User: "Yes"
Alexa: "I found the movie Superman, released in 1978. Is that the one you want?"
User: "Yes"
Alexa: "Okay! I've requested Superman. It should be available soon."
```

### Partial Match Suggestion (Typo/Speech Recognition Error)
```
User: "Download Jurrasic Park"
Alexa: "I couldn't find 'Jurrasic Park'. Did you mean 'Jurassic Park'?"
User: "Yes"
Alexa: "I found the movie Jurassic Park, released in 1993. Is that the one you want?"
User: "Yes"
Alexa: "Okay! I've requested Jurassic Park. It should be available soon."
```

### Unreleased Content
```
User: "Download Deadpool 3"
Alexa: "I found the movie Deadpool 3, releasing in 2024. That hasn't been released yet. Would you like to request it anyway?"
User: "Yes"
Alexa: "Okay! I've requested Deadpool 3. It'll be downloaded once it's released, which we're expecting to be on July 26th, 2024."
```

---

## 🔧 Technical Notes

### Voice Optimization Tips:
1. **Brevity**: Voice users have limited attention - keep messages under 2-3 sentences
2. **Natural speech**: Use contractions (I've, that's, you're) for more natural delivery
3. **Clear questions**: End prompts with clear yes/no questions when possible
4. **Avoid jargon**: Don't mention "media ID", "TMDB", "API", etc. to users
5. **Positive framing**: Focus on what can be done rather than what can't

### SSML Opportunities:
Consider adding SSML tags for better voice delivery:
- `<emphasis>` for title names
- `<break time="500ms"/>` after presenting information
- `<prosody rate="medium">` for consistent pacing

---

*Last Updated: 2025-10-17*
