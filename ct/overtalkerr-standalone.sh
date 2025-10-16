#!/usr/bin/env bash

# Overtalkerr Proxmox LXC Installation Script
# Standalone version - does not require community-scripts framework
# Copyright (c) 2025 Martin Steven (mscodemonkey)
# License: MIT
# Source: https://github.com/mscodemonkey/overtalkerr

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
msg_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

msg_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

msg_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

msg_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if running on Proxmox
if ! command -v pveversion &> /dev/null; then
    msg_error "This script must be run on a Proxmox VE host"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    msg_error "This script must be run as root"
    exit 1
fi

# Configuration
APP="Overtalkerr"
CTID_DEFAULT=$(pvesh get /cluster/nextid)
HOSTNAME="overtalkerr"
DISK_SIZE="4"
CORES="2"
RAM="1024"
BRIDGE="vmbr0"
OS_TYPE="debian"
OS_VERSION="12"

# Auto-detect available storage for containers
# Try common storage options in order of preference
STORAGE=""
for storage in "local-lxc" "local" "local-zfs" "local-btrfs"; do
    if pvesm status | grep -q "^${storage} "; then
        # Check if this storage supports container content
        if pvesm status | grep "^${storage} " | grep -q "rootdir\|images"; then
            STORAGE="$storage"
            break
        fi
    fi
done

if [ -z "$STORAGE" ]; then
    msg_error "No suitable storage found for containers"
    msg_info "Available storage:"
    pvesm status
    exit 1
fi

# Show banner
clear
echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}     Overtalkerr LXC Container Installation        ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# Prompt for container ID
read -p "Enter Container ID [${CTID_DEFAULT}]: " CTID
CTID=${CTID:-$CTID_DEFAULT}

# Validate CTID
if ! [[ "$CTID" =~ ^[0-9]+$ ]]; then
    msg_error "Container ID must be a number"
    exit 1
fi

# Check if CTID already exists
if pct status "$CTID" &>/dev/null; then
    msg_error "Container ID $CTID already exists"
    exit 1
fi

# Show configuration
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Container ID: ${GREEN}${CTID}${NC}"
echo -e "  Hostname: ${GREEN}${HOSTNAME}${NC}"
echo -e "  OS: ${GREEN}Debian ${OS_VERSION}${NC}"
echo -e "  Storage: ${GREEN}${STORAGE}${NC}"
echo -e "  Disk: ${GREEN}${DISK_SIZE}GB${NC}"
echo -e "  Cores: ${GREEN}${CORES}${NC}"
echo -e "  RAM: ${GREEN}${RAM}MB${NC}"
echo -e "  Bridge: ${GREEN}${BRIDGE}${NC}"
echo ""

# Confirm
read -p "Continue with installation? [Y/n]: " CONFIRM
CONFIRM=${CONFIRM:-Y}
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    msg_warn "Installation cancelled"
    exit 0
fi

echo ""

# Download Debian template
msg_info "Downloading Debian ${OS_VERSION} template..."
TEMPLATE="debian-${OS_VERSION}-standard_${OS_VERSION}.7-1_amd64.tar.zst"
if ! pveam list local | grep -q "$TEMPLATE"; then
    pveam download local "$TEMPLATE" || {
        msg_error "Failed to download template"
        exit 1
    }
fi
msg_ok "Template ready"

# Create container
msg_info "Creating LXC container..."
pct create "$CTID" local:vztmpl/"$TEMPLATE" \
    --hostname "$HOSTNAME" \
    --cores "$CORES" \
    --memory "$RAM" \
    --swap 512 \
    --rootfs "$STORAGE:$DISK_SIZE" \
    --net0 name=eth0,bridge="$BRIDGE",firewall=1,ip=dhcp \
    --features nesting=1 \
    --unprivileged 1 \
    --onboot 1 \
    --start 0 || {
        msg_error "Failed to create container"
        exit 1
    }
msg_ok "Container created"

# Start container
msg_info "Starting container..."
pct start "$CTID" || {
    msg_error "Failed to start container"
    exit 1
}

# Wait for container to be ready
sleep 5

# Get container IP
msg_info "Waiting for network..."
for i in {1..30}; do
    IP=$(pct exec "$CTID" -- hostname -I | awk '{print $1}' 2>/dev/null || echo "")
    if [ -n "$IP" ]; then
        break
    fi
    sleep 2
done

if [ -z "$IP" ]; then
    msg_warn "Could not determine IP address, continuing anyway..."
    IP="<pending>"
fi

msg_ok "Container is running"

# Install dependencies
msg_info "Installing dependencies..."
pct exec "$CTID" -- bash -c "
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        curl \
        sudo \
        git \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
        build-essential
" || {
    msg_error "Failed to install dependencies"
    exit 1
}
msg_ok "Dependencies installed"

# Create Python virtual environment
msg_info "Setting up Python virtual environment..."
pct exec "$CTID" -- bash -c "python3 -m venv /opt/overtalkerr/venv" || {
    msg_error "Failed to create virtual environment"
    exit 1
}
msg_ok "Virtual environment created"

# Clone repository and install
msg_info "Installing Overtalkerr..."
pct exec "$CTID" -- bash -c "
    cd /opt && \
    git clone https://github.com/mscodemonkey/overtalkerr.git && \
    cd overtalkerr && \
    /opt/overtalkerr/venv/bin/pip install --upgrade pip && \
    /opt/overtalkerr/venv/bin/pip install -r requirements.txt && \
    /opt/overtalkerr/venv/bin/pip install gunicorn
" || {
    msg_error "Failed to install Overtalkerr"
    exit 1
}
msg_ok "Overtalkerr installed"

# Create environment configuration
msg_info "Creating environment configuration..."
pct exec "$CTID" -- bash -c "cat > /opt/overtalkerr/.env <<EOF
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=\$(openssl rand -hex 32)

# Public base URL (update this with your actual URL)
PUBLIC_BASE_URL=https://overtalkerr.yourdomain.com

# Media Request Backend Configuration
# Supports: Overseerr, Jellyseerr, and Ombi
# REQUIRED: Update these with your backend details
MEDIA_BACKEND_URL=http://your-backend-url:5055
MEDIA_BACKEND_API_KEY=your-api-key-here

# Mock mode for testing (set to false for production)
MOCK_BACKEND=false

# Database Configuration
DATABASE_URL=sqlite:///./data/overtalkerr.db
SESSION_TTL_HOURS=24

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
"
msg_ok "Environment configuration created"

# Create data directory
msg_info "Setting up data directory..."
pct exec "$CTID" -- bash -c "
    mkdir -p /opt/overtalkerr/data && \
    chown -R root:root /opt/overtalkerr && \
    chmod 755 /opt/overtalkerr
"
msg_ok "Data directory created"

# Create systemd service
msg_info "Creating systemd service..."
pct exec "$CTID" -- bash -c 'cat > /etc/systemd/system/overtalkerr.service <<EOF
[Unit]
Description=Overtalkerr - Voice Assistant for Media Requests
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/overtalkerr
Environment="PATH=/opt/overtalkerr/venv/bin"
ExecStart=/opt/overtalkerr/venv/bin/gunicorn \\
    --bind 0.0.0.0:5000 \\
    --workers 2 \\
    --worker-class gthread \\
    --threads 4 \\
    --timeout 120 \\
    --access-logfile - \\
    --error-logfile - \\
    --log-level info \\
    app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
'
pct exec "$CTID" -- systemctl daemon-reload
pct exec "$CTID" -- systemctl enable overtalkerr.service
pct exec "$CTID" -- systemctl start overtalkerr.service
msg_ok "Systemd service created and started"

# Cleanup
msg_info "Cleaning up..."
pct exec "$CTID" -- bash -c "
    apt-get -y autoremove && \
    apt-get -y autoclean
"
msg_ok "Cleanup complete"

# Show completion message
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}     Installation Completed Successfully!           ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Container Details:${NC}"
echo -e "  ID: ${GREEN}${CTID}${NC}"
echo -e "  Hostname: ${GREEN}${HOSTNAME}${NC}"
echo -e "  IP Address: ${GREEN}${IP}${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: You must configure your backend settings!${NC}"
echo -e "   ${BLUE}1.${NC} Access the web UI: ${GREEN}http://${IP}:5000${NC}"
echo -e "   ${BLUE}2.${NC} Go to configuration: ${GREEN}http://${IP}:5000/config${NC}"
echo -e "   ${BLUE}3.${NC} Update MEDIA_BACKEND_URL with your Overseerr/Jellyseerr/Ombi URL"
echo -e "   ${BLUE}4.${NC} Update MEDIA_BACKEND_API_KEY with your API key"
echo -e "   ${BLUE}5.${NC} Update PUBLIC_BASE_URL with your public HTTPS URL"
echo ""
echo -e "${BLUE}Access Points:${NC}"
echo -e "  Dashboard: ${GREEN}http://${IP}:5000${NC}"
echo -e "  Configuration: ${GREEN}http://${IP}:5000/config${NC}"
echo -e "  Test Interface: ${GREEN}http://${IP}:5000/test${NC}"
echo ""
echo -e "${BLUE}Documentation:${NC} ${GREEN}https://github.com/mscodemonkey/overtalkerr${NC}"
echo ""
