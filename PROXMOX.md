# Proxmox Installation Guide

Overtalkerr can be installed on Proxmox VE using a helper script similar to those found at [community-scripts.github.io/ProxmoxVE](https://community-scripts.github.io/ProxmoxVE/).

## Quick Install

To create a new Overtalkerr LXC container on Proxmox VE, run this command from your Proxmox VE Shell:

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/mscodemonkey/overtalkerr/main/ct/overtalkerr.sh)"
```

## What Gets Installed

The script will:

1. ✅ Create an unprivileged Debian 12 LXC container
2. ✅ Install Python 3.11+ and required dependencies
3. ✅ Clone the Overtalkerr repository to `/opt/overtalkerr`
4. ✅ Set up a Python virtual environment
5. ✅ Install all Python dependencies
6. ✅ Create a systemd service for automatic startup
7. ✅ Configure Gunicorn as the production WSGI server
8. ✅ Generate a secure random SECRET_KEY
9. ✅ Set up logging and data directories

## Default Container Settings

- **OS**: Debian 12 (Bookworm)
- **Type**: Unprivileged Container
- **CPU Cores**: 2
- **RAM**: 1024 MB (1 GB)
- **Disk**: 4 GB
- **Tags**: media, voice-assistant
- **Port**: 5000

## Post-Installation Configuration

After installation, you **must** configure your backend settings:

### 1. Edit the Configuration File

```bash
nano /opt/overtalkerr/.env
```

### 2. Update Required Settings

```bash
# Your media request backend URL (Overseerr, Jellyseerr, or Ombi)
MEDIA_BACKEND_URL=http://your-overseerr-instance:5055

# Your backend API key
MEDIA_BACKEND_API_KEY=your-api-key-here

# Your public HTTPS URL (for Alexa/Google/Siri to reach)
PUBLIC_BASE_URL=https://overtalkerr.yourdomain.com
```

**Where to find your API key:**
- **Overseerr/Jellyseerr**: Settings → General → API Key
- **Ombi**: Settings → Ombi → API Key

### 3. Restart the Service

```bash
systemctl restart overtalkerr
```

### 4. Verify It's Running

```bash
systemctl status overtalkerr
```

You should see:
```
● overtalkerr.service - Overtalkerr - Voice Assistant for Media Requests
   Loaded: loaded (/etc/systemd/system/overtalkerr.service; enabled)
   Active: active (running)
```

## Accessing Overtalkerr

After installation:

- **Web UI Test Interface**: `http://YOUR-LXC-IP:5000/test`
- **Health Check**: `http://YOUR-LXC-IP:5000/test/info`
- **API Endpoint**: `http://YOUR-LXC-IP:5000/`

## Updating Overtalkerr

To update to the latest version, run the installation script again:

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/mscodemonkey/overtalkerr/main/ct/overtalkerr.sh)"
```

The update process will:
1. ✅ Detect existing installation
2. ✅ Stop the service
3. ✅ Create a backup of your current installation
4. ✅ Pull latest code from GitHub
5. ✅ Update Python dependencies
6. ✅ Run database migrations (if needed)
7. ✅ Restart the service

**Note**: Your `.env` configuration file is preserved during updates.

## Advanced Options

When running the installation script, you can choose **Advanced** mode to customize:

- Container ID
- Hostname
- Disk size
- CPU cores
- RAM allocation
- Network settings (static IP, bridge, VLAN)
- SSH access
- And more...

## Container Management

### Start/Stop/Restart

```bash
# Stop Overtalkerr
systemctl stop overtalkerr

# Start Overtalkerr
systemctl start overtalkerr

# Restart Overtalkerr
systemctl restart overtalkerr

# Check status
systemctl status overtalkerr
```

### View Logs

```bash
# Real-time logs
journalctl -u overtalkerr -f

# Last 100 lines
journalctl -u overtalkerr -n 100

# Logs since boot
journalctl -u overtalkerr -b
```

### Access Container Shell

From Proxmox VE Shell:

```bash
pct enter <CONTAINER_ID>
```

Or use the Proxmox web UI: Container → Console

## File Locations

- **Application**: `/opt/overtalkerr/`
- **Configuration**: `/opt/overtalkerr/.env`
- **Database**: `/opt/overtalkerr/data/overtalkerr.db`
- **Virtual Environment**: `/opt/overtalkerr/venv/`
- **Systemd Service**: `/etc/systemd/system/overtalkerr.service`
- **Logs**: `journalctl -u overtalkerr` or `/opt/overtalkerr/logs/` (if file logging enabled)

## Reverse Proxy Setup

For production use with Alexa/Google Assistant/Siri, you need HTTPS. Set up a reverse proxy:

### Using Nginx Proxy Manager (NPM)

1. In NPM, add a new Proxy Host
2. **Domain Names**: `overtalkerr.yourdomain.com`
3. **Scheme**: `http`
4. **Forward Hostname/IP**: `<LXC-IP>`
5. **Forward Port**: `5000`
6. **SSL**: Enable "Force SSL" and request a Let's Encrypt certificate
7. Save

### Using Nginx Directly

```nginx
server {
    listen 443 ssl http2;
    server_name overtalkerr.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://<LXC-IP>:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Update .env After Reverse Proxy

```bash
PUBLIC_BASE_URL=https://overtalkerr.yourdomain.com
```

Then restart: `systemctl restart overtalkerr`

## Troubleshooting

### Service Won't Start

```bash
# Check service status
systemctl status overtalkerr

# View detailed logs
journalctl -u overtalkerr -n 50

# Common issues:
# 1. Missing or invalid .env configuration
# 2. Database permissions
# 3. Port 5000 already in use
```

### Can't Connect to Backend

```bash
# Test backend connectivity from LXC
curl -H "X-Api-Key: YOUR-API-KEY" "http://your-backend:5055/api/v1/status"

# Or for Ombi:
curl -H "ApiKey: YOUR-API-KEY" "http://your-backend:3579/api/v1/Status"
```

### Check Configuration

```bash
# View current configuration (API keys will be visible!)
cat /opt/overtalkerr/.env

# Validate Python dependencies
cd /opt/overtalkerr
/opt/overtalkerr/venv/bin/pip check
```

### Reset to Defaults

If you need to start fresh:

```bash
# Stop service
systemctl stop overtalkerr

# Backup current config
cp /opt/overtalkerr/.env /opt/overtalkerr/.env.backup

# Delete database (will lose conversation state)
rm /opt/overtalkerr/data/overtalkerr.db

# Restart service
systemctl start overtalkerr
```

## Uninstall

To completely remove Overtalkerr:

```bash
# Stop and disable service
systemctl stop overtalkerr
systemctl disable overtalkerr

# Remove service file
rm /etc/systemd/system/overtalkerr.service
systemctl daemon-reload

# Remove application directory
rm -rf /opt/overtalkerr

# (Optional) Delete the entire LXC container from Proxmox
```

Or simply delete the LXC container from the Proxmox web UI.

## Support & Documentation

- 📚 **Main Documentation**: [README.md](README.md)
- 🔧 **Backend Configuration**: [BACKENDS.md](BACKENDS.md)
- 🔍 **Search Features**: [ENHANCED_SEARCH.md](ENHANCED_SEARCH.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/mscodemonkey/overtalkerr/issues)

## Credits

Installation script format inspired by [community-scripts/ProxmoxVE](https://github.com/community-scripts/ProxmoxVE).
