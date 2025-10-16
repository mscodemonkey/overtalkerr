# Setting Up Overtalkerr with Siri Shortcuts

Hey there! So you want to ask Siri to download your favorite movies and TV shows? You've come to the right place! 🎬

Unlike Alexa or Google Assistant where you install a "skill," Siri works a bit differently. Instead, we're going to create a custom Siri Shortcut - think of it like teaching Siri a new trick. Don't worry, it's easier than it sounds, and I'll walk you through every step!

## What You'll Need

Before we get started, make sure you have:

- **An iPhone or iPad** running iOS 13 or newer (or a Mac with macOS 12+)
- **The Shortcuts app** - it comes pre-installed on your device, look for the colorful icon with two overlapping squares
- **Your Overtalkerr URL** - This should be something like `https://overtalkerr.yourdomain.com`. It **must** start with `https://` (not `http://`) for Siri to be happy!

> **💡 Quick Check**: Open Safari and type in your Overtalkerr URL - if you see the config or test page, you're good to go!

---

## The Easy Way: Basic Download Shortcut

Let's start simple. This shortcut will let you say "Hey Siri, Overtalkerr" and then tell it what you want to download. Ready? Let's do this!

### Step 1: Open the Shortcuts App

Find and tap the **Shortcuts** app on your device. It looks like this: 🔲🔲 (two colorful squares).

### Step 2: Create a New Shortcut

1. Tap the **+** button in the top right corner
2. Tap **Add Action** at the bottom
3. You'll see a search bar - this is where the magic happens!

### Step 3: Ask for User Input

First, we need Siri to ask you what you want to download.

1. In the search bar, type **"ask for input"**
2. Tap on **Ask for Input** when it appears
3. Now configure it:
   - Where it says "Prompt," type: **"What would you like to download?"**
   - Tap the (i) icon if you want to change other settings, but the defaults are fine!

🎉 Nice! Now when you run this shortcut, Siri will ask you that question.

### Step 4: Send Your Request to Overtalkerr

Now we need to actually send what you said to your Overtalkerr server.

1. Tap the **+** button to add another action
2. Search for **"get contents of URL"** and tap it
3. Here's where we configure the important stuff:

   **URL Field**: Tap where it says "URL" and type:
   ```
   https://overtalkerr.yourdomain.com/voice
   ```
   *(Replace `overtalkerr.yourdomain.com` with your actual domain!)*

4. Tap **Show More** to reveal additional options
5. Change **Method** from "GET" to **POST**
6. Change **Request Body** to **JSON**
7. In the JSON field, tap and you'll see options - select **Dictionary**

### Step 5: Build the Request Dictionary

This part looks a bit technical, but just follow along!

1. The Dictionary action should appear. Tap **Add new item** for each of these:

   **First item:**
   - Key: `platform`
   - Value: `siri` (just type the word siri)

   **Second item:**
   - Key: `userId`
   - Value: `siri-user` (or your name, like `siri-john`)

   **Third item:**
   - Key: `action`
   - Value: `DownloadIntent`

   **Fourth item (this is the important one!):**
   - Key: `title`
   - Value: Tap here and select **"Provided Input"** from the variables menu (it's the blue text from your Ask for Input action)

2. Tap **Show More** under Get Contents of URL
3. Add a header:
   - Header: `Content-Type`
   - Value: `application/json`

### Step 6: Get Siri to Speak the Response

Almost there! Now we need to extract what Overtalkerr said and have Siri read it back to you.

1. Add another action - search for **"get dictionary value"**
2. Configure it:
   - Key: `speech`
   - Dictionary: **Contents of URL** (select from variables)

3. Add one more action - search for **"speak text"**
4. For the text input, select **Dictionary Value** from variables

### Step 7: Name Your Shortcut and Add to Siri

1. Tap **Done** in the top right
2. Your shortcut needs a name! Tap where it says "Shortcut Name" at the top
3. Name it something like **"Overtalkerr"** or **"Download Movie"**
4. Now tap the **⋮** (three dots) icon
5. Tap **Add to Siri**
6. Tap the red record button and say **"Overtalkerr"** (or whatever phrase you want to use)
7. Tap **Done**

### Step 8: Try It Out!

Say: **"Hey Siri, Overtalkerr"**

Siri should ask you what you want to download, and then send your request to Overtalkerr! How cool is that? 🎉

---

## Making It Better: Adding Year Support

Want to specify which year? Let's add that!

1. Open your shortcut for editing
2. After the first "Ask for Input" action, add another one
3. Configure it:
   - Prompt: **"What year? Say 'any' if you don't care"**
   - Input Type: **Text**
4. In your Dictionary action, add a new item:
   - Key: `year`
   - Value: **Provided Input** (from your second Ask for Input)

Now when you use the shortcut, Siri will ask for both the title and year!

---

## Advanced: Full Conversation Support (Yes/No)

This is where things get really cool, but also a bit more complex. Overtalkerr might offer you multiple options, and you want to say "No, next one" or "Yes, that's it!"

### The Challenge

Siri Shortcuts don't naturally handle back-and-forth conversations like Alexa does. But we can work around this!

### Option 1: Create Separate "Yes" and "No" Shortcuts

**"Overtalkerr Yes" Shortcut:**
1. Create a new shortcut called "Overtalkerr Yes"
2. Add "Get Contents of URL"
3. Set URL to: `https://overtalkerr.yourdomain.com/voice`
4. Method: POST
5. JSON Body:
   ```
   {
     "platform": "siri",
     "userId": "siri-user",
     "action": "AMAZON.YesIntent"
   }
   ```
6. Add "Get Dictionary Value" for key `speech`
7. Add "Speak Text"
8. Add to Siri with phrase: **"Overtalkerr Yes"**

**"Overtalkerr No" Shortcut:**
- Same as above, but change `AMAZON.YesIntent` to `AMAZON.NoIntent`
- Add to Siri with phrase: **"Overtalkerr No"**

**How to use:**
1. "Hey Siri, Overtalkerr" → "I found Jurassic World from 2015, is that the one?"
2. "Hey Siri, Overtalkerr No" → "What about Jurassic Park from 1993?"
3. "Hey Siri, Overtalkerr Yes" → "Great! I've requested it!"

It's not perfect (you need to say the wake phrase each time), but it works!

### Option 2: One Shortcut with Prompts

1. After Siri speaks the result, add "Ask for Input"
2. Prompt: **"Is this correct?"**
3. Input Type: **Text**
4. Add an "If" action
5. Condition: **Provided Input** contains **"yes"**
6. If true: Send YesIntent
7. Otherwise: Send NoIntent

This lets you continue the conversation in one go!

---

## Quick Reference: What Goes in the JSON?

When you're building your dictionary, here's what each field means:

| Field | What It Does | Example |
|-------|-------------|---------|
| `platform` | Tells Overtalkerr you're using Siri | Always `siri` |
| `userId` | Identifies you (helpful for logs) | `siri-john` or `iPhone-Living-Room` |
| `action` | What you want to do | `DownloadIntent`, `AMAZON.YesIntent`, `AMAZON.NoIntent` |
| `title` | The movie/show name | `Jurassic World` |
| `year` | (Optional) Filter by year | `2015` |
| `mediaType` | (Optional) Force movie or TV | `movie` or `tv` |
| `season` | (Optional) For TV shows | `2` |

---

## Troubleshooting

### "Could not connect to server"

**This usually means:**
- Your URL is wrong - double-check it! Make sure it has `https://` at the start
- Your Overtalkerr server is down - try opening the URL in Safari
- You're not connected to the internet

**Try this:**
1. Open Safari on your device
2. Go to your Overtalkerr URL
3. If you see a page load, the server is fine - check your shortcut's URL setting
4. If Safari can't connect either, your server might be offline

### "Invalid response" or Siri Says Nothing

**This means:**
- Overtalkerr sent back a response, but the shortcut couldn't read it
- Usually a problem with the "Get Dictionary Value" step

**Try this:**
1. Edit your shortcut
2. Add a "Show Result" action right after "Get Contents of URL"
3. Run the shortcut and see what it shows - this is what Overtalkerr sent back
4. Make sure you're extracting the `speech` key

### Siri Doesn't Recognize My Phrase

**Try this:**
1. Re-record the Siri phrase - speak more clearly
2. Use a unique phrase that doesn't sound like other things
3. Avoid phrases with words like "the" or "a" at the beginning

---

## Cool Ideas for Your Shortcuts

### Create Different Shortcuts for Different Uses

**"Quick Movie"** - Downloads a movie immediately, no year needed

**"Upcoming Shows"** - Asks for a TV show name and requests all upcoming episodes

**"Friday Movie Night"** - Automation that reminds you every Friday to download something new

### Add Shortcuts to Your Home Screen

1. Edit your shortcut
2. Tap the ⋮ menu
3. Select **Add to Home Screen**
4. Now you can tap an icon instead of using voice!

### Use NFC Tags

Got an NFC tag? Stick it somewhere fun:
- On your TV remote
- On your movie poster
- By your couch

Set it to trigger "What do you want to download?" when you tap your phone to it!

---

## Sharing Your Shortcut with Family

Once you've got the perfect shortcut set up:

1. Open the shortcut
2. Tap the ⋮ menu
3. Tap **Share**
4. Choose **Copy iCloud Link**
5. Send that link to family/friends
6. They tap it, tap "Add Shortcut," and they're done!

**Important:** They'll need to edit the shortcut to change the URL to your Overtalkerr server if you shared via iCloud link.

---

## Next Steps

Here's what I'd recommend:

1. **Start with the basic shortcut** - Just the title input, nothing fancy
2. **Test it!** - Try downloading a popular movie to make sure it works
3. **Add the year** - Once the basic one works, add year support
4. **Try Yes/No** - If you're feeling adventurous, set up the conversation shortcuts
5. **Create variations** - Make shortcuts for specific use cases

---

## Need Help?

If you get stuck:

1. Check the [main README](../README.md) for general Overtalkerr troubleshooting
2. Look at your Overtalkerr logs (if you have access)
3. Test your URL directly in a web browser first
4. Open an issue on [GitHub](https://github.com/mscodemonkey/overtalkerr/issues) - I'm happy to help!

---

## Example: Your First Complete Shortcut

Let me put it all together in simple steps:

**Shortcut Name:** "Overtalkerr Download"

**Actions in order:**

1. **Ask for Input**
   - Prompt: "What would you like to download?"

2. **Dictionary**
   - platform: siri
   - userId: siri-user
   - action: DownloadIntent
   - title: [Provided Input]

3. **Get Contents of URL**
   - URL: https://your-overtalkerr-url.com/voice
   - Method: POST
   - Request Body: JSON
   - JSON: [Dictionary]
   - Header: Content-Type = application/json

4. **Get Dictionary Value**
   - Key: speech
   - Dictionary: [Contents of URL]

5. **Speak Text**
   - Text: [Dictionary Value]

**Add to Siri:** "Overtalkerr"

That's it! Now you can say "Hey Siri, Overtalkerr" → "Jurassic World" → Siri requests it! 🎬

---

Happy downloading! If you create any cool shortcuts or automations, I'd love to hear about them! Drop an issue on GitHub and share what you built! 🚀
