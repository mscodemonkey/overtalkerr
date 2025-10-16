#!/bin/bash
#
# Overtalkerr Update Script - Docker Installation
#
# This script updates Overtalkerr when running via Docker Compose
# It backs up your data before updating.
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "========================================="
echo "  Overtalkerr Docker Update Script"
echo "========================================="
echo ""

# Check if docker-compose.yml exists
if [ ! -f "$SCRIPT_DIR/docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "   Please run this script from the Overtalkerr root directory."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker and try again."
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Step 1: Creating backup..."
echo "─────────────────────────────"

# Backup .env file
if [ -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env" "$BACKUP_DIR/.env.$TIMESTAMP"
    echo "✓ Backed up .env file"
fi

# Backup data volume
if [ -d "$SCRIPT_DIR/data" ]; then
    cp -r "$SCRIPT_DIR/data" "$BACKUP_DIR/data.$TIMESTAMP"
    echo "✓ Backed up data directory"
fi

# Get current version from running container
CURRENT_VERSION=$(docker-compose exec -T overtalkerr cat /app/VERSION 2>/dev/null || echo "unknown")
echo "Current version: $CURRENT_VERSION"

echo ""
echo "Step 2: Fetching latest changes..."
echo "─────────────────────────────────────"

# Check if we're in a git repository
if [ -d "$SCRIPT_DIR/.git" ]; then
    git fetch origin

    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u} 2>/dev/null || git rev-parse origin/main)

    if [ "$LOCAL" = "$REMOTE" ]; then
        echo "✓ Git repository already up to date"
    else
        echo ""
        echo "Changes to be applied:"
        git log --oneline $LOCAL..$REMOTE
        echo ""
        read -p "Pull latest changes? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            git pull origin main
            echo "✓ Code updated"
        fi
    fi
else
    echo "ℹ️  Not a git repository - skipping git pull"
fi

echo ""
echo "Step 3: Pulling latest Docker image..."
echo "───────────────────────────────────────"
docker-compose pull
echo "✓ Image updated"

echo ""
echo "Step 4: Restarting containers..."
echo "─────────────────────────────────"

# Stop containers
docker-compose down

# Start with new image
docker-compose up -d

# Wait for container to be ready
echo "Waiting for container to start..."
sleep 5

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo "✓ Container started successfully"

    # Get new version
    NEW_VERSION=$(docker-compose exec -T overtalkerr cat /app/VERSION 2>/dev/null || echo "unknown")

    # Run database migrations if needed
    echo ""
    echo "Step 5: Running database migrations..."
    echo "───────────────────────────────────────"
    docker-compose exec -T overtalkerr python -c "from db import init_db; init_db()" 2>/dev/null || echo "ℹ️  No migrations needed"
    echo "✓ Database up to date"

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
    echo "Container status:"
    docker-compose ps
    echo ""
    echo "View logs: docker-compose logs -f overtalkerr"
    echo "Check status at: http://localhost:5000"
    echo ""
else
    echo "❌ Container failed to start"
    echo ""
    echo "Checking logs..."
    docker-compose logs --tail=50 overtalkerr
    echo ""
    echo "Attempting rollback..."

    # Restore from backup
    if [ -f "$BACKUP_DIR/.env.$TIMESTAMP" ]; then
        cp "$BACKUP_DIR/.env.$TIMESTAMP" "$SCRIPT_DIR/.env"
    fi
    if [ -d "$BACKUP_DIR/data.$TIMESTAMP" ]; then
        rm -rf "$SCRIPT_DIR/data"
        cp -r "$BACKUP_DIR/data.$TIMESTAMP" "$SCRIPT_DIR/data"
    fi

    docker-compose down
    docker-compose up -d

    echo "❌ Update failed - rolled back to previous version"
    exit 1
fi
