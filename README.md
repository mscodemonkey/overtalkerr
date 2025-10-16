# Overtalkerr - Universal Voice Assistant for Media Requests

Request movies and TV shows using **Alexa**, **Google Assistant**, or **Siri**! 🎙️

> **⚠️ BETA SOFTWARE**: Overtalkerr is currently in beta testing. While we've worked hard to make it stable and feature-complete, please use at your own risk and report any issues you encounter on [GitHub Issues](https://github.com/mscodemonkey/overtalkerr/issues). Your feedback helps make it better!

> **🚀 Proxmox Users**: Install in seconds with our LXC helper script! See [install_on_proxmox.md](docs/install_on_proxmox.md)

A self-hostable multi-platform voice assistant backend that works with **Overseerr**, **Jellyseerr**, and **Ombi**:

**🔵 Alexa:**
- "Alexa, ask Overtalkerr to download Jurassic World"
- "Alexa, ask Overtalkerr to download season 2 of Breaking Bad"

**🔴 Google Assistant:**
- "Hey Google, talk to Overtalkerr"
- "Download the movie Jurassic World from 2015"

**⚪ Siri:**
- "Hey Siri, Overtalkerr"
- "Download the upcoming TV show Robin Hood"

The backend automatically detects your media request service (Overseerr, Jellyseerr, or Ombi) and uses the appropriate API to search titles and create requests. It confirms the best match, lets you say Yes/No to iterate through results (filtered by media type, year, season, and prioritizing upcoming releases), and submits the request.

## ✨ Features

### Voice Platforms
- **Amazon Alexa** - Full skill support with ask-sdk-python
- **Google Assistant** - Dialogflow integration
- **Siri Shortcuts** - iOS/macOS webhook support
- **Platform-Agnostic** - Unified business logic across all platforms

### Supported Media Request Backends
- **Overseerr** - The original media request manager
- **Jellyseerr** - Overseerr fork for Jellyfin (100% API compatible)
- **Ombi** - Alternative media request platform with different API

**Automatic Backend Detection**: Overtalkerr automatically detects which backend you're using by probing the API endpoints - no manual configuration needed! Just provide your base URL and API key.

> **💡 Using Radarr/Sonarr?** These tools are excellent for managing downloads, but they lack the unified search experience that makes voice requests intuitive. We recommend pairing them with one of the supported backends above - they're specifically designed to provide a better search and request interface while still managing your Radarr/Sonarr instances behind the scenes. This gives you the best of both worlds: powerful automation *and* user-friendly requests!

Overtalkerr supports the three most widely-used media request managers in the self-hosting community. If you're using a different request platform, we'd love to hear about it! [Open an issue on GitHub](https://github.com/mscodemonkey/overtalkerr/issues) to discuss potential support.

📚 **[See Backend Configuration Guide](docs/connect_to_request_apps.md)** for setup details and compatibility notes.

### Capabilities
- **🔍 Enhanced Search**:
  - Fuzzy matching handles typos and speech recognition errors
  - Natural language temporal queries ("recent movies", "upcoming shows")
  - Genre extraction from queries ("scary movie", "funny show")
  - Smart result ranking with similarity scores
- **📊 Smart Availability Checking**:
  - Automatically detects if media is already in your library
  - Warns you before requesting duplicates
  - Shows download progress ("already being downloaded")
  - Identifies pending requests waiting for approval
- **Intelligent Filters**: Media type (movie/tv), year, upcoming releases
- **Season Selection**: Request specific seasons for TV shows
- **Conversational Interface**: Natural Yes/No flow to iterate through search results
- **Persistent State**: SQLite-based conversation state with automatic cleanup
- **Test Harness**: Beautiful web UI for testing without any voice device

📚 **[See Enhanced Search Features Guide](docs/enhanced_search.md)** for examples and advanced usage!

### Production Ready
- Comprehensive error handling and retry logic
- Structured JSON logging for monitoring
- Health checks and timeout handling
- Secure Docker deployment with non-root user
- Automated database migrations
- Multi-platform request verification

### Modern Stack
- Flask 3.x with updated dependencies
- ask-sdk-python (modern Alexa SDK)
- SQLAlchemy 2.0 with proper indexing
- Request retry with exponential backoff
- Environment validation on startup

## 📋 Requirements

- Python 3.11+ (if running locally without Docker)
- One of the following media request services:
  - **Overseerr** instance with API access
  - **Jellyseerr** instance with API access
  - **Ombi** instance with API access
- (For Alexa) Public HTTPS endpoint with valid certificate. Options:
  - Reverse proxy (Nginx/Caddy) with Let's Encrypt
  - Cloudflare Tunnel or ngrok (paid plan recommended)

## 🚀 Quick Start

Choose your installation method:

### Option A: Proxmox VE (Easiest for Homelab!)

Perfect for homelab users! One-command LXC container installation:

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/mscodemonkey/overtalkerr/main/ct/overtalkerr-standalone.sh)"
```

This creates a lightweight LXC container with everything pre-configured (Python, dependencies, systemd service, and more!). The script will prompt you for a container ID and then automatically install everything. After installation, just configure your backend settings via the web UI at `http://YOUR-LXC-IP:5000/config`.

See **[install_on_proxmox.md](docs/install_on_proxmox.md)** for full details.

---

### Option B: Docker (Recommended for Most Users)

First, clone the repository:

```bash
git clone https://github.com/mscodemonkey/overtalkerr.git
cd overtalkerr

# Copy and edit environment template
cp .env.example .env
nano .env  # Configure MEDIA_BACKEND_URL and MEDIA_BACKEND_API_KEY
```

Then build and run:

```bash
# Build the image
docker build -t overtalkerr .

# Run the container
docker run -d \
  --name overtalkerr \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  overtalkerr

# Check logs
docker logs -f overtalkerr
```

### 2. Option C: Local Python

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migration (if upgrading)
python migrate_db.py

# Start application
python app.py
```

### 3. Configure and Test

**Configuration UI** (recommended): Open `http://localhost:5000/config` to:
- Configure your media backend (Overseerr/Jellyseerr/Ombi)
- Test your API connection
- Adjust application settings
- Save and automatically restart the service

**Test UI**: Open `http://localhost:5000/test` to try searching for a movie without a voice device!

## 🎙️ Voice Platform Setup

Overtalkerr supports three major voice platforms. Choose the one(s) you want to use:

### 🔵 Amazon Alexa (Recommended)

**Powered by:** ask-sdk-python (modern SDK)
**Endpoint:** `https://your-domain.com/alexa` (POST)

**Quick Setup:**
1. Create skill in [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
2. Set invocation name: `overtalkerr`
3. Import the interaction model from `alexa/interactionModel.json`
4. Configure HTTPS endpoint with your Overtalkerr URL
5. Enable testing and start using!

**Features Supported:**
- ✅ Full conversational flow (Yes/No)
- ✅ Season selection
- ✅ Year filtering
- ✅ Upcoming releases
- ✅ Request verification

📚 **[Complete Alexa Setup Guide](docs/how_to_setup_alexa.md)** - Step-by-step instructions with troubleshooting

---

### 🔴 Google Assistant

**Powered by:** Dialogflow
**Endpoint:** `https://your-domain.com/voice` (POST)

1. **Create Agent** in [Dialogflow Console](https://dialogflow.cloud.google.com/)
2. **Configure Intents**:
   - DownloadIntent (with parameters: MediaTitle, Year, MediaType, Season)
   - YesIntent
   - NoIntent
3. **Enable Fulfillment**:
   - Webhook URL: `https://your-domain.com/voice`
4. **Test in Actions Console**
5. **Deploy** to Google Assistant

**Features Supported:**
- ✅ Full conversational flow
- ✅ Season selection
- ✅ Suggestion chips (Yes/No buttons)
- ✅ Rich cards

📚 **[Complete Google Assistant Setup Guide](docs/how_to_setup_google_assistant.md)** - Detailed walkthrough with examples

---

### ⚪ Siri Shortcuts

**Powered by:** iOS/macOS Shortcuts app
**Endpoint:** `https://your-domain.com/voice` (POST)

1. **Open Shortcuts** app on iPhone/Mac
2. **Create New Shortcut** with these actions:
   - Ask for Input: "What would you like to download?"
   - Get Contents of URL: `https://your-domain.com/voice`
     - Method: POST
     - Body: JSON with title parameter
   - Speak Text: Response speech
3. **Add to Siri**: Record activation phrase "Overtalkerr"
4. **Test**: "Hey Siri, Overtalkerr"

**Features Supported:**
- ✅ Quick downloads
- ✅ Optional parameters (year, season)
- ⚠️ Limited conversation flow (requires additional shortcuts)

📚 **[Complete Siri Setup Guide](docs/how_to_setup_siri.md)** - Easy step-by-step tutorial for iOS users

---

### Platform Comparison

| Feature | Alexa | Google | Siri |
|---------|-------|--------|------|
| Setup Difficulty | Medium | Medium | Easy |
| Conversational Flow | Excellent | Excellent | Manual |
| Season Selection | ✅ | ✅ | ✅ |
| Year Filtering | ✅ | ✅ | ✅ |
| Upcoming Releases | ✅ | ✅ | ✅ |
| Visual Cards | ✅ | ✅ | ❌ |
| Multi-turn Dialog | ✅ | ✅ | ⚠️ (requires setup) |
| Review Process | Required | Required | None |
| Works Offline | ❌ | ❌ | ❌ |

**Recommendation:** Set up all three! They use the same backend, so there's no extra work once configured.

## How it works

- `GET /api/v1/search` is called with your spoken title. Results are enriched with `_releaseDate`, `_date`, `_title`, and `_mediaType`.
- If you said a year, items are filtered to keep only `releaseDate.startswith(year)`.
- If you asked for upcoming, items with future `_date` are ranked first.
- The best item is offered: "I found the movie … released in YEAR, is that the one you want?".
- If you say No, the next result is offered using "What about …".
- If you say Yes, `POST /api/v1/request` is sent with `mediaId` and `mediaType`.

Notes:
- For TV series, Overseerr defaults are used (no explicit seasons provided). You can extend `overseerr.request_media` to include seasons if you prefer.

## ⚙️ Configuration

All configuration is managed through environment variables in `.env`:

> **💡 Database Note**: Overtalkerr uses a SQLite database to remember conversation context between voice requests (e.g., when you say "No" to iterate through search results). The database is created automatically - no setup required! It's a single file that persists across restarts and is automatically cleaned up (old conversations are deleted after 24 hours).

### Required Settings

```bash
# Your media request backend (Overseerr, Jellyseerr, or Ombi)
MEDIA_BACKEND_URL=https://your-backend-instance.com
MEDIA_BACKEND_API_KEY=your-api-key-here
SECRET_KEY=your-random-secret-key
```

### Optional Settings

```bash
# Development
FLASK_ENV=development
LOG_FORMAT=text
LOG_LEVEL=DEBUG
MOCK_BACKEND=true

# Production
FLASK_ENV=production
LOG_FORMAT=json
LOG_LEVEL=INFO
MOCK_BACKEND=false

# Database (stores conversation state - required for multi-turn dialogs)
# DEFAULT: SQLite - zero setup, just works! No need to change this.
DATABASE_URL=sqlite:///./overtalkerr.db
SESSION_TTL_HOURS=24  # Auto-cleanup old conversations

# Note: Advanced users can use PostgreSQL/MySQL, but SQLite is recommended
# for typical deployments. See .env.example for alternative database URLs.

# Security (for test endpoints)
BASIC_AUTH_USER=admin
BASIC_AUTH_PASS=secure-password

# Alexa (required for skill)
PUBLIC_BASE_URL=https://your-domain.com
```

See [`.env.example`](.env.example) for complete documentation.

## Security and deployment tips

- Run behind a reverse proxy with HTTPS (Caddy makes this very easy):

Caddyfile example:
```
your.domain {
    reverse_proxy localhost:5000
}
```

- If using Nginx, ensure proxy buffers and headers for chunked responses are set.
- Lock down the host firewall to allow only 80/443.

## Extending

- Add slot elicitation to prompt for missing title or clarify media type.
- Localize prompts.
- Add an intent to request specific seasons for TV.

## Troubleshooting

- If Alexa says it can't reach the skill, confirm your endpoint is publicly reachable over HTTPS with a valid cert.
- Check container logs: `docker logs -f overtalkerr`.
- Verify backend API connection:
  - Overseerr/Jellyseerr: `curl -H "X-Api-Key: $MEDIA_BACKEND_API_KEY" "${MEDIA_BACKEND_URL}/api/v1/search?query=jurassic"`
  - Ombi: `curl -H "ApiKey: $MEDIA_BACKEND_API_KEY" "${MEDIA_BACKEND_URL}/api/v1/Search/movie/jurassic"`

## Local test harness (no Alexa device required)

Open your browser to `http://localhost:5000/test`.

- Start a search by filling Title, optional Year, Media Type (movie/tv/auto), and Upcoming flag.
- Click `Start` to simulate the DownloadIntent.
- Click `No` to iterate candidates (the UI will display the spoken prompt).
- Click `Yes` to confirm and create a request (or simulate if mock mode is on).
- Use `Reset` to clear the current conversation state, or `Purge` to remove all saved states.

REST endpoints (for curl/Postman):

- `POST /test/start` with JSON: `{ "userId": "tester-1", "conversationId": "conv-123", "title": "Jurassic World", "year": "2015", "mediaType": "movie", "upcoming": false }`
- `POST /test/yes` with JSON: `{ "userId": "tester-1", "conversationId": "conv-123" }`
- `POST /test/no` with JSON: `{ "userId": "tester-1", "conversationId": "conv-123" }`
- `GET /test/state?userId=tester-1&conversationId=conv-123`
- `POST /test/reset` with JSON: `{ "userId": "tester-1", "conversationId": "conv-123" }`
- `POST /test/purge` with JSON: `{}` or `{ "userId": "tester-1" }`

## Mock mode

Enable mocked backend behavior (no outbound API calls):

```
MOCK_BACKEND=true
```

The UI banner at `/test` shows whether mock mode is ON or OFF.

## Conditional Basic Auth for test endpoints

For `/test` and `/test/*` endpoints, Basic Auth is enforced only for non-local requests and only when credentials are configured.

Set credentials in `.env` (optional):

```
BASIC_AUTH_USER=someuser
BASIC_AUTH_PASS=somepass
```

- Local/private addresses (127.0.0.1, ::1, 192.168.x.x, 10.x.x.x, 172.16–172.31.x.x) can access `/test` without auth.
- Non-local requests must present Basic Auth if the variables above are set.
- When reverse-proxied, ensure `X-Forwarded-For` is passed so origin IPs are correctly detected.
