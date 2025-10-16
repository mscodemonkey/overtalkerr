# Backend Configuration Guide

Overtalkerr supports three popular media request services: **Overseerr**, **Jellyseerr**, and **Ombi**. The backend type is automatically detected - just configure your base URL and API key!

## Supported Backends

### Overseerr
The original media request manager for Plex.

**Features:**
- Full TMDB integration
- User-based quotas
- 4K support
- Discord/Slack/Email notifications

**API Compatibility:** ✅ Full support

### Jellyseerr
A fork of Overseerr designed for Jellyfin users.

**Features:**
- Same as Overseerr
- Optimized for Jellyfin integration
- 100% API compatible with Overseerr

**API Compatibility:** ✅ Full support (inherits Overseerr implementation)

### Ombi
An alternative media request platform supporting Plex, Jellyfin, and Emby.

**Features:**
- Multi-media server support (Plex/Jellyfin/Emby)
- User management and quotas
- Notifications and integrations
- Different API structure than Overseerr

**API Compatibility:** ✅ Full support (custom implementation)

## Configuration

### Step 1: Get Your API Key

#### For Overseerr/Jellyseerr:
1. Log in to your Overseerr/Jellyseerr instance
2. Go to **Settings** → **General**
3. Scroll down to **API Key** section
4. Copy the API key

#### For Ombi:
1. Log in to your Ombi instance
2. Go to **Settings** → **Ombi**
3. Find the **API Key** field
4. Copy the API key

### Step 2: Configure Environment Variables

Edit your `.env` file:

```bash
# Your backend base URL (no trailing slash)
MEDIA_BACKEND_URL=https://request.example.com

# Your backend API key
MEDIA_BACKEND_API_KEY=your-api-key-here

# Optional: Mock mode for testing
MOCK_BACKEND=false
```

### Step 3: Start Overtalkerr

When Overtalkerr starts, it will automatically detect which backend you're using:

```
INFO: Detected Jellyseerr backend
INFO: Initialized JellyseerrBackend
```

or

```
INFO: Detected Ombi backend
INFO: Initialized OmbiBackend
```

## How Auto-Detection Works

Overtalkerr probes your backend API to determine the type:

1. **Tries Overseerr/Jellyseerr API** (`/api/v1/status`):
   - If successful, checks the version string
   - If contains "jellyseerr" → Jellyseerr
   - Otherwise → Overseerr

2. **Tries Ombi API** (`/api/v1/Status`):
   - If successful → Ombi

3. **Fallback**:
   - If detection fails → defaults to Overseerr

## Backend-Specific Notes

### Overseerr & Jellyseerr

Both use identical APIs, so they share the same implementation:

- Search endpoint: `GET /api/v1/search`
- Request endpoint: `POST /api/v1/request`
- Authentication: `X-Api-Key` header
- Season selection: `{"seasons": [1, 2, 3]}` in request payload

**Example Request:**
```json
{
  "mediaId": 12345,
  "mediaType": "tv",
  "seasons": [2]
}
```

### Ombi

Ombi has a different API structure:

- Search endpoints:
  - Movies: `GET /api/v1/Search/movie/{query}`
  - TV: `GET /api/v1/Search/tv/{query}`
- Request endpoints:
  - Movies: `POST /api/v1/Request/movie`
  - TV: `POST /api/v1/Request/tv`
- Authentication: `ApiKey` header (different from Overseerr!)
- Season selection: More complex format with episode arrays

**Example Request:**
```json
{
  "tvDbId": 12345,
  "requestAll": false,
  "seasons": [
    {
      "seasonNumber": 2,
      "episodes": []
    }
  ]
}
```

**Important Ombi Differences:**
1. Uses TVDB IDs instead of TMDB IDs for TV shows
2. Requires fetching show details before requesting
3. Separate endpoints for movies and TV
4. Different header name for API key

Overtalkerr handles all these differences automatically!

## Testing Your Configuration

### Test via Web UI

1. Start Overtalkerr
2. Navigate to `http://localhost:5000/test`
3. Try searching for a movie or TV show
4. The results will show which backend is being used

### Test via Logs

Enable debug logging in `.env`:

```bash
LOG_LEVEL=DEBUG
```

You'll see detailed logs showing:
- Which backend was detected
- API calls being made
- Response data

Example log output:
```json
{
  "timestamp": "2025-10-16T10:30:00Z",
  "level": "INFO",
  "message": "Detected Jellyseerr backend"
}
{
  "timestamp": "2025-10-16T10:30:05Z",
  "level": "DEBUG",
  "message": "Searching backend: query='Jurassic World', media_type=movie"
}
```

## Mock Mode for Testing

You can test Overtalkerr without a real backend:

```bash
MOCK_BACKEND=true
```

This will:
- Skip backend auto-detection
- Return fake search results
- Simulate successful requests
- Perfect for development and testing

## Troubleshooting

### "Could not detect backend type, defaulting to Overseerr"

**Cause:** Auto-detection failed to connect to any backend API.

**Solutions:**
1. Check your `MEDIA_BACKEND_URL` is correct
2. Verify your `MEDIA_BACKEND_API_KEY` is valid
3. Ensure the backend is accessible from Overtalkerr
4. Check firewall rules
5. Review logs for connection errors

### "Invalid API key or insufficient permissions"

**Cause:** Authentication failed.

**Solutions:**
1. Verify your API key is correct
2. Check if the API key has expired
3. For Ombi: Ensure you're using the API key from Settings → Ombi (not User settings)
4. Regenerate the API key in your backend

### "Request to backend timed out"

**Cause:** Network connectivity issues.

**Solutions:**
1. Check if backend is running
2. Test connectivity: `curl https://your-backend.com/api/v1/status`
3. Increase timeout in `media_backends.py` if needed
4. Check network latency

### Different Results Between Backends

**Expected behavior:** Different backends may return different results because:
- Ombi uses TVDB instead of TMDB
- Search algorithms differ
- Available metadata varies

Overtalkerr normalizes results to provide a consistent experience.

## Media Status Tracking

One of Overtalkerr's most powerful features is **automatic duplicate prevention**. All three backends (Overseerr, Jellyseerr, and Ombi) track media availability by syncing with your media servers (Plex, Jellyfin, or Emby), and Overtalkerr intelligently uses this information to prevent duplicate requests.

### How It Works

When you search for media, Overtalkerr checks the current status and tells you:

**"This is already in your library!"**
- Media is fully available in Plex/Jellyfin/Emby
- You can watch it right now
- Request is **blocked** - no duplicate created

**"This is currently being downloaded"**
- Media is approved and actively downloading via Radarr/Sonarr
- It will be available soon
- Request is **blocked** - already in progress

**"This has already been requested and is pending approval"**
- Request exists but hasn't been approved yet
- Waiting for admin approval
- Request is **blocked** - duplicate pending request

**"This is partially in your library"** *(TV shows only)*
- Some episodes/seasons are available
- Other episodes/seasons might be missing
- Request is **allowed** if you're requesting a specific missing season
- User is **informed** about partial availability

### Status Information

Behind the scenes, Overtalkerr tracks these statuses:

| Status | Overseerr/Jellyseerr Code | Ombi Field | Meaning |
|--------|---------------------------|------------|---------|
| Unknown | `1` | N/A | Media server status unknown |
| Pending | `2` | `requested=true, approved=false` | Requested, awaiting approval |
| Processing | `3` | `approved=true, available=false` | Downloading via Radarr/Sonarr |
| Partially Available | `4` | N/A | Some content available (TV shows) |
| Available | `5` | `available=true` | Fully in your library |
| Deleted | `6` | N/A | Previously available, now removed |

### Examples

**Example 1: Already Available**
```
User: "Alexa, ask Overtalkerr to download Jurassic Park"
Overtalkerr: "I found the movie Jurassic Park, released in 1993. This is already in your library. Is that the one you want?"
User: "Yes"
Overtalkerr: "Jurassic Park is already in your library! You can watch it now."
```

**Example 2: Currently Downloading**
```
User: "Alexa, ask Overtalkerr to download Breaking Bad"
Overtalkerr: "I found the TV show Breaking Bad, released in 2008. This is currently being downloaded. Is that the one you want?"
User: "Yes"
Overtalkerr: "Breaking Bad is already being downloaded. It should be available soon!"
```

**Example 3: Pending Approval**
```
User: "Alexa, ask Overtalkerr to download The Matrix"
Overtalkerr: "I found the movie The Matrix, released in 1999. This has already been requested and is pending approval. Is that the one you want?"
User: "Yes"
Overtalkerr: "The Matrix has already been requested and is waiting for approval."
```

### Benefits

1. **Saves bandwidth** - No duplicate downloads
2. **Reduces server load** - Prevents redundant requests to Radarr/Sonarr
3. **Better user experience** - Clear feedback about media status
4. **Admin-friendly** - Fewer duplicate requests to manage

### No Direct Server Connection Required

Overtalkerr **does not** need to connect directly to Plex, Jellyfin, or Emby. All availability information comes from your backend (Overseerr/Jellyseerr/Ombi), which already syncs with your media servers.

This means:
- ✅ One API connection (to your backend)
- ✅ No additional permissions needed
- ✅ Works through reverse proxies
- ✅ Status is always current (synced by backend)

## API Compatibility Matrix

| Feature | Overseerr | Jellyseerr | Ombi |
|---------|-----------|------------|------|
| Search Movies | ✅ | ✅ | ✅ |
| Search TV Shows | ✅ | ✅ | ✅ |
| Request Movies | ✅ | ✅ | ✅ |
| Request TV Shows | ✅ | ✅ | ✅ |
| Season Selection | ✅ | ✅ | ✅ |
| Fuzzy Search | ✅ | ✅ | ✅ |
| Auto-Detection | ✅ | ✅ | ✅ |
| **Media Status Tracking** | ✅ | ✅ | ✅ |
| **Duplicate Prevention** | ✅ | ✅ | ✅ |
| **Availability Detection** | ✅ | ✅ | ✅ |
| 4K Requests | ✅ | ✅ | ⚠️ (via separate request) |

## Advanced Configuration

### Forcing a Specific Backend

While not recommended (auto-detection is reliable), you can force a backend type by modifying `media_backends.py`:

```python
# In app.py or config initialization
from media_backends import BackendFactory, BackendType

# Force Ombi
backend = BackendFactory.create(
    backend_type=BackendType.OMBI,
    base_url="https://ombi.example.com",
    api_key="your-api-key"
)
```

### Custom Backend Timeout

Edit `media_backends.py` to change request timeouts:

```python
class MediaBackend(ABC):
    def __init__(self, base_url: str, api_key: str):
        # ...
        self.timeout = (10, 60)  # (connect_timeout, read_timeout) in seconds
```

### Retry Configuration

Modify retry behavior in `media_backends.py`:

```python
retry_strategy = Retry(
    total=5,              # Number of retries (default: 3)
    backoff_factor=2,     # Wait time multiplier (default: 1)
    status_forcelist=[429, 500, 502, 503, 504],
)
```

## Switching Between Backends

If you're switching from one backend to another:

1. **Update `.env`** with new base URL and API key
2. **Restart Overtalkerr** - it will auto-detect the new backend
3. **Test the integration** using the web UI
4. **No code changes needed!**

Example switching from Overseerr to Jellyseerr:

```bash
# Old configuration
MEDIA_BACKEND_URL=https://overseerr.example.com
MEDIA_BACKEND_API_KEY=old-api-key

# New configuration
MEDIA_BACKEND_URL=https://jellyseerr.example.com
MEDIA_BACKEND_API_KEY=new-api-key
```

Restart and you're done!

## Contributing Backend Support

Want to add support for another backend? Here's how:

1. **Create a new backend class** in `media_backends.py`:
   ```python
   class NewBackend(MediaBackend):
       def search(self, query, media_type):
           # Implement search logic
           pass

       def request_media(self, media_id, media_type, season):
           # Implement request logic
           pass
   ```

2. **Add detection logic** to `BackendFactory.detect_backend_type()`:
   ```python
   # Try NewBackend API
   try:
       headers = {"Authorization": f"Bearer {api_key}"}
       resp = requests.get(f"{base_url}/api/status", headers=headers, timeout=5)
       if resp.ok:
           return BackendType.NEWBACKEND
   except:
       pass
   ```

3. **Update the factory** to instantiate your backend:
   ```python
   elif backend_type == BackendType.NEWBACKEND:
       return NewBackend(base_url, api_key)
   ```

4. **Test thoroughly** with the new backend
5. **Update documentation** in this file
6. **Submit a pull request!**

## Questions?

If you encounter issues with a specific backend:

1. Check the [Troubleshooting](#troubleshooting) section
2. Enable debug logging: `LOG_LEVEL=DEBUG`
3. Review backend-specific API documentation
4. Open an issue on GitHub with:
   - Backend type and version
   - Logs (redact sensitive info!)
   - Steps to reproduce

## Resources

- [Overseerr Documentation](https://docs.overseerr.dev/)
- [Jellyseerr Documentation](https://github.com/Fallenbagel/jellyseerr)
- [Ombi Documentation](https://docs.ombi.app/)
- [Overtalkerr GitHub](https://github.com/yourusername/overtalkerr)
