# Siri Shortcuts Setup for Overtalkerr

Set up Overtalkerr to work with Siri on iOS/macOS using Shortcuts webhooks.

## Overview

Unlike Alexa and Google Assistant, Siri doesn't have a traditional "skill" system. Instead, we use **Siri Shortcuts** which are user-created automations that can:
- Accept voice input
- Call your Overtalkerr webhook
- Read the response back to you

This approach gives you full control and doesn't require App Store approval!

## Prerequisites

- iOS 13+ or macOS 12+ device
- Shortcuts app (pre-installed on iOS/macOS)
- Your Overtalkerr backend URL (must be HTTPS)

## Creating the Download Shortcut

### Step 1: Create New Shortcut

1. Open **Shortcuts** app
2. Tap **+** (New Shortcut)
3. Name it: "Download with Overtalkerr"

### Step 2: Get User Input

1. Tap **Add Action**
2. Search for "Ask for Input"
3. Configure:
   - Question: "What would you like to download?"
   - Input Type: Text
   - Default Answer: (leave empty)

### Step 3: (Optional) Get Year

1. Add another "Ask for Input" action
2. Configure:
   - Question: "What year? (optional)"
   - Input Type: Number
   - Allow Decimal Numbers: OFF

### Step 4: Build JSON Request

1. Add "Dictionary" action
2. Configure the dictionary:
   ```
   platform: siri
   userId: (your-user-id or device name)
   action: DownloadIntent
   parameters:
     - title: [Provided Input from Step 2]
     - year: [Provided Input from Step 3]
   ```

### Step 5: Call Webhook

1. Add "Get Contents of URL" action
2. Configure:
   - URL: `https://your-domain.com/voice`
   - Method: POST
   - Headers:
     - Content-Type: application/json
   - Request Body: JSON
   - JSON: [Dictionary from Step 4]

### Step 6: Parse Response

1. Add "Get Dictionary from Input" action
   - Input: Contents of URL

2. Add "Get Dictionary Value" action
   - Key: speech
   - Dictionary: Dictionary

### Step 7: Speak Response

1. Add "Speak Text" action
2. Input: Dictionary Value (speech)

### Step 8: (Optional) Handle Yes/No

For a more advanced setup, you can add:
1. "Ask for Input" with Yes/No
2. Conditional logic
3. Another webhook call to `/voice` with YesIntent or NoIntent

### Step 9: Add to Siri

1. Tap the settings icon (⋯)
2. Tap "Add to Siri"
3. Record phrase: "Download with Overtalkerr" or just "Overtalkerr"
4. Tap "Done"

## Quick Download Shortcut (Simplified)

For a simpler one-step version:

```
1. Ask for Input: "What to download?"
2. Get Contents of URL
   - URL: https://your-domain.com/voice
   - Method: POST
   - Body:
     {
       "platform": "siri",
       "userId": "siri-user",
       "action": "DownloadIntent",
       "title": [Provided Input],
       "parameters": {
         "MediaTitle": [Provided Input]
       }
     }
3. Get Dictionary Value: "speech"
4. Speak Text: [Dictionary Value]
```

## Advanced: Full Conversation Flow

### Main Shortcut: "Overtalkerr"

**Inputs:**
- Title (text)
- Year (optional number)
- Media Type (choose from list: Movie, TV Show)
- Season (optional number)

**Actions:**
1. Build JSON request
2. POST to `/voice` endpoint
3. Get response speech
4. Speak response
5. If response contains "Is that the one?":
   - Ask "Is this correct?" (Yes/No)
   - If Yes: Call Confirm Shortcut
   - If No: Call Next Shortcut

### Confirm Shortcut

```json
{
  "platform": "siri",
  "userId": "siri-user",
  "action": "AMAZON.YesIntent",
  "sessionId": "[Store from previous response]"
}
```

### Next Shortcut

```json
{
  "platform": "siri",
  "userId": "siri-user",
  "action": "AMAZON.NoIntent",
  "sessionId": "[Store from previous response]"
}
```

## Example Webhook Requests

### Download Movie

```json
{
  "platform": "siri",
  "userId": "iPhone-John",
  "action": "DownloadIntent",
  "title": "Jurassic World",
  "year": "2015",
  "mediaType": "movie"
}
```

### Download TV Show Season

```json
{
  "platform": "siri",
  "userId": "iPhone-John",
  "action": "DownloadIntent",
  "title": "Breaking Bad",
  "season": "2",
  "mediaType": "tv"
}
```

## Example Responses

Your Overtalkerr backend returns:

```json
{
  "speech": "I found the movie Jurassic World, released in 2015. Is that the one you want?",
  "text": "I found the movie Jurassic World, released in 2015. Is that the one you want?",
  "endSession": false,
  "reprompt": "Is that the one you want?"
}
```

## Sharing Shortcuts

Once you've created the perfect shortcut:

1. Tap **Share**
2. Choose method:
   - **iCloud Link**: Share URL with others
   - **Export File**: Save .shortcut file
   - **Add to Shared Album**: Share with family

## Pre-made Shortcuts

### Basic Download
[Download iCloud Link]
```
icloud.com/shortcuts/overtalkerr-basic
```

### Advanced with Conversation
[Download iCloud Link]
```
icloud.com/shortcuts/overtalkerr-full
```

## Automation Ideas

### Location-Based
"When I arrive home, ask me if I want to download anything"

### Time-Based
"Every Friday at 8 PM, remind me to check for new releases"

### NFC Tag
Place NFC tag on TV remote:
- Tap tag
- Triggers "What do you want to watch?"
- Downloads to Overseerr

## Troubleshooting

**Issue: "Could not connect to server"**
- Check your Overtalkerr URL is correct and HTTPS
- Verify your device has internet connection
- Test the URL in Safari first

**Issue: "Invalid response"**
- Check server logs for errors
- Verify JSON structure in webhook call
- Test with Postman/curl first

**Issue: Siri doesn't understand the phrase**
- Re-record the Siri phrase more clearly
- Try shorter phrase
- Avoid similar-sounding shortcuts

## Tips & Tricks

1. **Use Variables**: Store session IDs in shortcut variables for multi-turn conversations

2. **Error Handling**: Add "If" actions to check for error responses

3. **Notifications**: Add "Show Notification" action for silent confirmation

4. **Home Screen Widget**: Add shortcut to home screen for quick access

5. **Multiple Shortcuts**: Create separate shortcuts for:
   - Quick movie download
   - TV show season download
   - Upcoming releases

## Security Considerations

1. **HTTPS Only**: Always use HTTPS for webhook URLs
2. **Authentication**: Consider adding API key to requests:
   ```json
   {
     "apiKey": "your-secret-key",
     "platform": "siri",
     ...
   }
   ```
3. **User ID**: Use device-specific user IDs to track usage

## Example: Complete Shortcut Flow

```
┌─────────────────────────────────────┐
│ User: "Hey Siri, Overtalkerr"      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Siri: "What would you like to       │
│        download?"                    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ User: "Jurassic World from 2015"    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Shortcut: POST to /voice            │
│ {title: "Jurassic World",           │
│  year: "2015"}                      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Overtalkerr: {speech: "I found..." }│
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Siri: "I found the movie Jurassic   │
│  World, released in 2015. Is that   │
│  the one you want?"                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ User: "Yes"                         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Shortcut: POST to /voice            │
│ {action: "AMAZON.YesIntent"}        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Siri: "Okay! I've requested         │
│  Jurassic World."                   │
└─────────────────────────────────────┘
```

## Next Steps

1. Create your first basic shortcut
2. Test with a simple movie download
3. Expand with year/season support
4. Add conversation flow for Yes/No
5. Share with family members

Happy downloading with Siri! 🎬📺
