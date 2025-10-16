#!/bin/bash
#
# Overtalkerr Update Script - Manual Installation
#
# This script updates Overtalkerr when installed manually (not Docker/Proxmox)
# It backs up your configuration and database before updating.
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "========================================="
echo "  Overtalkerr Update Script"
echo "========================================="
echo ""

# Check if we're in a git repository
if [ ! -d "$SCRIPT_DIR/.git" ]; then
    echo "❌ Error: This doesn't appear to be a git repository."
    echo "   Please run this script from the Overtalkerr root directory."
    exit 1
fi

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Warning: Running as root is not recommended."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for systemd service
SERVICE_NAME="overtalkerr"
if systemctl list-units --full -all | grep -q "$SERVICE_NAME.service"; then
    HAS_SERVICE=true
    echo "✓ Found systemd service: $SERVICE_NAME"
else
    HAS_SERVICE=false
    echo "ℹ️  No systemd service found (manual start)"
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo ""
echo "Step 1: Creating backup..."
echo "─────────────────────────────"

# Backup .env file
if [ -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env" "$BACKUP_DIR/.env.$TIMESTAMP"
    echo "✓ Backed up .env file"
fi

# Backup database
if [ -f "$SCRIPT_DIR/overtalkerr.db" ]; then
    cp "$SCRIPT_DIR/overtalkerr.db" "$BACKUP_DIR/overtalkerr.db.$TIMESTAMP"
    echo "✓ Backed up database"
fi

if [ -d "$SCRIPT_DIR/data" ]; then
    cp -r "$SCRIPT_DIR/data" "$BACKUP_DIR/data.$TIMESTAMP"
    echo "✓ Backed up data directory"
fi

echo ""
echo "Step 2: Fetching latest changes..."
echo "─────────────────────────────────────"

# Get current version
CURRENT_VERSION=$(cat "$SCRIPT_DIR/VERSION" 2>/dev/null || echo "unknown")
echo "Current version: $CURRENT_VERSION"

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

# Stop service if running
if [ "$HAS_SERVICE" = true ]; then
    echo ""
    echo "Step 3: Stopping service..."
    echo "────────────────────────────"
    sudo systemctl stop $SERVICE_NAME
    echo "✓ Service stopped"
fi

# Pull latest changes
echo ""
echo "Step 4: Updating code..."
echo "────────────────────────────"
git pull origin main
echo "✓ Code updated"

# Check for new dependencies
echo ""
echo "Step 5: Checking dependencies..."
echo "─────────────────────────────────────"

if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    if [ -d "$SCRIPT_DIR/venv" ]; then
        source "$SCRIPT_DIR/venv/bin/activate"
        pip install -q --upgrade pip
        pip install -q -r requirements.txt
        echo "✓ Dependencies updated"
    else
        echo "⚠️  Virtual environment not found"
        echo "   Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    fi
fi

# Get new version
NEW_VERSION=$(cat "$SCRIPT_DIR/VERSION" 2>/dev/null || echo "unknown")

# Start service if it was running
if [ "$HAS_SERVICE" = true ]; then
    echo ""
    echo "Step 6: Starting service..."
    echo "────────────────────────────"
    sudo systemctl start $SERVICE_NAME
    sleep 2

    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "✓ Service started successfully"
    else
        echo "❌ Service failed to start"
        echo "   Check logs: sudo journalctl -u $SERVICE_NAME -n 50"
        echo ""
        echo "Restoring from backup..."

        # Restore backup
        if [ -f "$BACKUP_DIR/.env.$TIMESTAMP" ]; then
            cp "$BACKUP_DIR/.env.$TIMESTAMP" "$SCRIPT_DIR/.env"
        fi
        if [ -f "$BACKUP_DIR/overtalkerr.db.$TIMESTAMP" ]; then
            cp "$BACKUP_DIR/overtalkerr.db.$TIMESTAMP" "$SCRIPT_DIR/overtalkerr.db"
        fi

        git reset --hard $LOCAL
        sudo systemctl start $SERVICE_NAME

        echo "❌ Update failed - rolled back to previous version"
        exit 1
    fi
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

if [ "$HAS_SERVICE" = false ]; then
    echo "⚠️  Remember to restart Overtalkerr manually!"
    echo ""
fi

echo "Check status at: http://localhost:5000"
echo ""
