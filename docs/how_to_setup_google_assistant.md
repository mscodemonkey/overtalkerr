# Setting Up Overtalkerr with Google Assistant

Hey Google user! Ready to talk to your media server? Let's get Overtalkerr working with Google Assistant! 🎙️

Google Assistant uses a service called **Dialogflow** to understand what you're saying and send it to your Overtalkerr server. Think of Dialogflow as a translator between you and your server. Don't worry if that sounds complicated - I'll walk you through everything step by step!

## Before We Start

You'll need a few things ready:

- **A Google account** - The one you use for Google Assistant
- **Your Overtalkerr server URL** - Something like `https://overtalkerr.yourdomain.com`
  - **Important**: It must start with `https://` (not `http://`)
- **About 15-20 minutes** - Grab a coffee, this is a bit longer than the Siri setup, but you only do it once!

> **💡 Quick Test**: Before we start, open your browser and go to your Overtalkerr URL. Can you see the test or config page? Perfect! If not, get that working first before continuing.

---

## Part 1: Create Your Dialogflow Agent

An "agent" is what Google calls the thing that listens to you and talks to your server. Let's create one!

### Step 1: Go to Dialogflow

1. Open your web browser and go to: **[dialogflow.cloud.google.com](https://dialogflow.cloud.google.com/)**
2. Sign in with your Google account if you're not already
3. You'll see a page asking you to create an agent

### Step 2: Create the Agent

1. Click the **"Create Agent"** button (it's big and blue!)
2. Fill in the form:
   - **Agent name**: Type `Overtalkerr` (or whatever you want to call it)
   - **Default language**: Choose **English**
   - **Default time zone**: Pick your time zone
   - **Google Project**: Leave the default (it'll create a new one)
3. Click **"CREATE"**

Wait a few seconds while Google sets things up. You'll see a loading spinner, then you'll be taken to your new agent's dashboard!

🎉 Nice! You've created your agent. Now let's teach it what to listen for.

---

## Part 2: Teach Your Agent What to Listen For (Intents)

"Intents" are what Google calls the different things you might say. We need to set up a few of them.

### Intent 1: Welcome Message

This is what happens when you first say "Talk to Overtalkerr."

1. On the left sidebar, click **"Intents"**
2. Click on **"Default Welcome Intent"** (it's already there!)
3. Scroll down to **"Responses"**
4. Delete what's there and type this instead:
   ```
   Welcome to Overtalkerr! You can say things like "download the movie Jurassic World" or "download season 2 of Breaking Bad". What would you like to download?
   ```
5. Scroll up and click **"SAVE"** at the top

Great! Now when someone says "Talk to Overtalkerr," Google will say that welcome message.

### Intent 2: Download Request

This is the important one - when you actually ask to download something!

1. Click the **"+"** button next to "Intents" in the left sidebar
2. At the top, name it: `DownloadIntent`
3. Scroll down to **"Training phrases"** section
4. Click **"Add Training Phrases"** and add these one by one:
   - `download Jurassic World`
   - `download the movie Jurassic World`
   - `download Jurassic World from 2015`
   - `download season 2 of Breaking Bad`
   - `request the movie Inception`
   - `get the show Breaking Bad`
   - `download the upcoming show Robin Hood`

   As you type these, Dialogflow will automatically highlight words in different colors - that's it learning!

5. Scroll down to **"Action and parameters"** section
6. You should see Dialogflow automatically created some parameters. If not, add these:
   - **MediaTitle** - Entity: `@sys.any` - Required: ✓
   - **MediaType** - Entity: `@MediaType` - Required: ✗
   - **Year** - Entity: `@sys.number` - Required: ✗
   - **Season** - Entity: `@sys.number` - Required: ✗

7. For **MediaTitle**, click the "DEFINE PROMPTS" link and add: `What's the title?`

8. Scroll down to **"Fulfillment"** section (at the very bottom)
9. Click **"Enable webhook call for this intent"**
10. Click **"SAVE"** at the top

Awesome! Now Google knows how to recognize when you're asking to download something.

### Intent 3: Saying "Yes"

When Overtalkerr asks "Is that the one you want?" you need to be able to say yes!

1. Create a new intent (click the "+" next to Intents again)
2. Name it: `YesIntent`
3. Add training phrases:
   - `yes`
   - `yep`
   - `yeah`
   - `that's the one`
   - `correct`
   - `affirmative`
   - `sure`
   - `sounds good`
4. Scroll to **"Fulfillment"** and enable webhook
5. Click **"SAVE"**

### Intent 4: Saying "No"

And you need to be able to say no to see other options!

1. Create another new intent
2. Name it: `NoIntent`
3. Add training phrases:
   - `no`
   - `nope`
   - `not that one`
   - `next`
   - `show me another`
   - `try again`
   - `different one`
4. Enable webhook for this intent too
5. Click **"SAVE"**

---

## Part 3: Teach Google About Media Types (Optional but Recommended)

Let's create a custom entity so Google knows what "movie" and "TV show" mean.

1. In the left sidebar, click **"Entities"**
2. Click the **"+"** button to create a new entity
3. Name it: `MediaType`
4. Add these entries:

   **First entry:**
   - Reference value: `movie`
   - Synonyms: `film`, `motion picture`, `flick`

   **Second entry:**
   - Reference value: `tv`
   - Synonyms: `tv show`, `show`, `series`, `television show`

5. Click **"SAVE"**

Perfect! Now when you say "download the movie Jurassic World," Google knows "movie" is a media type!

---

## Part 4: Connect to Your Overtalkerr Server

Now we tell Dialogflow where your Overtalkerr server lives.

1. In the left sidebar, click **"Fulfillment"**
2. Toggle the **"Webhook"** switch to **ENABLED** (it'll turn blue)
3. In the **"URL"** field, enter:
   ```
   https://overtalkerr.yourdomain.com/voice
   ```
   (Replace with your actual Overtalkerr URL! And don't forget the `/voice` at the end!)

4. Scroll down and click **"SAVE"**

🎯 You're almost done! Now let's test it.

---

## Part 5: Test It Out!

Before we connect it to Google Assistant, let's make sure it works!

1. Look at the right side of the Dialogflow page - you'll see a **"Try it now"** section
2. In the text box, type: `download Jurassic World from 2015`
3. Press Enter

You should see:
- **Default Response** from Overtalkerr saying something like "I found the movie Jurassic World..."
- If you see an error, check that your webhook URL is correct and your server is running!

**Try a few more:**
- `download season 2 of Breaking Bad`
- `request the movie Inception`

If these work, you're golden! If not, here are common issues:

**"Webhook call failed"**
- Check your URL - is it correct? Does it start with `https://`?
- Is your Overtalkerr server running? Try opening the URL in your browser
- Check the logs on your Overtalkerr server - they'll show what went wrong

**"I couldn't understand"**
- Your training phrases might not match - try adding more variations
- Check the "Intents" tab to see which intent it matched (or didn't match)

---

## Part 6: Connect to Google Assistant

Now for the grand finale - connecting this to your actual Google Assistant!

### For Personal Use (Testing)

1. In Dialogflow, click **"Integrations"** in the left sidebar
2. Click on the **"Google Assistant"** card
3. Click **"UPDATE DRAFT"** (not "Test" - we want to save it first)
4. Wait for the confirmation, then click **"TEST"**
5. This will open a new tab called the **Actions Console**

In the Actions Console:
1. Click **"Test"** in the top navigation
2. You'll see a simulator - this lets you test without using your phone!
3. In the text box, type: `Talk to Overtalkerr`
4. You should see the welcome message!
5. Try saying: `download Jurassic World from 2015`

**Does it work?** Great! Now try it on your actual Google device:

- Say: **"Hey Google, talk to Overtalkerr"**
- Google should respond with your welcome message!
- Try: **"Download Jurassic World from 2015"**

🎉 **It works!** You're now talking to your media server through Google Assistant!

### For Public Release (Optional)

If you want to publish this so anyone can use it (not just you):

1. In the Actions Console, click **"Deploy"** in the left menu
2. Click **"Directory information"**
3. Fill in all the required fields:
   - **Display name**: Overtalkerr
   - **Pronunciation**: Over talker
   - **Description**: Voice assistant for requesting movies and TV shows
   - **Sample invocations**: Add 3 examples like "Talk to Overtalkerr"
   - **Category**: Entertainment
   - **Privacy policy URL**: You'll need to host a privacy policy somewhere
4. Click **"Save"**
5. Go to **"Release"** → **"Production"**
6. Click **"Submit for production"**
7. Google will review it (takes a few days to a week)

**Important**: For personal use, you don't need to do this! It works just fine for your own account without publishing.

---

## What's Actually Happening?

Curious how this works? Here's the flow:

```
You: "Hey Google, talk to Overtalkerr"
   ↓
Google: "Welcome to Overtalkerr! What would you like to download?"
   ↓
You: "Download Jurassic World from 2015"
   ↓
Google → Dialogflow → Your Overtalkerr Server
   ↓
Your Server: Searches Overseerr/Jellyseerr/Ombi
   ↓
Your Server → Dialogflow → Google
   ↓
Google: "I found the movie Jurassic World, released in 2015. Is that the one?"
   ↓
You: "Yes!"
   ↓
Google → Dialogflow → Your Server → Overseerr
   ↓
Google: "Okay! I've requested Jurassic World."
```

Pretty cool, right?

---

## Example Conversations

Here's what you can do once it's set up:

**Simple movie download:**
- **You**: "Hey Google, talk to Overtalkerr"
- **Google**: "Welcome to Overtalkerr! What would you like to download?"
- **You**: "Download Jurassic World"
- **Google**: "I found the movie Jurassic World from 2015. Is that the one?"
- **You**: "Yes"
- **Google**: "Okay! I've requested Jurassic World."

**TV show with season:**
- **You**: "Hey Google, ask Overtalkerr to download season 2 of Breaking Bad"
- **Google**: "I found the TV show Breaking Bad from 2008. Is that the one?"
- **You**: "Yes"
- **Google**: "Okay! I've requested season 2 of Breaking Bad."

**Specifying the year:**
- **You**: "Hey Google, tell Overtalkerr to download Jurassic World from 2015"
- **Google**: "I found the movie Jurassic World, released in 2015. Is that the one?"
- **You**: "Yes"
- **Google**: "Done!"

---

## Troubleshooting Common Issues

### "I'm sorry, I don't understand"

**This means Google couldn't figure out what you're asking for.**

Try:
- Adding more training phrases in the DownloadIntent
- Speaking more clearly
- Using different words ("request" instead of "download," for example)

### "I can't reach Overtalkerr right now"

**This means Dialogflow can't connect to your server.**

Check:
1. Is your server running? Test it in a browser
2. Is the webhook URL correct? Go to Fulfillment and double-check
3. Does your URL start with `https://` (not `http://`)?
4. Check your server's firewall - is port 443 open?

### "Something went wrong"

**This means your server responded, but with an error.**

Check:
1. Your Overtalkerr server logs - they'll show the error
2. Your Overseerr/Jellyseerr/Ombi connection - is it working?
3. Try the test UI at `/test` to see if the basic functionality works

### Testing Locally with ngrok

If you're developing and your server isn't public yet:

```bash
# In one terminal, run your app
python app.py

# In another terminal, run ngrok
ngrok http 5000

# Copy the https URL ngrok gives you (like https://abc123.ngrok.io)
# Use that + /voice in your Dialogflow webhook settings
```

---

## Tips & Tricks

### Make It Sound Natural

Add more training phrases that sound like how you'd actually talk:
- "grab me the movie Inception"
- "I wanna watch Jurassic World"
- "find Breaking Bad season 2"

The more examples you give, the better Google gets at understanding you!

### Use Suggestion Chips

In your responses, you can show clickable suggestions. Overtalkerr already does this - when it asks "Is that the one?" you'll see "Yes" and "No" buttons on your phone screen!

### Test on Different Devices

Works on:
- Google Home / Nest speakers
- Android phones (Google Assistant)
- Google Assistant on iPhone
- Smart displays (Nest Hub)

Try it on all your devices!

---

## Need Help?

Stuck on something?

1. Check the [main README](../README.md) for general troubleshooting
2. Look at your server logs - they're super helpful for debugging
3. Test with the Dialogflow simulator before trying on your device
4. Open an issue on [GitHub](https://github.com/mscodemonkey/overtalkerr/issues) and I'll help you out!

---

## Next Steps

Now that you've got it working:

1. **Test it thoroughly** - Try different movies, TV shows, and years
2. **Add more training phrases** - Make it understand you better
3. **Customize the welcome message** - Make it sound like you!
4. **Share with family** - They can use it on their Google accounts too
5. **Set up Alexa and Siri too** - Use all three platforms at once!

---

Happy downloading with Google Assistant! If you come up with cool training phrases or use cases, share them in a GitHub issue - I'd love to hear about it! 🚀
