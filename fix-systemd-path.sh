#!/bin/bash
# Fix systemd service PATH to include git and systemctl for auto-update feature
# Run this on existing Overtalkerr installations to enable the auto-update button

echo "🔧 Fixing Overtalkerr systemd service PATH..."

# Backup the current service file
cp /etc/systemd/system/overtalkerr.service /etc/systemd/system/overtalkerr.service.backup

# Update the PATH in the service file
sed -i 's|Environment="PATH=/opt/overtalkerr/venv/bin"|Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/overtalkerr/venv/bin"|g' /etc/systemd/system/overtalkerr.service

# Reload systemd and restart service
systemctl daemon-reload
systemctl restart overtalkerr

echo "✅ Done! The auto-update feature should now work."
echo "   Backup saved to: /etc/systemd/system/overtalkerr.service.backup"
