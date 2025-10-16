# Installing Overtalkerr on Proxmox VE

Hey Proxmox user! If you're running a homelab with Proxmox, you're going to love this - Overtalkerr can be installed with a single command, just like those awesome community scripts from [community-scripts.github.io/ProxmoxVE](https://community-scripts.github.io/ProxmoxVE/)!

We've created an LXC helper script that sets everything up for you automatically. No Docker, no complicated configuration files, just a clean Debian container running Overtalkerr. Let's get you set up!

---

## The One-Command Install

Ready? Open your **Proxmox VE Shell** (SSH into your Proxmox host or use the web console) and run this:

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/mscodemonkey/overtalkerr/main/ct/overtalkerr-standalone.sh)"
```

The script will:
1. Ask you for a container ID (it suggests the next available one)
2. Show you the configuration
3. Ask you to confirm
4. Then automatically create and configure everything!

It takes about 2-3 minutes, and you'll see colorized progress messages for each step. ✨

---

## What Gets Installed

The installation script does all the heavy lifting for you:

1. ✅ Creates an unprivileged Debian 12 LXC container
2. ✅ Installs Python 3.11+ and all system dependencies
3. ✅ Clones the Overtalkerr repository to `/opt/overtalkerr`
4. ✅ Sets up a Python virtual environment (keeps things clean!)
5. ✅ Installs all Python dependencies
6. ✅ Creates a systemd service for automatic startup and restarts
7. ✅ Configures Gunicorn as the production WSGI server
8. ✅ Generates a secure random SECRET_KEY
9. ✅ Sets up logging and data directories with proper permissions

When it's done, you'll have a fully functional Overtalkerr instance running on port 5000!

---

## Default Container Settings

The script creates a lightweight LXC container with sensible defaults:

- **OS**: Debian 12 (Bookworm) - rock solid and lightweight
- **Type**: Unprivileged Container (more secure!)
- **CPU Cores**: 2 (plenty for voice requests)
- **RAM**: 1024 MB (1 GB) - more than enough
- **Disk**: 4 GB (includes OS, app, and room for logs)
- **Tags**: `media`, `voice-assistant` (helps you find it in Proxmox!)
- **Port**: 5000

> **💡 Want different specs?** Choose "Advanced" when the script asks, and you can customize everything!

---

## Post-Installation: Configure Your Backend

Okay, the app is installed, but it doesn't know where your Overseerr/Jellyseerr/Ombi server is yet. Let's fix that!

You have two options - the web UI (super easy!) or editing the config file directly:

### Option 1: Web Configuration UI (Recommended! 🌟)

This is the easiest way - just point your browser to:

```
http://YOUR-LXC-IP:5000/config
```

Replace `YOUR-LXC-IP` with your container's IP address (you can find this in the Proxmox web UI or by running `ip addr` in the container).

The web interface gives you:
- ✅ A user-friendly form for all settings
- ✅ "Test Connection" button to verify your backend works
- ✅ Real-time validation (catches mistakes before you save!)
- ✅ Helpful hints for each setting
- ✅ "Save & Restart" button that applies changes automatically

**What you need to fill in:**
1. **Backend URL**: Your Overseerr/Jellyseerr/Ombi URL (like `http://192.168.1.50:5055`)
2. **Backend API Key**: Copy it from your backend's settings
   - **Overseerr/Jellyseerr**: Settings → General → API Key
   - **Ombi**: Settings → Ombi → API Key
3. **Public URL**: Your public HTTPS URL (for voice assistants to reach you)
   - Like `https://overtalkerr.yourdomain.com`
   - You'll set up the reverse proxy next!

After entering everything, click **"Test Connection"** to make sure it works, then click **"Save & Restart"**!

---

### Option 2: Edit Configuration File Directly

Prefer the command line? No problem!

```bash
# Connect to your LXC container
pct enter <CONTAINER_ID>

# Edit the config file
nano /opt/overtalkerr/.env
```

Find these lines and update them:

```bash
# Your media request backend URL (Overseerr, Jellyseerr, or Ombi)
MEDIA_BACKEND_URL=http://your-overseerr-instance:5055

# Your backend API key (get it from Settings → General → API Key)
MEDIA_BACKEND_API_KEY=your-api-key-here

# Your public HTTPS URL (for Alexa/Google/Siri to reach)
PUBLIC_BASE_URL=https://overtalkerr.yourdomain.com
```

Save the file (Ctrl+O, Enter, Ctrl+X in nano), then restart:

```bash
systemctl restart overtalkerr
```

---

### Verify It's Running

Check that everything started up correctly:

```bash
systemctl status overtalkerr
```

You should see something like:
```
● overtalkerr.service - Overtalkerr - Voice Assistant for Media Requests
   Loaded: loaded (/etc/systemd/system/overtalkerr.service; enabled)
   Active: active (running) since ...
```

If you see `active (running)`, you're golden! 🎉

---

## What You Can Access Now

Your new Overtalkerr instance has these endpoints ready:

- **⚙️ Configuration UI**: `http://YOUR-LXC-IP:5000/config` - **Start here first!**
- **🧪 Test Interface**: `http://YOUR-LXC-IP:5000/test` - Try voice requests from your browser!
- **❤️ Health Check**: `http://YOUR-LXC-IP:5000/test/info` - Check if everything is healthy
- **🔌 API Endpoint**: `http://YOUR-LXC-IP:5000/` - For Alexa/Google/Siri to connect to

Try opening the test interface and searching for a movie to make sure your backend connection works!

---

## Setting Up HTTPS (Required for Voice Assistants!)

Alexa, Google Assistant, and Siri all require HTTPS connections. You'll need to set up a reverse proxy with a valid SSL certificate.

> **💡 Don't panic!** If you're already using Nginx Proxy Manager (NPM) or similar, this is super easy!

### Using Nginx Proxy Manager (Easiest!)

1. Open Nginx Proxy Manager
2. Click **"Add Proxy Host"**
3. Fill in the details:
   - **Domain Names**: `overtalkerr.yourdomain.com` (whatever subdomain you want)
   - **Scheme**: `http` (yes, HTTP - we're proxying to the LXC)
   - **Forward Hostname/IP**: Your LXC container's IP
   - **Forward Port**: `5000`
4. Go to the **SSL** tab:
   - Enable **"Force SSL"**
   - Request a new Let's Encrypt certificate
5. Save!

Now update your `.env` with the new HTTPS URL:
```bash
PUBLIC_BASE_URL=https://overtalkerr.yourdomain.com
```

Restart: `systemctl restart overtalkerr`

Done! Now voice assistants can reach your server securely! 🔒

### Using Nginx Directly

If you're using plain Nginx, here's a config snippet:

```nginx
server {
    listen 443 ssl http2;
    server_name overtalkerr.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://YOUR-LXC-IP:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Updating Overtalkerr

Got a notification that there's a new version? Updating is easy - just run the install script again!

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/mscodemonkey/overtalkerr/main/ct/overtalkerr.sh)"
```

The script is smart - it will:
1. ✅ Detect that Overtalkerr is already installed
2. ✅ Stop the service gracefully
3. ✅ Create a backup of your current installation (just in case!)
4. ✅ Pull the latest code from GitHub
5. ✅ Update Python dependencies
6. ✅ Run any database migrations if needed
7. ✅ Restart the service with the new version

**Important:** Your `.env` configuration is preserved! You won't lose your settings.

---

## Managing Your Container

### Start/Stop/Restart the Service

```bash
# Stop Overtalkerr
systemctl stop overtalkerr

# Start Overtalkerr
systemctl start overtalkerr

# Restart Overtalkerr (after config changes)
systemctl restart overtalkerr

# Check if it's running
systemctl status overtalkerr
```

### View the Logs

Logs are super helpful for troubleshooting!

```bash
# Watch logs in real-time
journalctl -u overtalkerr -f

# See the last 100 lines
journalctl -u overtalkerr -n 100

# See logs since the last boot
journalctl -u overtalkerr -b
```

### Access the Container Shell

From Proxmox VE Shell:

```bash
pct enter <CONTAINER_ID>
```

Or just use the **Console** button in the Proxmox web UI!

---

## File Locations (For Reference)

Everything lives in `/opt/overtalkerr/`:

- **Application Code**: `/opt/overtalkerr/`
- **Configuration File**: `/opt/overtalkerr/.env` - Your settings live here!
- **Database**: `/opt/overtalkerr/data/overtalkerr.db` - Conversation state
- **Virtual Environment**: `/opt/overtalkerr/venv/` - Python dependencies
- **Systemd Service**: `/etc/systemd/system/overtalkerr.service`
- **Logs**: `journalctl -u overtalkerr` or `/opt/overtalkerr/logs/` (if file logging is enabled)

---

## Troubleshooting

### "The service won't start!"

Check what went wrong:

```bash
# See the service status
systemctl status overtalkerr

# View detailed logs (last 50 lines)
journalctl -u overtalkerr -n 50
```

**Common issues:**
1. **Missing `.env` configuration** - Did you configure your backend URL and API key?
2. **Database permissions** - Usually fixed by restarting the service
3. **Port 5000 already in use** - Is something else using that port?

---

### "Can't connect to my backend!"

Test the connection manually:

```bash
# For Overseerr/Jellyseerr:
curl -H "X-Api-Key: YOUR-API-KEY" "http://your-backend:5055/api/v1/status"

# For Ombi:
curl -H "ApiKey: YOUR-API-KEY" "http://your-backend:3579/api/v1/Status"
```

If this fails, the problem is network connectivity or a wrong URL/API key.

---

### "I need to reset everything!"

No problem, here's how to start fresh:

```bash
# Stop the service
systemctl stop overtalkerr

# Backup your current config (just in case)
cp /opt/overtalkerr/.env /opt/overtalkerr/.env.backup

# Delete the database (you'll lose conversation history)
rm /opt/overtalkerr/data/overtalkerr.db

# Restart
systemctl start overtalkerr
```

The database will be recreated automatically!

---

## Advanced Options

When you run the install script, it asks if you want **"Default"** or **"Advanced"** settings.

Choose **Advanced** if you want to customize:
- Container ID number
- Hostname
- Disk size (need more space for logs?)
- CPU cores (running on a beefy server?)
- RAM allocation
- Network settings (static IP, bridge, VLAN tag)
- SSH access
- And more!

Most people are fine with the defaults, but the option is there if you need it!

---

## Uninstalling

Changed your mind? No hard feelings! Here's how to remove Overtalkerr:

**Option 1: Remove just the app (keep the LXC container)**

```bash
# Stop and disable the service
systemctl stop overtalkerr
systemctl disable overtalkerr

# Remove the service file
rm /etc/systemd/system/overtalkerr.service
systemctl daemon-reload

# Remove the application
rm -rf /opt/overtalkerr
```

**Option 2: Delete the entire LXC container (easiest)**

Just delete the container from the Proxmox web UI. Done!

---

## Need Help?

Stuck on something?

1. **Check the logs first** - `journalctl -u overtalkerr -n 100`
2. **Read the main docs:**
   - 📚 [Main Documentation](../README.md)
   - 🔧 [Backend Configuration](connect_to_request_apps.md)
   - 🔍 [Enhanced Search Features](enhanced_search.md)
3. **Open a GitHub issue** - I'm happy to help! [github.com/mscodemonkey/overtalkerr/issues](https://github.com/mscodemonkey/overtalkerr/issues)

---

## Credits

Big thanks to the folks at [community-scripts/ProxmoxVE](https://github.com/community-scripts/ProxmoxVE) for inspiring the installation script format! Their scripts are awesome, and I wanted to make Overtalkerr just as easy to install.

---

**Happy voice requesting! Your Proxmox homelab just got a whole lot cooler! 🎬🏠✨**
