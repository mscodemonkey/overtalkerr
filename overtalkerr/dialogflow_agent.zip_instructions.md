# Google Assistant (Dialogflow) Setup for Overtalkerr

This guide explains how to set up Overtalkerr with Google Assistant using Dialogflow.

## Prerequisites

- Google Cloud account
- Access to Dialogflow Console
- Your Overtalkerr backend URL (must be HTTPS)

## Step 1: Create Dialogflow Agent

1. Go to [Dialogflow Console](https://dialogflow.cloud.google.com/)
2. Click "Create Agent"
3. Name: `Overtalkerr`
4. Default Language: English
5. Default Time Zone: Your timezone
6. Click "CREATE"

## Step 2: Configure Intents

### Intent: Default Welcome Intent
**Training Phrases:**
- Talk to Overtalkerr
- I want to download a movie
- Help me request media

**Responses:**
```
Welcome to Overtalkerr! You can say things like "download the movie Jurassic World" or "download the upcoming TV show Robin Hood". You can also specify seasons for TV shows. What would you like to download?
```

### Intent: DownloadIntent
**Training Phrases:**
- download $MediaTitle
- download the $MediaTitle
- download $MediaType $MediaTitle
- download the $MediaType $MediaTitle
- download $MediaTitle from $Year
- download the $MediaType $MediaTitle from $Year
- download the upcoming $MediaType $MediaTitle
- download season $Season of $MediaTitle
- download $MediaTitle season $Season
- request $MediaTitle
- get $MediaTitle

**Parameters:**
| Parameter Name | Entity Type | Required | Prompts |
|---------------|-------------|----------|---------|
| MediaTitle | @sys.any | Yes | "What's the title?" |
| MediaType | @MediaType | No | |
| Year | @sys.number | No | |
| Season | @sys.number | No | |
| Upcoming | @sys.any | No | |

**Fulfillment:**
- Enable webhook call for this intent
- Webhook URL: `https://your-domain.com/voice`

### Intent: YesIntent
**Training Phrases:**
- yes
- yep
- sure
- that's the one
- correct
- affirmative

**Fulfillment:**
- Enable webhook call for this intent

### Intent: NoIntent
**Training Phrases:**
- no
- nope
- not that one
- next
- show me another

**Fulfillment:**
- Enable webhook call for this intent

## Step 3: Create Custom Entities

### Entity: @MediaType
**Values:**
- movie (synonyms: film, motion picture)
- tv show (synonyms: series, television show, tv series, show)

## Step 4: Configure Fulfillment

1. Go to "Fulfillment" in left sidebar
2. Enable "Webhook"
3. URL: `https://your-domain.com/voice`
4. Click "SAVE"

## Step 5: Test in Dialogflow

1. Go to "Integrations" > "Google Assistant"
2. Click "TEST" to open Actions Console
3. Test with phrases like:
   - "Talk to Overtalkerr"
   - "Download the movie Jurassic World from 2015"
   - "Download season 2 of Breaking Bad"

## Step 6: Deploy to Google Assistant

1. In Actions Console, go to "Deploy" > "Directory Information"
2. Fill in required fields:
   - Display Name: Overtalkerr
   - Pronunciation: Over talker
   - Description: Voice assistant for requesting media through Overseerr
   - Sample Invocations:
     - "Talk to Overtalkerr"
     - "Ask Overtalkerr to download Jurassic World"
3. Add privacy policy URL
4. Submit for review

## Webhook Payload Structure

Your Overtalkerr backend at `/voice` will receive requests like this:

```json
{
  "responseId": "...",
  "queryResult": {
    "queryText": "download jurassic world from 2015",
    "intent": {
      "displayName": "DownloadIntent"
    },
    "parameters": {
      "MediaTitle": "jurassic world",
      "Year": 2015
    }
  },
  "originalDetectIntentRequest": {
    "payload": {
      "user": {
        "userId": "..."
      }
    }
  },
  "session": "projects/.../sessions/..."
}
```

And should respond with:

```json
{
  "fulfillmentText": "I found the movie Jurassic World, released in 2015. Is that the one you want?",
  "fulfillmentMessages": [
    {
      "text": {
        "text": ["I found the movie Jurassic World, released in 2015. Is that the one you want?"]
      }
    },
    {
      "suggestions": {
        "suggestions": [
          {"title": "Yes"},
          {"title": "No"}
        ]
      }
    }
  ]
}
```

## Troubleshooting

**Issue: "Webhook call failed"**
- Verify your webhook URL is HTTPS
- Check server logs at your Overtalkerr backend
- Test `/voice` endpoint directly with curl

**Issue: "I couldn't reach Overtalkerr"**
- Ensure your server is publicly accessible
- Check firewall settings
- Verify SSL certificate is valid

**Issue: Parameters not being captured**
- Review training phrases in Dialogflow
- Check entity definitions
- Test with different phrasings

## Testing Locally

You can test Google Assistant integration locally using ngrok:

```bash
# Start your app
python app.py

# In another terminal, start ngrok
ngrok http 5000

# Use the HTTPS URL in Dialogflow webhook settings
# Example: https://abc123.ngrok.io/voice
```

## Example Conversations

**User:** "Talk to Overtalkerr"
**Overtalkerr:** "Welcome to Overtalkerr! What would you like to download?"

**User:** "Download the movie Jurassic World from 2015"
**Overtalkerr:** "I found the movie Jurassic World, released in 2015. Is that the one you want?"

**User:** "Yes"
**Overtalkerr:** "Okay! I've requested Jurassic World. It should be available soon."

---

**User:** "Download season 2 of Breaking Bad"
**Overtalkerr:** "I found the TV show Breaking Bad, released in 2008. Is that the one you want?"

**User:** "Yes"
**Overtalkerr:** "Okay! I've requested season 2 of Breaking Bad. It should be available soon."
