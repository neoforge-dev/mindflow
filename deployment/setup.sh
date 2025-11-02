#!/bin/bash

# MindFlow Server Setup Script
# Run this script on a fresh Ubuntu 22.04 LTS server
# Usage: sudo bash setup.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

log_info "Starting MindFlow server setup..."

# ============================================================================
# SYSTEM UPDATE
# ============================================================================

log_info "Updating system packages..."
apt-get update
apt-get upgrade -y

# ============================================================================
# INSTALL DEPENDENCIES
# ============================================================================

log_info "Installing system dependencies..."
apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw \
    fail2ban \
    unattended-upgrades \
    htop \
    vim

# ============================================================================
# INSTALL PYTHON 3.11
# ============================================================================

log_info "Installing Python 3.11..."
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip

# Set Python 3.11 as default
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

log_info "Python version: $(python3 --version)"

# ============================================================================
# INSTALL UV (Python Package Manager)
# ============================================================================

log_info "Installing uv package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Make uv available system-wide
ln -sf $HOME/.cargo/bin/uv /usr/local/bin/uv

log_info "uv version: $(uv --version)"

# ============================================================================
# INSTALL POSTGRESQL 15
# ============================================================================

log_info "Installing PostgreSQL 15..."
sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt-get update
apt-get install -y postgresql-15 postgresql-contrib-15

# Start PostgreSQL
systemctl start postgresql
systemctl enable postgresql

log_info "PostgreSQL version: $(sudo -u postgres psql --version)"

# ============================================================================
# INSTALL NGINX
# ============================================================================

log_info "Installing Nginx..."
apt-get install -y nginx

# Start Nginx
systemctl start nginx
systemctl enable nginx

log_info "Nginx version: $(nginx -v 2>&1 | cut -d'/' -f2)"

# ============================================================================
# INSTALL CERTBOT (Let's Encrypt)
# ============================================================================

log_info "Installing Certbot for SSL certificates..."
apt-get install -y certbot python3-certbot-nginx

# ============================================================================
# CONFIGURE FIREWALL
# ============================================================================

log_info "Configuring firewall (UFW)..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

log_info "Firewall status:"
ufw status

# ============================================================================
# CONFIGURE FAIL2BAN
# ============================================================================

log_info "Configuring fail2ban..."
systemctl start fail2ban
systemctl enable fail2ban

# Create jail configuration for SSH
cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
EOF

systemctl restart fail2ban

log_info "fail2ban configured for SSH protection"

# ============================================================================
# CONFIGURE AUTOMATIC SECURITY UPDATES
# ============================================================================

log_info "Configuring automatic security updates..."
cat > /etc/apt/apt.conf.d/50unattended-upgrades <<EOF
Unattended-Upgrade::Allowed-Origins {
    "\${distro_id}:\${distro_codename}-security";
    "\${distro_id}ESMApps:\${distro_codename}-apps-security";
    "\${distro_id}ESM:\${distro_codename}-infra-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

cat > /etc/apt/apt.conf.d/20auto-upgrades <<EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

log_info "Automatic security updates configured"

# ============================================================================
# CREATE DEPLOY USER
# ============================================================================

log_info "Creating deploy user..."
if id "deploy" &>/dev/null; then
    log_warn "User 'deploy' already exists, skipping creation"
else
    useradd -m -s /bin/bash deploy
    log_info "User 'deploy' created"
fi

# ============================================================================
# SETUP APPLICATION DIRECTORY
# ============================================================================

log_info "Creating application directories..."
mkdir -p /opt/mindflow
mkdir -p /opt/backups/mindflow
mkdir -p /var/log/mindflow
mkdir -p /var/www/certbot

# Set ownership
chown -R deploy:deploy /opt/mindflow
chown -R deploy:deploy /opt/backups/mindflow
chown -R deploy:deploy /var/log/mindflow

log_info "Application directories created"

# ============================================================================
# SETUP LOG ROTATION
# ============================================================================

log_info "Configuring log rotation..."
cat > /etc/logrotate.d/mindflow <<EOF
/var/log/mindflow/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 deploy deploy
    sharedscripts
    postrotate
        systemctl reload mindflow >/dev/null 2>&1 || true
    endscript
}

/var/log/nginx/mindflow_*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        systemctl reload nginx >/dev/null 2>&1 || true
    endscript
}
EOF

log_info "Log rotation configured"

# ============================================================================
# SUMMARY
# ============================================================================

log_info "=========================================="
log_info "Server setup complete!"
log_info "=========================================="
log_info ""
log_info "Installed components:"
log_info "  - Python 3.11"
log_info "  - uv package manager"
log_info "  - PostgreSQL 15"
log_info "  - Nginx"
log_info "  - Certbot (Let's Encrypt)"
log_info "  - UFW firewall"
log_info "  - fail2ban"
log_info ""
log_info "Next steps:"
log_info "  1. Setup SSH key for deploy user:"
log_info "     sudo -u deploy mkdir -p /home/deploy/.ssh"
log_info "     sudo -u deploy vim /home/deploy/.ssh/authorized_keys"
log_info "     sudo chmod 700 /home/deploy/.ssh"
log_info "     sudo chmod 600 /home/deploy/.ssh/authorized_keys"
log_info ""
log_info "  2. Clone repository:"
log_info "     sudo -u deploy git clone https://github.com/yourusername/mindflow.git /opt/mindflow"
log_info ""
log_info "  3. Run database migration script:"
log_info "     sudo bash /opt/mindflow/deployment/migrate-db.sh"
log_info ""
log_info "  4. Setup environment file:"
log_info "     sudo -u deploy cp /opt/mindflow/deployment/env.production.template /opt/mindflow/backend/.env.production"
log_info "     sudo -u deploy vim /opt/mindflow/backend/.env.production"
log_info ""
log_info "  5. Install Python dependencies:"
log_info "     cd /opt/mindflow/backend"
log_info "     sudo -u deploy uv venv"
log_info "     sudo -u deploy uv sync"
log_info ""
log_info "  6. Install systemd service:"
log_info "     sudo cp /opt/mindflow/deployment/mindflow.service /etc/systemd/system/"
log_info "     sudo systemctl daemon-reload"
log_info "     sudo systemctl enable mindflow"
log_info "     sudo systemctl start mindflow"
log_info ""
log_info "  7. Configure Nginx and SSL:"
log_info "     sudo cp /opt/mindflow/deployment/nginx.conf /etc/nginx/sites-available/mindflow"
log_info "     # Edit nginx.conf to replace api.yourdomain.com with your domain"
log_info "     sudo ln -s /etc/nginx/sites-available/mindflow /etc/nginx/sites-enabled/"
log_info "     sudo nginx -t"
log_info "     sudo certbot --nginx -d api.yourdomain.com"
log_info "     sudo systemctl reload nginx"
log_info ""
log_info "  8. Setup health monitoring:"
log_info "     sudo -u deploy crontab -e"
log_info "     # Add: */5 * * * * /opt/mindflow/deployment/monitor.sh"
log_info ""
log_info "=========================================="
