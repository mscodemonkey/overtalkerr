#!/bin/bash
#
# Overtalkerr Update Script - Proxmox LXC Installation
#
# This script updates Overtalkerr when installed in a Proxmox LXC container
# It backs up your data before updating.
#

set -e  # Exit on error

INSTALL_DIR="/opt/overtalkerr"
BACKUP_DIR="$INSTALL_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SERVICE_NAME="overtalkerr"

echo "========================================="
echo "  Overtalkerr Proxmox Update Script"
echo "========================================="
echo ""

# Check if we're in the right location
if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ Error: Overtalkerr installation not found at $INSTALL_DIR"
    exit 1
fi

cd "$INSTALL_DIR"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: This script must be run as root"
    echo "   Please run: sudo $0"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Step 1: Creating backup..."
echo "─────────────────────────────"

# Backup .env file
if [ -f "$INSTALL_DIR/.env" ]; then
    cp "$INSTALL_DIR/.env" "$BACKUP_DIR/.env.$TIMESTAMP"
    echo "✓ Backed up .env file"
fi

# Backup database
if [ -f "$INSTALL_DIR/data/overtalkerr.db" ]; then
    mkdir -p "$BACKUP_DIR/data"
    cp "$INSTALL_DIR/data/overtalkerr.db" "$BACKUP_DIR/data/overtalkerr.db.$TIMESTAMP"
    echo "✓ Backed up database"
fi

if [ -d "$INSTALL_DIR/data" ]; then
    cp -r "$INSTALL_DIR/data" "$BACKUP_DIR/data.$TIMESTAMP"
    echo "✓ Backed up data directory"
fi

# Get current version
CURRENT_VERSION=$(cat "$INSTALL_DIR/VERSION" 2>/dev/null || echo "unknown")
echo "Current version: $CURRENT_VERSION"

echo ""
echo "Step 2: Fetching latest changes..."
echo "─────────────────────────────────────"

# Fetch latest changes
git fetch origin

# Check if there are updates
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u} 2>/dev/null || git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✓ Already up to date!"
    exit 0
fi

# Show what will be updated
echo ""
echo "Changes to be applied:"
git log --oneline $LOCAL..$REMOTE

echo ""
read -p "Continue with update? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Update cancelled."
    exit 0
fi

echo ""
echo "Step 3: Stopping service..."
echo "────────────────────────────"
systemctl stop $SERVICE_NAME
echo "✓ Service stopped"

echo ""
echo "Step 4: Updating code..."
echo "────────────────────────────"
git pull origin main
echo "✓ Code updated"

echo ""
echo "Step 5: Updating dependencies..."
echo "─────────────────────────────────────"

if [ -d "$INSTALL_DIR/venv" ]; then
    source "$INSTALL_DIR/venv/bin/activate"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    deactivate
    echo "✓ Dependencies updated"
else
    echo "⚠️  Virtual environment not found - creating new one"
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    deactivate
    echo "✓ Virtual environment created and dependencies installed"
fi

# Get new version
NEW_VERSION=$(cat "$INSTALL_DIR/VERSION" 2>/dev/null || echo "unknown")

echo ""
echo "Step 6: Starting service..."
echo "────────────────────────────"
systemctl start $SERVICE_NAME
sleep 3

if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✓ Service started successfully"
else
    echo "❌ Service failed to start"
    echo "   Check logs: journalctl -u $SERVICE_NAME -n 50"
    echo ""
    echo "Attempting rollback..."

    # Restore backup
    if [ -f "$BACKUP_DIR/.env.$TIMESTAMP" ]; then
        cp "$BACKUP_DIR/.env.$TIMESTAMP" "$INSTALL_DIR/.env"
    fi
    if [ -f "$BACKUP_DIR/data/overtalkerr.db.$TIMESTAMP" ]; then
        cp "$BACKUP_DIR/data/overtalkerr.db.$TIMESTAMP" "$INSTALL_DIR/data/overtalkerr.db"
    fi

    git reset --hard $LOCAL

    systemctl start $SERVICE_NAME

    echo "❌ Update failed - rolled back to previous version"
    exit 1
fi

echo ""
echo "========================================="
echo "  ✓ Update Complete!"
echo "========================================="
echo ""
echo "Updated from: $CURRENT_VERSION"
echo "         to: $NEW_VERSION"
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Service status:"
systemctl status $SERVICE_NAME --no-pager -l
echo ""
echo "Check status at: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
