# MindFlow Production Deployment Guide

## Overview

Deploy MindFlow FastAPI backend to DigitalOcean for $13-14/month with production-grade reliability, security, and observability.

**Target Monthly Cost:** $13-14/month
**Estimated Setup Time:** 90 minutes
**Minimum Requirements:** DigitalOcean account, SSH access, domain name (optional)

## Architecture

### Infrastructure Components

- **Compute:** DigitalOcean Droplet (2GB RAM, 1 vCPU, 50GB SSD) - $12/month
- **Database:** PostgreSQL 15 (same droplet, not managed DB)
- **Web Server:** Nginx (reverse proxy + SSL termination)
- **Application Server:** FastAPI with Uvicorn (2 workers)
- **Process Manager:** Systemd (auto-restart, logging)
- **SSL:** Let's Encrypt (free, auto-renewal)
- **CI/CD:** GitHub Actions (automated deployment)

### Architecture Diagram

```
Internet
    |
    v
[Let's Encrypt SSL]
    |
    v
[Nginx :443] ---> [FastAPI :8000] ---> [PostgreSQL :5432]
    |                   |
    v                   v
[Static Files]    [Alembic Migrations]
```

### Security Layers

1. **Network:** UFW firewall (ports 22, 80, 443 only)
2. **SSL/TLS:** Let's Encrypt certificates with automatic renewal
3. **Application:** JWT authentication, rate limiting, CORS
4. **Database:** Least-privilege user, local connections only
5. **Process:** Systemd security hardening (NoNewPrivileges, PrivateTmp)

## Prerequisites

### Required Accounts & Access

- [ ] DigitalOcean account with payment method
- [ ] GitHub repository access with push permissions
- [ ] Domain name (optional but recommended for SSL)
- [ ] SSH key pair for server access

### Local Tools

```bash
# Install DigitalOcean CLI (optional)
brew install doctl

# Verify you have SSH keys
ls -la ~/.ssh/id_*.pub
```

## Step-by-Step Deployment

### 1. Create DigitalOcean Droplet (5 minutes)

#### Option A: Web Console

1. Go to https://cloud.digitalocean.com/droplets/new
2. Choose configuration:
   - **Image:** Ubuntu 22.04 LTS (x64)
   - **Plan:** Basic
   - **CPU:** Regular (1 vCPU, 2GB RAM, 50GB SSD) - $12/month
   - **Datacenter:** Closest to your users
   - **Authentication:** SSH keys (recommended) or Password
   - **Hostname:** mindflow-prod
3. Click "Create Droplet"
4. Note the droplet IP address

#### Option B: doctl CLI

```bash
# Authenticate
doctl auth init

# Create droplet
doctl compute droplet create mindflow-prod \
  --image ubuntu-22-04-x64 \
  --size s-1vcpu-2gb \
  --region sfo3 \
  --ssh-keys $(doctl compute ssh-key list --format ID --no-header | head -n1)

# Get IP address
doctl compute droplet list mindflow-prod --format PublicIPv4 --no-header
```

**Save the IP address:** `export SERVER_IP=<your-droplet-ip>`

### 2. Initial Server Setup (10 minutes)

SSH into your server:

```bash
ssh root@$SERVER_IP
```

#### Create Deploy User

```bash
# Create user with sudo privileges
adduser deploy
usermod -aG sudo deploy

# Setup SSH key authentication for deploy user
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# Test sudo access
su - deploy
sudo -v
```

#### Configure Firewall

```bash
# Setup UFW firewall
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

#### Update System

```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
```

Exit and reconnect as deploy user:

```bash
exit
exit
ssh deploy@$SERVER_IP
```

### 3. Install Dependencies (15 minutes)

Run the automated setup script from the repository:

```bash
# Download and run setup script
curl -fsSL https://raw.githubusercontent.com/YOUR-USERNAME/mindflow/main/backend/deployment/setup.sh -o setup.sh
chmod +x setup.sh
sudo ./setup.sh
```

Or manually install dependencies:

```bash
# Add deadsnakes PPA for Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install PostgreSQL 15
sudo apt install -y postgresql-15 postgresql-contrib-15

# Install Nginx
sudo apt install -y nginx

# Install Certbot for Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx

# Install Git
sudo apt install -y git curl

# Install uv (modern Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Verify installations
python3.11 --version
psql --version
nginx -v
certbot --version
uv --version
```

### 4. Database Setup (10 minutes)

#### Create Database and User

```bash
# Generate secure password
DB_PASSWORD=$(openssl rand -hex 16)
echo "Database Password: $DB_PASSWORD" > ~/db_credentials.txt
chmod 600 ~/db_credentials.txt

# Create database
sudo -u postgres psql <<EOF
-- Create database
CREATE DATABASE mindflow_prod;

-- Create application user
CREATE USER mindflow_app WITH PASSWORD '$DB_PASSWORD';

-- Grant permissions
GRANT CONNECT ON DATABASE mindflow_prod TO mindflow_app;
\c mindflow_prod
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mindflow_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mindflow_app;

-- For future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mindflow_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO mindflow_app;
EOF

echo "Database created successfully"
```

Or use the migration script:

```bash
cd /opt/mindflow/backend/deployment
chmod +x migrate-db.sh
./migrate-db.sh
```

#### Configure PostgreSQL

```bash
# Enable PostgreSQL on startup
sudo systemctl enable postgresql

# Verify service is running
sudo systemctl status postgresql
```

### 5. Application Setup (15 minutes)

#### Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/mindflow
sudo chown deploy:deploy /opt/mindflow

# Clone repository
cd /opt/mindflow
git clone https://github.com/YOUR-USERNAME/mindflow.git .

# Checkout main branch
git checkout main
```

#### Configure Environment

```bash
cd /opt/mindflow/backend

# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)

# Create production environment file
cat > .env.production <<EOF
# Database Configuration
DATABASE_URL=postgresql+asyncpg://mindflow_app:$DB_PASSWORD@localhost/mindflow_prod

# Security
SECRET_KEY=$SECRET_KEY
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Environment
ENVIRONMENT=production
DEBUG=false

# Monitoring (Optional - add later)
SENTRY_DSN=

# CORS (Update with your frontend domain)
ALLOWED_ORIGINS=https://mindflow.example.com,https://www.mindflow.example.com
EOF

# Secure the file
chmod 600 .env.production

echo "Secret Key: $SECRET_KEY" >> ~/db_credentials.txt
```

#### Install Dependencies

```bash
cd /opt/mindflow/backend

# Create virtual environment and install dependencies
uv sync

# Verify installation
source .venv/bin/activate
python --version
pip list
```

#### Run Database Migrations

```bash
cd /opt/mindflow/backend

# Run migrations
uv run alembic upgrade head

# Verify tables created
PGPASSWORD=$DB_PASSWORD psql -U mindflow_app -d mindflow_prod -c "\dt"
```

### 6. Nginx + SSL Configuration (20 minutes)

#### Configure Domain DNS (if using custom domain)

Add A record pointing to your server IP:

```
Type: A
Name: api
Value: <your-server-ip>
TTL: 3600
```

Wait for DNS propagation (check with `dig api.yourdomain.com`).

#### Install Nginx Configuration

```bash
# Copy nginx config
sudo cp /opt/mindflow/backend/deployment/nginx.conf /etc/nginx/sites-available/mindflow

# Update domain name in config
sudo nano /etc/nginx/sites-available/mindflow
# Change api.mindflow.example.com to your actual domain

# Enable site
sudo ln -s /etc/nginx/sites-available/mindflow /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

#### Obtain SSL Certificate

```bash
# For custom domain
sudo certbot --nginx -d api.yourdomain.com

# Follow prompts:
# - Enter email for renewal notifications
# - Agree to Terms of Service
# - Choose redirect HTTP to HTTPS (recommended)

# Verify auto-renewal
sudo certbot renew --dry-run
```

#### Configure Nginx Without SSL (Alternative)

If you don't have a domain, use IP-only configuration:

```bash
# Create simple config for IP access
sudo tee /etc/nginx/sites-available/mindflow <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/mindflow /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 7. Systemd Service Setup (10 minutes)

#### Install Service File

```bash
# Copy service file
sudo cp /opt/mindflow/backend/deployment/mindflow.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable mindflow

# Start service
sudo systemctl start mindflow

# Check status
sudo systemctl status mindflow

# View logs
sudo journalctl -u mindflow -f
```

#### Verify Application Running

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","environment":"production","version":"2.0.0"}

# Test via Nginx
curl http://localhost/health

# If using domain with SSL
curl https://api.yourdomain.com/health
```

### 8. CI/CD Setup with GitHub Actions (15 minutes)

#### Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

1. **SERVER_IP:** Your droplet IP address
2. **SSH_PRIVATE_KEY:** Your SSH private key for deploy user

```bash
# Generate deploy key if needed
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy
cat ~/.ssh/github_deploy.pub

# Add public key to server
ssh deploy@$SERVER_IP
echo "ssh-ed25519 AAAA... github-actions-deploy" >> ~/.ssh/authorized_keys

# Copy private key content to GitHub secret
cat ~/.ssh/github_deploy
```

#### Configure Deploy Script on Server

```bash
# Create deployment script
sudo tee /opt/mindflow/deploy.sh <<'EOF'
#!/bin/bash
set -e

echo "=== MindFlow Deployment Started ==="

cd /opt/mindflow

# Backup current commit
LAST_COMMIT=$(git rev-parse HEAD)
echo $LAST_COMMIT > .last-deploy
echo "Current version: $LAST_COMMIT"

# Pull new code
git pull origin main
NEW_COMMIT=$(git rev-parse HEAD)
echo "Deploying version: $NEW_COMMIT"

# Install dependencies
cd backend
/home/deploy/.cargo/bin/uv sync

# Run migrations
if ! /home/deploy/.cargo/bin/uv run alembic upgrade head; then
    echo "Migration failed, rolling back..."
    cd /opt/mindflow
    git reset --hard $LAST_COMMIT
    exit 1
fi

# Restart service
sudo systemctl restart mindflow

# Wait for startup
echo "Waiting for service to start..."
sleep 10

# Health check
if ! curl -f http://localhost:8000/health; then
    echo "Health check failed, rolling back..."
    cd /opt/mindflow
    git reset --hard $LAST_COMMIT
    cd backend
    /home/deploy/.cargo/bin/uv run alembic downgrade -1
    sudo systemctl restart mindflow
    exit 1
fi

echo "=== Deployment Successful: $NEW_COMMIT ==="
EOF

sudo chmod +x /opt/mindflow/deploy.sh
sudo chown deploy:deploy /opt/mindflow/deploy.sh
```

#### Allow Deploy User to Restart Service

```bash
# Grant sudo permission for systemctl restart
sudo tee /etc/sudoers.d/mindflow-deploy <<'EOF'
deploy ALL=(ALL) NOPASSWD: /bin/systemctl restart mindflow
deploy ALL=(ALL) NOPASSWD: /bin/systemctl status mindflow
EOF

sudo chmod 440 /etc/sudoers.d/mindflow-deploy
```

#### Test GitHub Actions Workflow

The workflow file is already in `.github/workflows/deploy.yml`.

Push to main branch to trigger deployment:

```bash
git add .
git commit -m "feat: configure production deployment"
git push origin main
```

Monitor deployment in GitHub Actions tab.

### 9. Monitoring Setup (Optional but Recommended)

#### Configure Health Check Monitoring

```bash
# Copy monitoring script
sudo cp /opt/mindflow/backend/deployment/monitor.sh /opt/mindflow/

# Make executable
sudo chmod +x /opt/mindflow/monitor.sh

# Create log directory
sudo mkdir -p /var/log/mindflow
sudo chown deploy:deploy /var/log/mindflow

# Add to crontab (runs every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/mindflow/monitor.sh") | crontab -

# Verify crontab
crontab -l
```

#### Configure Sentry (Optional)

1. Create free Sentry account at https://sentry.io
2. Create new project for Python/FastAPI
3. Copy DSN
4. Add to `.env.production`:

```bash
echo "SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id" >> /opt/mindflow/backend/.env.production
sudo systemctl restart mindflow
```

#### Setup Log Rotation

```bash
# Create logrotate config
sudo tee /etc/logrotate.d/mindflow <<'EOF'
/var/log/mindflow/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
    sharedscripts
    postrotate
        systemctl reload mindflow > /dev/null
    endscript
}
EOF
```

### 10. Verification & Testing (10 minutes)

#### System Health Checks

```bash
# Check all services running
sudo systemctl status postgresql nginx mindflow

# Check firewall
sudo ufw status

# Check disk space
df -h

# Check memory usage
free -h

# Check application logs
sudo journalctl -u mindflow --since "5 minutes ago"
```

#### API Endpoint Testing

```bash
# Health check
curl https://api.yourdomain.com/health

# API documentation
curl https://api.yourdomain.com/docs

# Register test user
curl -X POST https://api.yourdomain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }'

# Login
curl -X POST https://api.yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

#### Load Testing (Optional)

```bash
# Install Apache Bench
sudo apt install -y apache2-utils

# Test 100 requests with 10 concurrent
ab -n 100 -c 10 https://api.yourdomain.com/health
```

## Post-Deployment Operations

### View Application Logs

```bash
# Real-time logs
sudo journalctl -u mindflow -f

# Last 100 lines
sudo journalctl -u mindflow -n 100

# Logs from last hour
sudo journalctl -u mindflow --since "1 hour ago"

# Filter by priority
sudo journalctl -u mindflow -p err
```

### Restart Application

```bash
sudo systemctl restart mindflow
sudo systemctl status mindflow
```

### Update Application

```bash
# Manual deployment
cd /opt/mindflow
./deploy.sh

# Or push to main branch for automatic deployment via GitHub Actions
```

### Rollback Deployment

```bash
cd /opt/mindflow

# View last successful deployment
cat .last-deploy

# Rollback to previous commit
git reset --hard $(cat .last-deploy)

# Rollback database migration (if needed)
cd backend
uv run alembic downgrade -1

# Restart service
sudo systemctl restart mindflow
```

### Database Backup

```bash
# Create backup
pg_dump -U mindflow_app mindflow_prod > ~/backup-$(date +%Y%m%d-%H%M%S).sql

# Restore from backup
psql -U mindflow_app mindflow_prod < ~/backup-20250131-120000.sql

# Automated daily backups (add to crontab)
# 0 2 * * * pg_dump -U mindflow_app mindflow_prod | gzip > /opt/backups/mindflow-$(date +\%Y\%m\%d).sql.gz
```

### SSL Certificate Renewal

```bash
# Certificates auto-renew via cron
# Test renewal process
sudo certbot renew --dry-run

# Force renewal (if needed)
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```

## Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| DigitalOcean Droplet (2GB) | $12.00/month | 1 vCPU, 2GB RAM, 50GB SSD |
| Bandwidth | $0/month | 2TB included, overage $0.01/GB |
| Backups (optional) | +$2.40/month | 20% of droplet cost |
| Floating IP (optional) | $4/month | If droplet off >744 hrs |
| Let's Encrypt SSL | $0/month | Free certificates |
| **Total Base Cost** | **$12-14/month** | Without optional add-ons |

### Scaling Options

- **4GB Droplet:** $18/month (2 vCPU, 4GB RAM) - 2x performance
- **Managed PostgreSQL:** +$15/month (1GB RAM, 10GB storage) - Automated backups
- **Load Balancer:** +$12/month - High availability with 2+ droplets

## Security Checklist

- [ ] Firewall configured (UFW) with only necessary ports
- [ ] SSH key authentication enabled, password auth disabled
- [ ] SSL/TLS certificates installed and auto-renewing
- [ ] Database user has least-privilege permissions
- [ ] Environment variables secured with restrictive file permissions
- [ ] Systemd service running with security hardening
- [ ] Regular security updates configured (unattended-upgrades)
- [ ] Rate limiting enabled in application
- [ ] CORS configured for production origins
- [ ] Sentry error monitoring configured (optional)
- [ ] Database backups scheduled
- [ ] Log rotation configured
- [ ] Health monitoring active

## Troubleshooting

### Application Won't Start

```bash
# Check service status
sudo systemctl status mindflow

# Check logs for errors
sudo journalctl -u mindflow -n 50

# Common issues:
# - Database connection: Check DATABASE_URL in .env.production
# - Port conflict: Check if port 8000 is available (lsof -i :8000)
# - Permissions: Ensure deploy user owns /opt/mindflow
```

### Database Connection Errors

```bash
# Test database connection
PGPASSWORD=your_password psql -U mindflow_app -d mindflow_prod -c "SELECT 1;"

# Check PostgreSQL running
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -c "\l"
```

### Nginx Configuration Issues

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Reload configuration
sudo systemctl reload nginx
```

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Check Nginx SSL config
sudo nginx -t
```

### High Memory Usage

```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Reduce Uvicorn workers (edit mindflow.service)
# Change --workers 2 to --workers 1

# Restart service
sudo systemctl restart mindflow
```

### Performance Issues

```bash
# Check system resources
htop

# Check slow queries
sudo -u postgres psql mindflow_prod
SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

# Enable query logging (temporarily)
# Edit /etc/postgresql/15/main/postgresql.conf
# log_min_duration_statement = 100

# Reload PostgreSQL
sudo systemctl reload postgresql
```

## Maintenance Schedule

### Daily

- Automated backups (via cron)
- Health check monitoring (via cron)
- Log rotation

### Weekly

- Review application logs for errors
- Check disk space usage
- Review Sentry errors (if configured)

### Monthly

- Security updates: `sudo apt update && sudo apt upgrade`
- Review and clean old backups
- Performance monitoring and optimization

### Quarterly

- Review and update dependencies
- Security audit
- Cost optimization review

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [DigitalOcean Tutorials](https://www.digitalocean.com/community/tutorials)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)

## Support

For issues or questions:

1. Check application logs: `sudo journalctl -u mindflow -f`
2. Review this deployment guide
3. Check GitHub Issues
4. Contact: your-email@example.com

---

**Last Updated:** 2025-10-31
**Version:** 1.0.0
