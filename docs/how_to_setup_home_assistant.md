# Setting Up Overtalkerr with Home Assistant Assist

Want to request movies and TV shows through your Home Assistant voice assistant? Perfect! This guide will show you how to connect Overtalkerr to Home Assistant Assist. 🏠🎬

## What You'll Need

Before we get started, make sure you have:

- **Home Assistant** installed and running (version 2023.1 or newer recommended)
- **HACS** (Home Assistant Community Store) installed for easy integration management
- **Home Assistant Assist** configured with a voice assistant (like Wyoming Protocol, Piper, Whisper, etc.)
- **Your Overtalkerr URL** - Something like `http://overtalkerr.local:5000` or `https://overtalkerr.yourdomain.com`

> **💡 Quick Check**: Open a browser and navigate to your Overtalkerr URL - if you see the dashboard, you're good to go!

---

## What is Home Assistant Assist?

Home Assistant Assist is the built-in voice assistant platform in Home Assistant. It lets you control your smart home and interact with integrations using voice commands. By adding Overtalkerr as a "conversation agent," you can ask your voice assistant to download media!

**Instead of saying:** "Turn on the living room lights"
**You can now say:** "Download The Matrix" or "Find Breaking Bad season 2"

---

## Step 1: Install the Webhook-Conversation Integration

Overtalkerr connects to Home Assistant via the **webhook-conversation** custom integration. This allows external services to act as conversation agents.

### Install via HACS (Recommended)

1. Open **Home Assistant**
2. Go to **HACS** → **Integrations**
3. Click the **⋮** menu (top right) → **Custom repositories**
4. Add repository:
   - **URL**: `https://github.com/EuleMitKeule/webhook-conversation`
   - **Category**: Integration
5. Click **Add**
6. Search for **"Webhook Conversation"** in HACS
7. Click **Download**
8. Restart Home Assistant

### Manual Installation (Alternative)

If you don't use HACS:

1. Download the latest release from [webhook-conversation GitHub](https://github.com/EuleMitKeule/webhook-conversation)
2. Extract the `webhook_conversation` folder
3. Copy it to `config/custom_components/webhook_conversation/`
4. Restart Home Assistant

---

## Step 2: Configure Your Overtalkerr Webhook URL

You need to know your Overtalkerr webhook URL. It follows this format:

```
http://YOUR-SERVER-IP:5000/homeassistant
```

**Examples:**
- Local network: `http://192.168.1.100:5000/homeassistant`
- Docker: `http://overtalkerr:5000/homeassistant`
- Remote: `https://overtalkerr.yourdomain.com/homeassistant`

> **🔒 Security Note**: If Overtalkerr is exposed to the internet, set up a webhook secret! See "Optional: Securing Your Webhook" below.

To find your URL:
1. Open Overtalkerr in a browser
2. Go to **Configuration** → **Home Assistant Integration**
3. The webhook URL is displayed there - copy it!

---

## Step 3: Add Overtalkerr as a Conversation Agent

Now let's tell Home Assistant to use Overtalkerr for voice commands.

### Via UI (Easiest)

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **"Webhook Conversation"**
4. Click on it to configure
5. Enter the following:
   - **Name**: `Overtalkerr`
   - **Webhook URL**: `http://your-server:5000/homeassistant` (your Overtalkerr URL)
   - **Output Field**: `output` (default - don't change)
   - **Timeout**: `30` seconds (default is fine)
   - **Response Streaming**: **MUST be UNCHECKED** ⚠️ (streaming is not supported)
6. Click **Submit**

> **⚠️ Important:** Make sure "Enable response streaming" is **unchecked**. This checkbox is sometimes checked by default, but Overtalkerr does not support streaming responses. Leaving it enabled will cause "Unable to get response" errors.

### Via YAML (Advanced)

Alternatively, add to `configuration.yaml`:

```yaml
conversation:
  - platform: webhook_conversation
    name: Overtalkerr
    url: http://your-server:5000/homeassistant
    output_field: output
    timeout: 30
```

Then restart Home Assistant.

---

## Step 4: Set Overtalkerr as Your Default Assistant

For Overtalkerr to handle media requests, it needs to be your active conversation agent.

### Option A: Set as Default for All Assist Requests

1. Go to **Settings** → **Voice Assistants**
2. Click on **Assist** (or your configured assistant)
3. Under **Conversation agent**, select **Overtalkerr Local**
4. **IMPORTANT**: Make sure **"Prefer handling commands locally"** is **OFF** (unchecked)
   - This ensures all commands go directly to Overtalkerr
   - If enabled, Home Assistant will try to handle commands first, causing issues
5. Click **Save**

Now all voice commands will go through Overtalkerr first.

### Option B: Create a Dedicated Media Request Assistant

Want to keep the default Home Assistant assistant for smart home control? Create a second assistant just for media!

1. Go to **Settings** → **Voice Assistants**
2. Click **+ Add Assistant**
3. Configure:
   - **Name**: `Media Assistant`
   - **Conversation agent**: `Overtalkerr Local`
   - **Prefer handling commands locally**: **OFF** (unchecked) ⚠️
   - **Text-to-Speech**: Your preferred TTS engine
   - **Speech-to-Text**: Your preferred STT engine
4. Click **Create**

Now you can switch assistants based on what you want to do!

---

## Step 5: Try It Out!

Time to test! Say to your Home Assistant voice assistant:

**"Download Inception"**

Your assistant should respond with:
> "I found Inception from 2010. Would you like me to request it?"

Then say:

**"Yes"**

And Overtalkerr will submit the request to your media backend! 🎉

---

## How It Works: Understanding the Flow

Here's what happens behind the scenes:

1. **You speak** → "Download The Office season 3"
2. **Home Assistant Assist** processes the audio (STT)
3. **Webhook-Conversation** sends the text to Overtalkerr
4. **Overtalkerr** searches your media backend (Overseerr/Jellyseerr/Ombi)
5. **Overtalkerr** responds with results
6. **Home Assistant** speaks the response (TTS)
7. **You confirm** → "Yes" or "No, next one"
8. **Overtalkerr** creates the request!

---

## Advanced Usage

### Requesting TV Shows with Seasons

**Say:** "Download Breaking Bad season 2"

Overtalkerr automatically detects the season number and requests it specifically.

### Filtering by Year

**Say:** "Find Dune from 2021"

The year filter helps when there are multiple versions of a movie.

### Requesting Movies vs TV Shows

Overtalkerr tries to figure out if you want a movie or TV show automatically, but you can be explicit:

**Say:** "Find the movie Fargo" (when there's also a TV series with that name)

### Multi-Turn Conversations

Overtalkerr remembers context between requests:

**You:** "Download Stranger Things"
**Assistant:** "I found Stranger Things from 2016..."
**You:** "No"
**Assistant:** "I don't have any other results. Would you like to try a different search?"

---

## Optional: Securing Your Webhook

If your Overtalkerr instance is exposed to the internet, add authentication:

### 1. Generate a Secret Token

Create a secure random string (password manager or command line):

```bash
openssl rand -hex 32
```

Copy the output - this is your webhook secret.

### 2. Configure Overtalkerr

1. Open Overtalkerr configuration at `/config`
2. Scroll to **Home Assistant Integration**
3. Enter your secret in **Webhook Secret**
4. Click **Save & Restart**

### 3. Configure Webhook-Conversation with Authentication

Update your Home Assistant configuration to include the secret:

**Via UI:**
1. Go to **Settings** → **Devices & Services**
2. Find **Webhook Conversation (Overtalkerr)**
3. Click **Configure**
4. Under **Authentication**:
   - **Username**: leave blank
   - **Password**: `your-webhook-secret-here`
5. Click **Submit**

**Via YAML:**

```yaml
conversation:
  - platform: webhook_conversation
    name: Overtalkerr
    url: http://your-server:5000/homeassistant
    output_field: output
    timeout: 30
    headers:
      Authorization: "Bearer your-webhook-secret-here"
```

Now only authenticated requests will be processed!

---

## Troubleshooting

### "Sorry, I couldn't understand your request"

**This usually means:**
- Overtalkerr couldn't parse your request
- Check Overtalkerr logs for errors

**Try this:**
1. Open your Overtalkerr web UI
2. Go to the test page (`/test`)
3. Try the same request manually to see what happens

### "Unable to get response" Error

**Symptoms:** Home Assistant shows "Unable to get response" when testing the conversation agent

**Most Common Cause:** Response streaming is enabled when it shouldn't be

**Fix:**
1. Go to **Settings** → **Devices & Services**
2. Find **Webhook Conversation (Overtalkerr)**
3. Click **Configure**
4. **Uncheck "Enable response streaming"** ✓
5. Click **Submit**

**Why this happens:** The streaming checkbox is sometimes checked by default. Overtalkerr sends standard JSON responses, not streaming responses, so this must be disabled.

### Connection Errors

**Symptoms:** "Unable to reach Overtalkerr" or timeout errors

**Check:**
1. Is Overtalkerr running? Visit the URL in a browser
2. Can Home Assistant reach the URL? Check network/firewall
3. Is the webhook URL correct? Double-check spelling and port
4. Are you using `http://` vs `https://` correctly?
5. Use the **local IP address** (e.g., `http://192.168.1.100:5000/homeassistant`) instead of public domain to avoid redirect issues

**Test connectivity:**
1. In Home Assistant, go to **Developer Tools** → **Services**
2. Call service: `conversation.process`
3. Service data:
   ```yaml
   text: "test"
   agent_id: conversation.overtalkerr
   ```
4. Check for errors in Home Assistant logs

### Authentication Failed

**If you set up a webhook secret:**
- Make sure the secret matches exactly in both Overtalkerr and Home Assistant
- Check for extra spaces or typos
- The format should be: `Authorization: Bearer your-secret`

### Voice Assistant Not Using Overtalkerr

**Check:**
1. Is Overtalkerr selected as the conversation agent?
   - **Settings** → **Voice Assistants** → Check the agent setting
2. Is **"Prefer handling commands locally"** turned OFF?
   - Go to **Settings** → **Voice Assistants** → Click your assistant
   - Make sure this toggle is **unchecked** (off)
   - If enabled, Home Assistant intercepts commands instead of sending them to Overtalkerr
3. Did you restart Home Assistant after adding the integration?
4. Is the webhook-conversation integration loaded?
   - **Settings** → **System** → **Logs** - Look for webhook_conversation errors

---

## Using Multiple Assistants

Want both smart home control AND media requests? Set up multiple assistants!

### Assistant 1: Home Control
- **Name**: "Home Assistant"
- **Conversation Agent**: "Home Assistant (built-in)"
- Use for: Lights, switches, sensors, automations

### Assistant 2: Media Requests
- **Name**: "Media Assistant"
- **Conversation Agent**: "Overtalkerr"
- Use for: Movies, TV shows, media downloads

Switch between them:
1. In the Home Assistant app, go to **Assist**
2. Tap the assistant name at the top
3. Select which assistant to use

Or assign different devices to different assistants:
- Living room speaker → Home Assistant
- Bedroom speaker → Media Assistant

---

## Automations & Scripts

### Create a Quick Request Script

Want a button to request media? Create a script:

```yaml
script:
  request_media:
    alias: Request Media
    sequence:
      - service: conversation.process
        data:
          text: "{{ media_title }}"
          agent_id: conversation.overtalkerr
```

### Voice-Activated Request

Create an automation triggered by a voice command:

```yaml
automation:
  - alias: Movie Night
    trigger:
      - platform: voice_command
        sentence: "It's movie night"
    action:
      - service: conversation.process
        data:
          text: "Download a popular movie from 2024"
          agent_id: conversation.overtalkerr
```

---

## Example Voice Commands

Here are some things you can say:

**Basic Requests:**
- "Download Inception"
- "Find Breaking Bad"
- "Request The Matrix"

**With Details:**
- "Download Stranger Things season 4"
- "Find Dune from 2021"
- "Request the movie Fargo"

**Conversations:**
- "Download Top Gun" → "Maverick from 2022?" → "No" → "Original from 1986?" → "Yes"

**Help:**
- "Help" (Overtalkerr explains what it can do)

---

## Integration with Other Home Assistant Features

### Dashboard Button

Add a button to your dashboard to open the media request interface:

```yaml
type: button
name: Request Media
icon: mdi:movie-search
tap_action:
  action: call-service
  service: conversation.process
  service_data:
    agent_id: conversation.overtalkerr
    text: "What would you like to download?"
```

### Notify When Media Is Added

Combine with Overseerr/Jellyseerr webhooks to get notifications:

```yaml
automation:
  - alias: Media Request Completed
    trigger:
      - platform: webhook
        webhook_id: overseerr_webhook
    action:
      - service: notify.mobile_app
        data:
          message: "{{ trigger.json.subject }} is ready to watch!"
```

---

## Tips & Best Practices

### 1. Use Natural Language

Overtalkerr understands conversational requests:
- ✅ "I want to watch The Office season 3"
- ✅ "Can you download Inception?"
- ✅ "Find me a movie called Interstellar"

### 2. Be Specific with Titles

If there are multiple results:
- Add the year: "Dune 2021"
- Specify media type: "The movie Fargo" or "The show Fargo"

### 3. Test via UI First

Before voice testing:
1. Open Overtalkerr test page (`/test`)
2. Try your queries there
3. See what results come back
4. Adjust your voice commands based on what works

### 4. Check Your Backend Connection

Make sure Overtalkerr can reach your media backend:
1. Go to Overtalkerr **Configuration**
2. Test the backend connection
3. Fix any connection issues before trying voice commands

---

## Frequently Asked Questions

### Can I use this with multiple Home Assistant instances?

Yes! Each Home Assistant instance can have its own webhook-conversation configuration pointing to the same or different Overtalkerr instances.

### Does this work with Home Assistant Cloud (Nabu Casa)?

Yes! Just make sure your Overtalkerr instance is accessible from the internet (use HTTPS and set up a webhook secret for security).

### Can I use this with custom wake words?

Absolutely! Home Assistant Assist supports custom wake words via Wyoming Protocol. Set up your wake word as usual, and Overtalkerr will work with it.

### What about local voice processing?

Yes! This works great with local STT/TTS (like Piper + Whisper). Overtalkerr receives text, so it doesn't matter how Home Assistant processes the audio.

### Can I use this with ESPHome voice assistants?

Yes! Any device that works with Home Assistant Assist (including ESPHome devices) can use Overtalkerr.

---

## Next Steps

Here's what I'd recommend:

1. **Test the basic flow** - Just request one movie to make sure it works
2. **Try conversations** - Say "No" to iterate through results
3. **Set up authentication** - If your instance is internet-accessible
4. **Create automations** - Add buttons, scripts, or routines
5. **Customize responses** - Overtalkerr's behavior is configurable

---

## Need Help?

If you get stuck:

1. Check the [main README](../README.md) for general Overtalkerr troubleshooting
2. Look at Overtalkerr logs for errors (`docker logs overtalkerr`)
3. Check Home Assistant logs (**Settings** → **System** → **Logs**)
4. Test the webhook URL directly using curl or Postman
5. Open an issue on [GitHub](https://github.com/mscodemonkey/overtalkerr/issues)

---

## Additional Resources

- [Home Assistant Assist Documentation](https://www.home-assistant.io/voice_control/)
- [Webhook-Conversation Integration](https://github.com/EuleMitKeule/webhook-conversation)
- [Overtalkerr GitHub](https://github.com/mscodemonkey/overtalkerr)

---

Happy voice requesting! Now go forth and ask your home to download all your favorite movies! 🎬🏠✨
