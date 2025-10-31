#!/bin/bash
#
# MindFlow Production Server Setup Script
#
# This script prepares a fresh Ubuntu 22.04 server for MindFlow deployment
# Run as root or with sudo privileges
#
# Usage: sudo ./setup.sh
#

set -e  # Exit on any error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root or with sudo"
   exit 1
fi

log_info "=== MindFlow Production Server Setup ==="
log_info "This will install: Python 3.11, PostgreSQL 15, Nginx, Certbot, and uv"
echo ""

# Confirmation prompt
read -p "Continue with installation? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "Installation cancelled"
    exit 0
fi

# Update system packages
log_info "Updating system packages..."
apt update
apt upgrade -y
log_success "System packages updated"

# Install basic dependencies
log_info "Installing basic dependencies..."
apt install -y \
    software-properties-common \
    build-essential \
    curl \
    wget \
    git \
    vim \
    htop \
    ufw \
    fail2ban \
    unzip
log_success "Basic dependencies installed"

# Install Python 3.11
log_info "Installing Python 3.11..."
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip
log_success "Python 3.11 installed: $(python3.11 --version)"

# Install PostgreSQL 15
log_info "Installing PostgreSQL 15..."
apt install -y postgresql-15 postgresql-contrib-15 libpq-dev
systemctl enable postgresql
systemctl start postgresql
log_success "PostgreSQL 15 installed: $(psql --version)"

# Install Nginx
log_info "Installing Nginx..."
apt install -y nginx
systemctl enable nginx
systemctl start nginx
log_success "Nginx installed: $(nginx -v 2>&1)"

# Install Certbot for Let's Encrypt
log_info "Installing Certbot..."
apt install -y certbot python3-certbot-nginx
log_success "Certbot installed: $(certbot --version)"

# Install uv (modern Python package manager)
log_info "Installing uv for deploy user..."
if id "deploy" &>/dev/null; then
    sudo -u deploy bash -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'
    log_success "uv installed for deploy user"
else
    log_warn "Deploy user not found, skipping uv installation"
    log_info "Run as deploy user: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# Configure firewall (UFW)
log_info "Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
log_success "Firewall configured"
ufw status

# Configure fail2ban for SSH protection
log_info "Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban
log_success "fail2ban configured and started"

# Create mindflow application directory structure
log_info "Creating application directory structure..."
mkdir -p /opt/mindflow
mkdir -p /var/log/mindflow
mkdir -p /opt/backups/mindflow

# Set ownership if deploy user exists
if id "deploy" &>/dev/null; then
    chown -R deploy:deploy /opt/mindflow
    chown -R deploy:deploy /var/log/mindflow
    chown -R deploy:deploy /opt/backups/mindflow
    log_success "Application directories created and owned by deploy user"
else
    log_warn "Deploy user not found"
    log_info "Create deploy user with: adduser deploy && usermod -aG sudo deploy"
fi

# Configure automatic security updates
log_info "Configuring automatic security updates..."
apt install -y unattended-upgrades
cat > /etc/apt/apt.conf.d/50unattended-upgrades <<EOF
Unattended-Upgrade::Allowed-Origins {
    "\${distro_id}:\${distro_codename}-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF
log_success "Automatic security updates configured"

# Clean up
log_info "Cleaning up..."
apt autoremove -y
apt clean

# Display summary
echo ""
log_success "=== Installation Complete ==="
echo ""
echo -e "${GREEN}Installed Components:${NC}"
echo "  - Python: $(python3.11 --version)"
echo "  - PostgreSQL: $(psql --version | head -n1)"
echo "  - Nginx: $(nginx -v 2>&1)"
echo "  - Certbot: $(certbot --version 2>&1 | head -n1)"
if id "deploy" &>/dev/null && sudo -u deploy bash -c 'command -v uv' &>/dev/null; then
    echo "  - uv: $(sudo -u deploy bash -c 'uv --version')"
fi
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Create deploy user (if not exists): adduser deploy && usermod -aG sudo deploy"
echo "  2. Setup SSH keys for deploy user"
echo "  3. Clone repository to /opt/mindflow"
echo "  4. Run database setup: /opt/mindflow/backend/deployment/migrate-db.sh"
echo "  5. Configure application environment: /opt/mindflow/backend/.env.production"
echo "  6. Install application dependencies: cd /opt/mindflow/backend && uv sync"
echo "  7. Configure Nginx: /opt/mindflow/backend/deployment/nginx.conf"
echo "  8. Setup systemd service: /opt/mindflow/backend/deployment/mindflow.service"
echo "  9. Obtain SSL certificate: sudo certbot --nginx"
echo "  10. Start application: sudo systemctl start mindflow"
echo ""
echo -e "${BLUE}Server Information:${NC}"
echo "  - IP Address: $(hostname -I | awk '{print $1}')"
echo "  - Hostname: $(hostname)"
echo "  - OS: $(lsb_release -d | cut -f2)"
echo "  - Kernel: $(uname -r)"
echo ""
echo -e "${GREEN}Setup script completed successfully!${NC}"
