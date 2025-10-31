# MindFlow Deployment Configuration

This directory contains all configuration files and scripts needed to deploy MindFlow backend to production on DigitalOcean.

## Files Overview

### Configuration Files

- **nginx.conf** - Nginx reverse proxy configuration with SSL, security headers, and rate limiting
- **mindflow.service** - Systemd service configuration with auto-restart and security hardening
- **env.production.template** - Template for production environment variables

### Setup Scripts

- **setup.sh** - Initial server setup (Python, PostgreSQL, Nginx, dependencies)
- **migrate-db.sh** - Database creation and user setup with secure permissions
- **monitor.sh** - Health check monitoring with automatic service restart

### CI/CD

- **../.github/workflows/deploy.yml** - GitHub Actions workflow for automated deployment

## Quick Start

### 1. Initial Server Setup

```bash
# SSH into your DigitalOcean droplet as root
ssh root@YOUR_SERVER_IP

# Download and run setup script
curl -fsSL https://raw.githubusercontent.com/YOUR-USERNAME/mindflow/main/backend/deployment/setup.sh -o setup.sh
chmod +x setup.sh
sudo ./setup.sh
```

### 2. Create Deploy User

```bash
# Create user
adduser deploy
usermod -aG sudo deploy

# Setup SSH keys
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# Switch to deploy user
su - deploy
```

### 3. Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/mindflow
sudo chown deploy:deploy /opt/mindflow

# Clone repository
cd /opt/mindflow
git clone https://github.com/YOUR-USERNAME/mindflow.git .
```

### 4. Setup Database

```bash
cd /opt/mindflow/backend/deployment
./migrate-db.sh
```

### 5. Configure Environment

```bash
cd /opt/mindflow/backend

# Copy template
cp deployment/env.production.template .env.production

# Edit with actual values (use credentials from migrate-db.sh)
nano .env.production

# Secure the file
chmod 600 .env.production
```

### 6. Install Application Dependencies

```bash
cd /opt/mindflow/backend
uv sync
```

### 7. Run Database Migrations

```bash
cd /opt/mindflow/backend
uv run alembic upgrade head
```

### 8. Configure Nginx

```bash
# Copy nginx config
sudo cp /opt/mindflow/backend/deployment/nginx.conf /etc/nginx/sites-available/mindflow

# Update domain name
sudo nano /etc/nginx/sites-available/mindflow
# Change api.mindflow.example.com to your actual domain

# Enable site
sudo ln -s /etc/nginx/sites-available/mindflow /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### 9. Setup SSL Certificate

```bash
sudo certbot --nginx -d api.yourdomain.com
```

### 10. Install Systemd Service

```bash
# Copy service file
sudo cp /opt/mindflow/backend/deployment/mindflow.service /etc/systemd/system/

# Grant deploy user permission to restart service
sudo tee /etc/sudoers.d/mindflow-deploy <<'EOF'
deploy ALL=(ALL) NOPASSWD: /bin/systemctl restart mindflow
deploy ALL=(ALL) NOPASSWD: /bin/systemctl status mindflow
EOF
sudo chmod 440 /etc/sudoers.d/mindflow-deploy

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mindflow
sudo systemctl start mindflow

# Check status
sudo systemctl status mindflow
```

### 11. Setup Health Monitoring

```bash
# Copy monitor script
cp /opt/mindflow/backend/deployment/monitor.sh /opt/mindflow/
chmod +x /opt/mindflow/monitor.sh

# Create log directory
sudo mkdir -p /var/log/mindflow
sudo chown deploy:deploy /var/log/mindflow

# Add to crontab (runs every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/mindflow/monitor.sh") | crontab -
```

### 12. Configure GitHub Actions

1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Add secrets:
   - `SERVER_IP`: Your droplet IP address
   - `SSH_PRIVATE_KEY`: SSH private key for deploy user

## Verification

### Test Health Endpoint

```bash
# Local test
curl http://localhost:8000/health

# Public test (with SSL)
curl https://api.yourdomain.com/health
```

### View Logs

```bash
# Application logs
sudo journalctl -u mindflow -f

# Nginx access logs
sudo tail -f /var/log/nginx/mindflow_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/mindflow_error.log
```

### Check Service Status

```bash
sudo systemctl status mindflow
sudo systemctl status nginx
sudo systemctl status postgresql
```

## Operations

### Manual Deployment

```bash
cd /opt/mindflow
git pull origin main
cd backend
uv sync
uv run alembic upgrade head
sudo systemctl restart mindflow
```

### Rollback Deployment

```bash
cd /opt/mindflow
git reset --hard $(cat .last-deploy)
cd backend
uv run alembic downgrade -1
sudo systemctl restart mindflow
```

### Database Backup

```bash
# Manual backup
pg_dump -U mindflow_app mindflow_prod > ~/backup-$(date +%Y%m%d-%H%M%S).sql

# Restore from backup
psql -U mindflow_app mindflow_prod < ~/backup-20250131-120000.sql
```

### View Monitoring Logs

```bash
tail -f /var/log/mindflow/health.log
```

## Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| DigitalOcean Droplet (2GB) | $12.00/month | 1 vCPU, 2GB RAM, 50GB SSD |
| Bandwidth | Included | 2TB included |
| SSL Certificate | Free | Let's Encrypt |
| **Total** | **$12-14/month** | |

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u mindflow -n 50

# Check configuration
cd /opt/mindflow/backend
cat .env.production

# Test manually
cd /opt/mindflow/backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Database Connection Issues

```bash
# Test connection
PGPASSWORD='your_password' psql -U mindflow_app -d mindflow_prod -c "SELECT 1;"

# Check PostgreSQL
sudo systemctl status postgresql
```

### SSL Certificate Issues

```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew --dry-run
```

## Security Checklist

- [ ] Firewall configured (UFW) with only ports 22, 80, 443
- [ ] SSH key authentication enabled
- [ ] SSL certificates installed
- [ ] Database user has least-privilege permissions
- [ ] Environment variables secured (chmod 600)
- [ ] Systemd service security hardening enabled
- [ ] Rate limiting configured in Nginx
- [ ] Health monitoring active
- [ ] Automatic security updates configured
- [ ] Database backups scheduled

## Additional Resources

- [Full Deployment Guide](../docs/DEPLOYMENT-GUIDE.md)
- [DigitalOcean Documentation](https://docs.digitalocean.com/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Nginx Documentation](https://nginx.org/en/docs/)

## Support

For issues or questions, refer to:
1. [Deployment Guide](../docs/DEPLOYMENT-GUIDE.md)
2. Application logs: `sudo journalctl -u mindflow -f`
3. GitHub Issues

---

**Last Updated:** 2025-10-31
**Version:** 1.0.0
