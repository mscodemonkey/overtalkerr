# Setting Up Overtalkerr with Amazon Alexa

Hey Alexa user! Ready to make your Echo device download movies and TV shows just by asking? Let's get you set up! 🎤

Alexa is probably the easiest of the three voice platforms to set up, and it works really well with Overtalkerr. Once you're done, you'll be able to just say "Alexa, ask Overtalkerr to download Jurassic World" and boom - it's requested!

## Before We Start

Make sure you have these things ready:

- **An Amazon account** - The one you use with your Alexa devices
- **Your Overtalkerr server URL** - Something like `https://overtalkerr.yourdomain.com`
  - **Super important**: It **must** be `https://` (not `http://`) - Alexa won't work without HTTPS!
  - It must be publicly accessible from the internet (Alexa needs to reach it from Amazon's servers)
- **About 10-15 minutes** - This is pretty straightforward!

> **💡 Quick Check**: Can you open your Overtalkerr URL in a web browser and see the test or config page? Great! Make sure it has a valid SSL certificate (you should see a padlock 🔒 in your browser's address bar).

---

## Part 1: Create Your Alexa Skill

A "skill" is what Amazon calls third-party apps for Alexa. We're going to create a custom skill that talks to your server!

### Step 1: Go to the Alexa Developer Console

1. Open your web browser and go to: **[developer.amazon.com/alexa/console/ask](https://developer.amazon.com/alexa/console/ask)**
2. Sign in with your Amazon account
3. You might need to accept some terms of service if this is your first time - that's normal!

### Step 2: Create a New Skill

1. Click the big **"Create Skill"** button
2. Fill in the form:

   **Skill name**: Type `Overtalkerr` (or whatever you want - this is just for you to see)

   **Primary locale**: Choose **English (US)** (or your preferred English variant)

   **Choose a model**: Select **Custom**

   **Choose a method**: Select **Provision your own**

   **Hosting services**: Select **Provision your own** (since you're running your own server!)

3. Click **"Create skill"** at the top right

4. On the next screen, choose **"Start from scratch"**

5. Click **"Continue with template"**

Wait a few seconds while Amazon sets everything up. You'll be taken to your new skill's dashboard!

🎉 Nice! You've created your skill. Now let's teach it what to do.

---

## Part 2: Set the Invocation Name

This is what you'll say to activate your skill - like "Alexa, ask Overtalkerr..."

1. On the left sidebar, click **"Invocations" → "Skill Invocation Name"**
2. In the **"Skill Invocation Name"** field, type: `overtalkerr`
   - Note: It has to be all lowercase, no spaces
   - This is what you'll say: "Alexa, ask **overtalkerr** to download..."
3. Click **"Save Model"** at the top

---

## Part 3: Import the Interaction Model

This is where the magic happens! Instead of manually creating all the intents, we have a pre-made configuration file you can just import.

### Step 1: Get the Interaction Model File

1. In your Overtalkerr project folder, find the file: `alexa/interactionModel.json`
2. Open it in a text editor (Notepad, TextEdit, VS Code, etc.)
3. Select everything (Ctrl+A or Cmd+A) and copy it (Ctrl+C or Cmd+C)

### Step 2: Import It into Alexa

1. In the Alexa Developer Console, look at the left sidebar
2. Click on **"Interaction Model" → "JSON Editor"**
3. You'll see some JSON code already there - select it all and delete it
4. Paste the code you copied from `interactionModel.json`
5. Click **"Save Model"** at the top
6. Click **"Build Model"** at the top
7. Wait for it to build (you'll see a progress indicator - this takes about 30 seconds)

When it's done, you'll see a success message! ✅

**What did we just do?** We taught Alexa how to understand phrases like:
- "Download Jurassic World"
- "Download season 2 of Breaking Bad"
- "Download the movie Jurassic World from 2015"
- "Yes" and "No" to confirm selections

Pretty cool, right?

---

## Part 4: Configure Your Endpoint

Now we need to tell Alexa where your Overtalkerr server lives.

1. In the left sidebar, click **"Endpoint"**
2. Select **"HTTPS"** (not AWS Lambda!)
3. In the **"Default Region"** field, enter your Overtalkerr URL:
   ```
   https://overtalkerr.yourdomain.com/alexa
   ```
   **Important notes:**
   - Use your actual domain (replace `overtalkerr.yourdomain.com`)
   - It must be HTTPS
   - Include `/alexa` at the end (this is the Alexa-specific endpoint)
   - Google and Siri use `/voice`, but Alexa uses `/alexa`

4. Scroll down to **"SSL certificate type"**
5. Select one of these based on your setup:
   - **"My development endpoint is a sub-domain..."** - If you're using Let's Encrypt, Cloudflare, or another standard CA
   - **"My development endpoint has a wildcard certificate..."** - If you're using a wildcard cert

   > **💡 Not sure?** If you're using Let's Encrypt or a standard SSL provider, choose the first option!

6. Click **"Save Endpoints"** at the top

---

## Part 5: Enable Testing

Now let's turn on testing so you can actually use it!

1. At the top of the page, click the **"Test"** tab
2. Where it says "Test is disabled for this skill," toggle the dropdown to **"Development"**

That's it! The skill is now active on your Amazon account! 🎉

---

## Part 6: Try It Out!

Time for the moment of truth! Let's test it.

### Test in the Browser First

1. You should already be on the "Test" tab
2. In the big text box at the top, type or use your microphone to say:
   ```
   ask overtalkerr to download jurassic world
   ```
3. Hit Enter (or click the microphone button)

You should see Alexa's response appear on the right side!

**What you should see:**
- Alexa says something like: "I found the movie Jurassic World, released in 2015. Is that the one you want?"
- You can then type or say "yes" or "no"

**If you see an error instead:**
- Check that your Overtalkerr server is running
- Make sure the endpoint URL is correct
- Look at your Overtalkerr server logs to see what went wrong

### Test on Your Actual Alexa Device

Once the browser test works, try it on your Echo, Echo Dot, or Alexa app!

Say: **"Alexa, ask Overtalkerr to download Jurassic World"**

Alexa should respond with the search results! Then you can say:
- **"Yes"** - to confirm and request it
- **"No"** - to see the next result

---

## What You Can Say

Here are some examples of things you can ask:

**Simple movie request:**
- "Alexa, ask Overtalkerr to download Jurassic World"

**Movie with year:**
- "Alexa, ask Overtalkerr to download Jurassic World from 2015"

**TV show with season:**
- "Alexa, ask Overtalkerr to download season 2 of Breaking Bad"

**Upcoming releases:**
- "Alexa, ask Overtalkerr to download the upcoming movie Robin Hood"

**Conversation flow:**
- "Alexa, ask Overtalkerr to download Jurassic"
- Alexa: "I found Jurassic World from 2015. Is that the one?"
- "No"
- Alexa: "What about Jurassic Park from 1993?"
- "Yes"
- Alexa: "Okay! I've requested Jurassic Park."

---

## Example Conversation

Here's what a full conversation looks like:

**You**: "Alexa, ask Overtalkerr to download Jurassic World"

**Alexa**: "I found the movie Jurassic World, released in 2015. Is that the one you want?"

**You**: "Yes"

**Alexa**: "Okay! I've requested Jurassic World. It should be available soon."

Done! Your movie is now in Overseerr/Jellyseerr/Ombi and will start downloading! 🎬

---

## Troubleshooting

### "There was a problem with the requested skill's response"

**This means Alexa got an error from your server.**

Check:
1. Is your Overtalkerr server running? Test the URL in your browser
2. Check your server logs - they'll show exactly what went wrong
3. Is your Overseerr/Jellyseerr/Ombi connection working? Try the test UI at `/test`
4. Make sure your `.env` file has the correct `MEDIA_BACKEND_URL` and `MEDIA_BACKEND_API_KEY`

### "The requested skill did not provide a valid response"

**This means Alexa couldn't understand your server's response.**

Check:
1. Make sure you're running the latest version of Overtalkerr
2. Check the logs for Python errors
3. Your server might be returning invalid JSON

### Alexa Says "I'm having trouble connecting to Overtalkerr"

**This means Alexa can't reach your server at all.**

Check:
1. Is your server publicly accessible? Try opening the URL from a different network (like your phone's cellular data)
2. Is your SSL certificate valid? Check for the padlock 🔒 in your browser
3. Is the endpoint URL correct in the Alexa skill settings? (Go to Endpoint tab and verify)
4. Is your firewall blocking port 443 (HTTPS)?

### "Alexa did not receive a valid response from Overtalkerr"

**This usually means a timeout - your server is too slow to respond.**

Check:
1. Is your Overseerr/Jellyseerr/Ombi server responding quickly? Test it directly
2. Check your internet connection speed
3. Look for errors in your Overtalkerr logs

### Testing Locally with ngrok

If you're developing and your server isn't public yet, you can use ngrok:

```bash
# In one terminal, run your app
python app.py

# In another terminal, run ngrok
ngrok http 5000

# Use the HTTPS URL ngrok gives you in your Alexa skill endpoint
# Example: https://abc123.ngrok-free.app/
```

**Important**: Free ngrok URLs change every time you restart, so you'll need to update the endpoint in Alexa each time!

---

## Advanced: Understanding the Interaction Model

Curious about what's in that `interactionModel.json` file? Here's what it contains:

### Intents (What Alexa Listens For)

**DownloadIntent** - The main intent for requesting media
- Recognizes: "download", "request", "get", etc.
- Parameters: MediaTitle, Year, MediaType, Season, Upcoming

**AMAZON.YesIntent** - Built-in intent for saying "yes"

**AMAZON.NoIntent** - Built-in intent for saying "no"

**AMAZON.CancelIntent & AMAZON.StopIntent** - Built-in intents for exiting

**AMAZON.HelpIntent** - Built-in intent for asking for help

**AMAZON.FallbackIntent** - Catches anything Alexa didn't understand

### Sample Utterances

The model includes lots of different ways you might phrase your request:
- "download {MediaTitle}"
- "download the {MediaType} {MediaTitle}"
- "download {MediaTitle} from {Year}"
- "download season {Season} of {MediaTitle}"
- And many more!

---

## Tips & Tricks

### Shorter Invocation

Instead of saying "Alexa, ask Overtalkerr to download Jurassic World," you can say:
- "Alexa, tell Overtalkerr download Jurassic World" (shorter!)
- "Alexa, open Overtalkerr" then "Download Jurassic World"

### Routines

You can create Alexa Routines that include Overtalkerr:
1. Open the Alexa app
2. Go to More → Routines
3. Create a routine like: "When I say 'movie night', ask Overtalkerr what I want to download"

### Multiple Users

Everyone in your household can use the skill! It works with:
- All Echo devices on your account
- The Alexa app on phones
- Alexa on Fire TV devices

### Keep It Enabled

Unlike published skills, your custom skill stays in "Development" mode. That's totally fine! It works perfectly, you just can't share it publicly (which you probably don't want to anyway since it's your personal media server!).

---

## Publishing Your Skill (Optional - Not Recommended)

You *could* publish this skill to the Alexa Skill Store, but **we don't recommend it** because:
1. Everyone who uses it would need access to YOUR Overseerr server (security issue!)
2. Amazon's certification process is strict and takes time
3. You'd need privacy policies, terms of service, etc.
4. It works great in Development mode for personal use!

**Keep it in Development mode** - it'll work forever for you and your household!

---

## What Happens Behind the Scenes?

Curious about the technical flow? Here's what happens:

```
You: "Alexa, ask Overtalkerr to download Jurassic World"
   ↓
Your Echo Device → Amazon Alexa Servers
   ↓
Amazon's servers use the Interaction Model to understand:
  - Intent: DownloadIntent
  - MediaTitle: "Jurassic World"
   ↓
Amazon sends JSON request to: https://your-domain.com/
   ↓
Your Overtalkerr server receives the request
   ↓
Overtalkerr searches your Overseerr/Jellyseerr/Ombi
   ↓
Overtalkerr sends response back to Amazon
   ↓
Alexa speaks the response to you!
```

---

## Next Steps

Now that you've got Alexa working:

1. **Test it thoroughly** - Try different movies, shows, years, seasons
2. **Check your Overseerr** - Make sure the requests are actually going through
3. **Teach your family** - Show them how to use it!
4. **Set up the other platforms** - Overtalkerr works with Google Assistant and Siri too!
5. **Customize the responses** - You can edit `alexa_handlers.py` if you want to change what Alexa says

---

## Need Help?

Stuck on something?

1. Check the [main README](../README.md) for general troubleshooting
2. Look at your server logs - they're incredibly helpful!
3. Test the basic functionality with the web test UI at `/test` first
4. Make sure your Overseerr/Jellyseerr/Ombi connection is working in the config UI
5. Open an issue on [GitHub](https://github.com/mscodemonkey/overtalkerr/issues) and I'll help you out!

---

## Resources

- **Alexa Developer Console**: [developer.amazon.com/alexa/console/ask](https://developer.amazon.com/alexa/console/ask)
- **Interaction Model File**: [interactionModel.json](../alexa/interactionModel.json)
- **Alexa Skill Documentation**: [developer.amazon.com/docs/custom-skills](https://developer.amazon.com/docs/custom-skills)

---

Happy downloading with Alexa! Your movie nights just got a whole lot easier! 🍿🎬

If you come up with cool new phrases or ways to use Overtalkerr with Alexa, share them in a GitHub issue - I'd love to hear about it!
