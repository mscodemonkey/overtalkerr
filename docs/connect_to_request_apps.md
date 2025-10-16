# Configuring Your Media Request Backend

Hey there! So you've got Overtalkerr set up and now you need to connect it to your media request system. Great! Let's get that configured! 🎬

The cool thing about Overtalkerr is that it works with **three different backends** - Overseerr, Jellyseerr, and Ombi. Even better? It **automatically detects** which one you're using! You just need to tell it where to find your backend and give it an API key. Easy!

## Which Backend Should I Use?

Don't have one yet? Here's a quick guide:

### Overseerr
**Best for:** Plex users who want a modern, polished request manager

The original and most popular choice! Overseerr is actively developed, has a beautiful UI, and tons of features like user quotas, 4K support, and Discord notifications.

**Get it:** [overseerr.dev](https://overseerr.dev/)

### Jellyseerr
**Best for:** Jellyfin users

This is a fork of Overseerr specifically designed for Jellyfin instead of Plex. It looks identical to Overseerr and has all the same features - it's just optimized for Jellyfin!

**Get it:** [github.com/Fallenbagel/jellyseerr](https://github.com/Fallenbagel/jellyseerr)

### Ombi
**Best for:** Users who want multi-server support or were using Ombi before Overseerr existed

Ombi has been around longer and supports Plex, Jellyfin, AND Emby. It has a different API structure, but Overtalkerr handles that automatically.

**Get it:** [ombi.io](https://ombi.io/)

> **💡 Already using one of these?** Perfect! Skip to the [Configuration](#configuration) section below!

---

## Configuration

Alright, let's connect Overtalkerr to your backend! This is super simple - just two steps.

### Step 1: Get Your API Key

An API key is like a password that lets Overtalkerr talk to your backend. Here's how to find it:

#### If you're using Overseerr or Jellyseerr:

1. Open your Overseerr/Jellyseerr web interface in your browser
2. Log in (you'll need admin access)
3. Click **Settings** in the sidebar
4. Click **General**
5. Scroll down until you see **API Key**
6. There it is! Click the **Copy** button next to it

That's it! Keep that key handy - you'll need it in a second.

#### If you're using Ombi:

1. Open your Ombi web interface in your browser
2. Log in (you'll need admin access)
3. Click **Settings** in the sidebar
4. Click **Ombi** (under Configuration section)
5. Look for the **API Key** field
6. Copy that key!

**Important:** Make sure you're getting the API key from Settings → Ombi, NOT from your user settings!

### Step 2: Add It to Your Configuration

Now let's tell Overtalkerr where your backend lives!

#### Option 1: Use the Web Configuration UI (Easiest!)

1. Open your browser and go to: `http://your-overtalkerr-server:5000/config`
2. In the **Media Request Backend** section:
   - **Backend URL**: Enter your backend's URL (like `https://requests.yourdomain.com`)
   - **Backend API Key**: Paste the API key you just copied
3. Click **Test Connection** to make sure it works!
4. If the test succeeds, click **Save & Restart**

Done! Overtalkerr will restart and automatically detect which backend you're using! 🎉

#### Option 2: Edit the .env File Manually

If you prefer the command line:

1. Open your `.env` file in a text editor
2. Find these lines and update them:

```bash
# Your backend's URL (no trailing slash!)
MEDIA_BACKEND_URL=https://requests.yourdomain.com

# Your backend's API key (paste it here)
MEDIA_BACKEND_API_KEY=your-api-key-goes-here
```

3. Save the file
4. Restart Overtalkerr

When it starts up, check the logs - you should see something like:

```
INFO: Detected Jellyseerr backend
INFO: Initialized JellyseerrBackend
```

Perfect! That means it's working!

---

## How Does Auto-Detection Work?

Curious how Overtalkerr figures out which backend you're using? Here's the magic:

1. **First, it tries the Overseerr/Jellyseerr API** at `/api/v1/status`
   - If it gets a response, it checks the version string
   - If it contains "jellyseerr" → You're using Jellyseerr!
   - If it doesn't → You're using Overseerr!

2. **If that didn't work, it tries the Ombi API** at `/api/v1/Status`
   - If it gets a response → You're using Ombi!

3. **If nothing worked** → It assumes Overseerr and hopes for the best!

You don't need to do anything special - it all happens automatically when Overtalkerr starts up!

---

## Testing Your Setup

Let's make sure everything is working!

### Quick Test via Web UI

1. Make sure Overtalkerr is running
2. Open your browser to: `http://localhost:5000/test` (or your server's address)
3. Try searching for a popular movie like "Jurassic World"
4. You should see results! If you do, it's working! 🎉

At the bottom of the test page, you'll see which backend it detected.

### Check the Logs

Want to see what's happening behind the scenes? Enable debug logging!

1. Edit your `.env` file:
   ```bash
   LOG_LEVEL=DEBUG
   ```

2. Restart Overtalkerr

3. Watch the logs - you'll see detailed information like:
   ```
   INFO: Detected Jellyseerr backend
   DEBUG: Searching backend: query='Jurassic World', media_type=movie
   DEBUG: Found 5 results from backend
   ```

This is super helpful for troubleshooting!

---

## The Cool Part: Smart Duplicate Prevention

Here's one of Overtalkerr's best features - it **prevents duplicate requests automatically**!

Your backend (whether it's Overseerr, Jellyseerr, or Ombi) already syncs with your media server (Plex, Jellyfin, or Emby). It knows what you have and what's being downloaded. Overtalkerr uses that information to give you helpful feedback:

### What You'll Hear

**"This is already in your library!"**
- The movie/show is fully available in your media server
- You can watch it right now!
- Overtalkerr **blocks** the request - no need to download it again!

**Example:**
```
You: "Alexa, ask Overtalkerr to download Jurassic Park"
Alexa: "I found Jurassic Park from 1993. This is already in your library! You can watch it now."
```

---

**"This is currently being downloaded"**
- The media has been approved and Radarr/Sonarr is downloading it
- It'll be in your library soon!
- Overtalkerr **blocks** the request - it's already on the way!

**Example:**
```
You: "Hey Google, ask Overtalkerr to download Breaking Bad"
Google: "I found Breaking Bad from 2008. This is currently being downloaded. It should be available soon!"
```

---

**"This has already been requested and is pending approval"**
- Someone already requested it, but it hasn't been approved yet
- An admin needs to approve it first
- Overtalkerr **blocks** the request - no duplicate pending requests!

**Example:**
```
You: "Alexa, ask Overtalkerr to download The Matrix"
Alexa: "The Matrix has already been requested and is waiting for approval."
```

---

**"This is partially in your library" (TV shows only)**
- Some episodes or seasons are available
- Others might be missing
- Overtalkerr **allows** the request if you're asking for a specific missing season
- You'll be **informed** about what's already there

---

### Why This Is Awesome

1. **Saves bandwidth** - No downloading the same thing twice!
2. **Saves disk space** - No duplicate files cluttering your server
3. **Better experience** - You get clear feedback about what's available
4. **Easier for admins** - Fewer duplicate requests to sort through

### The Best Part?

Overtalkerr **doesn't need** to connect directly to Plex, Jellyfin, or Emby! All the availability information comes from your backend, which already knows what's in your library. One API connection, no extra setup needed!

---

## Troubleshooting

### "Could not detect backend type, defaulting to Overseerr"

**What this means:** Overtalkerr couldn't connect to your backend to figure out which type it is.

**Try these fixes:**

1. **Check your URL** - Make sure `MEDIA_BACKEND_URL` is correct
   - It should be something like `https://requests.yourdomain.com`
   - No trailing slash!
   - Make sure it's the URL you actually use to access your backend

2. **Test the URL** - Open it in your browser
   - Can you see your backend's login page?
   - If not, the URL is wrong or your backend is down

3. **Check your API key** - Make sure `MEDIA_BACKEND_API_KEY` is correct
   - Try copying it again from your backend's settings
   - Make sure you didn't accidentally include extra spaces

4. **Test connectivity** - From your Overtalkerr server, try:
   ```bash
   curl https://your-backend-url/api/v1/status
   ```
   - If this fails, there's a network issue
   - Check firewalls, DNS, etc.

5. **Check the logs** - Look for error messages that might give you a clue

---

### "Invalid API key or insufficient permissions"

**What this means:** The API key isn't working.

**Try these fixes:**

1. **Double-check the API key** - Copy it again from your backend
2. **Regenerate it** - In your backend's settings, generate a new API key
3. **For Ombi users** - Make SURE you're using the API key from Settings → Ombi, NOT from user settings!
4. **Check permissions** - Make sure the API key has admin permissions

---

### "Request to backend timed out"

**What this means:** Your backend is too slow to respond or not responding at all.

**Try these fixes:**

1. **Is the backend running?** - Check if you can access it in your browser
2. **Network issues?** - Is there a firewall blocking the connection?
3. **Backend overloaded?** - Is your backend server struggling? Check its CPU/memory usage
4. **Try manually:**
   ```bash
   curl -H "X-Api-Key: your-key" https://your-backend-url/api/v1/search?query=test
   ```
   If this takes forever, the problem is with your backend, not Overtalkerr

---

### The results look different than what I see in my backend

**This is normal!** Different backends work differently:

- **Ombi** uses TVDB for TV shows, while **Overseerr/Jellyseerr** use TMDB
  - Different databases sometimes have different info!
- Search algorithms are different
- Available metadata varies

Overtalkerr tries its best to normalize everything and give you consistent results!

---

## Mock Mode (For Testing)

Want to test Overtalkerr without having a real backend connected? No problem!

1. Edit your `.env` file:
   ```bash
   MOCK_BACKEND=true
   ```

2. Restart Overtalkerr

Now it will:
- Skip trying to connect to a real backend
- Return fake search results (like "Jurassic World" and "The Matrix")
- Pretend requests succeed

This is perfect for:
- Development
- Testing the voice interfaces without setting up a full backend
- Demonstrating Overtalkerr to someone

Just remember to set it back to `false` when you're ready to use it for real!

---

## Switching Backends

Moving from Overseerr to Jellyseerr? Or from Ombi to Overseerr? No problem!

1. **Get your new backend's API key** (follow the steps above)

2. **Update your configuration:**
   - Use the config UI at `/config`, OR
   - Edit `.env` and change `MEDIA_BACKEND_URL` and `MEDIA_BACKEND_API_KEY`

3. **Restart Overtalkerr**

That's it! It'll automatically detect the new backend and start using it. No code changes, no complicated migration!

---

## Behind the Scenes: How It Works

Want to know the technical details? Here you go!

### Overseerr & Jellyseerr

These two use the **exact same API**, so Overtalkerr uses the same implementation for both:

- **Search:** `GET /api/v1/search?query=jurassic`
- **Request:** `POST /api/v1/request` with JSON body
- **Authentication:** Uses the `X-Api-Key` header
- **Season selection:** Sends `{"seasons": [2]}` in the request

### Ombi

Ombi does things differently:

- **Search:** Separate endpoints for movies and TV
  - Movies: `GET /api/v1/Search/movie/jurassic`
  - TV: `GET /api/v1/Search/tv/breaking bad`
- **Request:** Also separate endpoints
  - Movies: `POST /api/v1/Request/movie`
  - TV: `POST /api/v1/Request/tv`
- **Authentication:** Uses `ApiKey` header (note: different name!)
- **IDs:** Uses TVDB IDs for TV shows instead of TMDB IDs
- **Season selection:** More complex format with episode arrays

**But you don't need to worry about any of this!** Overtalkerr handles all the differences automatically.

---

## API Compatibility

Here's what works with each backend:

| Feature | Overseerr | Jellyseerr | Ombi |
|---------|-----------|------------|------|
| Search Movies | ✅ | ✅ | ✅ |
| Search TV Shows | ✅ | ✅ | ✅ |
| Request Movies | ✅ | ✅ | ✅ |
| Request TV Shows | ✅ | ✅ | ✅ |
| Request Specific Seasons | ✅ | ✅ | ✅ |
| Auto-Detection | ✅ | ✅ | ✅ |
| Duplicate Prevention | ✅ | ✅ | ✅ |
| Availability Tracking | ✅ | ✅ | ✅ |
| 4K Requests | ✅ | ✅ | ⚠️ (possible but requires separate request) |

Everything just works! 🎉

---

## Advanced Stuff (For Power Users)

### Custom Timeouts

If your backend is slow, you can increase the timeout. Edit `media_backends.py`:

```python
class MediaBackend(ABC):
    def __init__(self, base_url: str, api_key: str):
        # ...
        self.timeout = (10, 60)  # (connect, read) in seconds
        # Increase these numbers if needed!
```

### Retry Configuration

By default, Overtalkerr retries failed requests 3 times. Want to change that? Edit `media_backends.py`:

```python
retry_strategy = Retry(
    total=5,              # More retries
    backoff_factor=2,     # Wait longer between retries
    status_forcelist=[429, 500, 502, 503, 504],
)
```

### Force a Specific Backend Type

Don't want auto-detection? You can force a specific backend type in your code, but honestly, auto-detection is so reliable that you probably don't need to!

---

## Need Help?

Stuck on something?

1. **Check this guide again** - The answer might be in a section you skipped!
2. **Enable debug logging** - Set `LOG_LEVEL=DEBUG` in your `.env` file
3. **Test with the web UI** - Go to `/test` and try searching there
4. **Check your backend's docs:**
   - [Overseerr Docs](https://docs.overseerr.dev/)
   - [Jellyseerr GitHub](https://github.com/Fallenbagel/jellyseerr)
   - [Ombi Docs](https://docs.ombi.app/)
5. **Open a GitHub issue** - I'm happy to help! [github.com/mscodemonkey/overtalkerr/issues](https://github.com/mscodemonkey/overtalkerr/issues)

---

## Want to Add Support for Another Backend?

Got another media request system you'd like Overtalkerr to support? Awesome! Here's how to add it:

1. Create a new class in `media_backends.py` that inherits from `MediaBackend`
2. Implement the `search()` and `request_media()` methods
3. Add detection logic to `BackendFactory.detect_backend_type()`
4. Test it thoroughly!
5. Update this documentation
6. Submit a pull request!

I'd love to expand backend support - let's make Overtalkerr work with everything! 🚀

---

Happy requesting! Your voice-controlled media downloads just got a whole lot smarter! 🎬🍿
