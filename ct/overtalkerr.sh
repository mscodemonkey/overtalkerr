#!/usr/bin/env bash
source <(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/misc/build.func)
# Copyright (c) 2025 community-scripts
# Author: Martin Steven (mscodemonkey)
# License: MIT | https://github.com/community-scripts/ProxmoxVE/raw/main/LICENSE
# Source: https://github.com/mscodemonkey/overtalkerr

# App Update Function
function update_script() {
  header_info
  check_container_storage
  check_container_resources

  if [[ ! -d /opt/overtalkerr ]]; then
    msg_error "No ${APP} Installation Found!"
    exit
  fi

  RELEASE=$(curl -s https://api.github.com/repos/mscodemonkey/overtalkerr/releases/latest | grep "tag_name" | awk '{print substr($2, 2, length($2)-3)}')
  if [[ ! -n "$RELEASE" ]]; then
    msg_error "Can't retrieve latest release version!"
    exit
  fi

  msg_info "Stopping ${APP}"
  systemctl stop overtalkerr
  msg_ok "Stopped ${APP}"

  msg_info "Backing up current installation"
  cp -r /opt/overtalkerr /opt/overtalkerr.backup.$(date +%Y%m%d_%H%M%S)
  msg_ok "Backup created"

  msg_info "Updating to ${RELEASE}"
  cd /opt/overtalkerr
  git fetch --all
  git reset --hard origin/main
  git pull origin main

  # Update Python dependencies
  /opt/overtalkerr/venv/bin/pip install --upgrade pip
  /opt/overtalkerr/venv/bin/pip install -r requirements.txt --upgrade
  msg_ok "Updated to ${RELEASE}"

  msg_info "Running database migrations"
  if [[ -f /opt/overtalkerr/migrate_db.py ]]; then
    /opt/overtalkerr/venv/bin/python3 /opt/overtalkerr/migrate_db.py
  fi
  msg_ok "Database migrations complete"

  msg_info "Starting ${APP}"
  systemctl start overtalkerr
  msg_ok "Started ${APP}"

  msg_ok "Updated Successfully!\n"
  exit
}

# App Default Values
APP="Overtalkerr"
var_tags="${var_tags:-media;voice-assistant}"
var_cpu="${var_cpu:-2}"
var_ram="${var_ram:-1024}"
var_disk="${var_disk:-4}"
var_os="${var_os:-debian}"
var_version="${var_version:-12}"
var_unprivileged="${var_unprivileged:-1}"

# App Output & Base Settings
header_info "$APP"
variables
color
catch_errors

# Create & Start LXC
start
build_container
description

msg_info "Installing Dependencies"
$STD apt-get install -y \
  curl \
  sudo \
  git \
  python3 \
  python3-pip \
  python3-venv \
  ca-certificates \
  build-essential
msg_ok "Installed Dependencies"

msg_info "Setting up Python Virtual Environment"
python3 -m venv /opt/overtalkerr/venv
msg_ok "Created Python Virtual Environment"

msg_info "Installing Overtalkerr"
cd /opt
git clone https://github.com/mscodemonkey/overtalkerr.git
cd overtalkerr

# Install Python dependencies in venv
/opt/overtalkerr/venv/bin/pip install --upgrade pip
/opt/overtalkerr/venv/bin/pip install -r requirements.txt
/opt/overtalkerr/venv/bin/pip install gunicorn
msg_ok "Installed Overtalkerr"

msg_info "Creating Environment Configuration"
cat > /opt/overtalkerr/.env <<EOF
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)

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
msg_ok "Created Environment Configuration"

msg_info "Setting up Data Directory"
mkdir -p /opt/overtalkerr/data
chown -R root:root /opt/overtalkerr
chmod 755 /opt/overtalkerr
msg_ok "Created Data Directory"

msg_info "Creating Systemd Service"
cat > /etc/systemd/system/overtalkerr.service <<EOF
[Unit]
Description=Overtalkerr - Voice Assistant for Media Requests
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/overtalkerr
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/overtalkerr/venv/bin"
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

systemctl daemon-reload
systemctl enable --now overtalkerr.service
msg_ok "Created Systemd Service"

motd_ssh
customize

msg_info "Cleaning up"
$STD apt-get -y autoremove
$STD apt-get -y autoclean
msg_ok "Cleaned"

description

msg_ok "Completed Successfully!\n"
echo -e "\n${APP} is now installed and running."
echo -e "\n⚠️  IMPORTANT: You must configure your backend settings!"
echo -e "   1. Edit: ${YW}/opt/overtalkerr/.env${CL}"
echo -e "   2. Update MEDIA_BACKEND_URL with your Overseerr/Jellyseerr/Ombi URL"
echo -e "   3. Update MEDIA_BACKEND_API_KEY with your API key"
echo -e "   4. Update PUBLIC_BASE_URL with your public HTTPS URL"
echo -e "   5. Restart: ${YW}systemctl restart overtalkerr${CL}\n"
echo -e "${APP} should be reachable at ${BL}http://${IP}:5000${CL}"
echo -e "  - Dashboard: ${BL}http://${IP}:5000${CL}"
echo -e "  - Configuration UI: ${BL}http://${IP}:5000/config${CL}"
echo -e "  - Test Interface: ${BL}http://${IP}:5000/test${CL}\n"
echo -e "📚 Documentation: ${BL}https://github.com/mscodemonkey/overtalkerr${CL}"
echo -e "🔧 Configuration Guide: ${BL}https://github.com/mscodemonkey/overtalkerr/blob/main/documentation/connect_to_request_apps.md${CL}\n"
