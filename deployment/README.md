# MindFlow Deployment Operations Guide

Quick reference for deploying and maintaining MindFlow in production.

## Quick Links

- **Comprehensive Guide**: [`docs/DEPLOYMENT-GUIDE.md`](../docs/DEPLOYMENT-GUIDE.md) (detailed walkthrough)
- **Deployment Summary**: [`backend/DEPLOYMENT-SUMMARY.md`](../backend/DEPLOYMENT-SUMMARY.md) (overview)
- **This File**: Quick reference for common operations

---

## Files in This Directory

| File | Purpose | Executable |
|------|---------|------------|
| `setup.sh` | Server initialization (one-time) | ✓ |
| `migrate-db.sh` | Database setup and migrations | ✓ |
| `monitor.sh` | Health monitoring (cron) | ✓ |
| `nginx.conf` | Nginx reverse proxy config | - |
| `mindflow.service` | Systemd service config | - |
| `env.production.template` | Environment variables template | - |
| `README.md` | This file | - |

---

## Initial Deployment (90 minutes)

### Prerequisites
- Ubuntu 22.04 LTS server (DigitalOcean 2GB droplet)
- Domain name pointing to server IP
- SSH access as root

### Step-by-Step

```bash
# 1. Run server setup (as root)
sudo bash deployment/setup.sh

# 2. Configure SSH for deploy user
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo -u deploy vim /home/deploy/.ssh/authorized_keys  # Add your public key
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys

# 3. Clone repository
sudo -u deploy git clone https://github.com/yourusername/mindflow.git /opt/mindflow

# 4. Setup database
sudo bash /opt/mindflow/deployment/migrate-db.sh

# 5. Configure environment
sudo -u deploy cp /opt/mindflow/deployment/env.production.template /opt/mindflow/backend/.env.production
sudo -u deploy vim /opt/mindflow/backend/.env.production  # Fill in values

# 6. Install Python dependencies
cd /opt/mindflow/backend
sudo -u deploy uv venv
sudo -u deploy uv sync

# 7. Install systemd service
sudo cp /opt/mindflow/deployment/mindflow.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mindflow
sudo systemctl start mindflow

# 8. Configure Nginx
sudo cp /opt/mindflow/deployment/nginx.conf /etc/nginx/sites-available/mindflow
sudo sed -i 's/api.yourdomain.com/YOUR_ACTUAL_DOMAIN/g' /etc/nginx/sites-available/mindflow
sudo ln -s /etc/nginx/sites-available/mindflow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 9. Setup SSL certificate
sudo certbot --nginx -d YOUR_ACTUAL_DOMAIN

# 10. Setup health monitoring
sudo -u deploy crontab -e
# Add: */5 * * * * /opt/mindflow/deployment/monitor.sh
```

---

## Common Operations

### View Application Logs

```bash
# Live tail
sudo journalctl -u mindflow -f

# Last 100 lines
sudo journalctl -u mindflow -n 100

# Logs from last hour
sudo journalctl -u mindflow --since "1 hour ago"

# Errors only
sudo journalctl -u mindflow -p err
```

### Service Management

```bash
# Status
sudo systemctl status mindflow

# Start
sudo systemctl start mindflow

# Stop
sudo systemctl stop mindflow

# Restart
sudo systemctl restart mindflow

# Reload (graceful restart)
sudo systemctl reload mindflow

# Enable auto-start
sudo systemctl enable mindflow

# Disable auto-start
sudo systemctl disable mindflow
```

### Database Operations

```bash
# Connect to database
PGPASSWORD='your_password' psql -U mindflow_app -d mindflow_prod

# Run migrations
cd /opt/mindflow/backend
source .venv/bin/activate
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# Check migration status
uv run alembic current

# View migration history
uv run alembic history

# Backup database
pg_dump -U mindflow_app mindflow_prod > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Manual Deployment (Without CI/CD)

```bash
# 1. SSH to server
ssh deploy@YOUR_SERVER_IP

# 2. Navigate to app directory
cd /opt/mindflow

# 3. Backup current version
git rev-parse HEAD > .last-deploy

# 4. Pull latest code
git pull origin main

# 5. Install dependencies
cd backend
uv sync

# 6. Backup database
pg_dump -U mindflow_app mindflow_prod > /opt/backups/mindflow/backup_$(date +%Y%m%d_%H%M%S).sql

# 7. Run migrations
uv run alembic upgrade head

# 8. Restart service
sudo systemctl restart mindflow

# 9. Check health
curl http://localhost:8000/health

# 10. Check logs
sudo journalctl -u mindflow -n 50
```

### Rollback Deployment

```bash
# 1. Navigate to app directory
cd /opt/mindflow

# 2. Rollback code
git reset --hard $(cat .last-deploy)

# 3. Rollback database (if needed)
cd backend
source .venv/bin/activate
uv run alembic downgrade -1

# 4. Restart service
sudo systemctl restart mindflow

# 5. Verify
curl http://localhost:8000/health
```

### Monitoring

```bash
# Check health endpoint
curl https://YOUR_DOMAIN/health

# Check service status
sudo systemctl status mindflow

# Check Nginx status
sudo systemctl status nginx

# Check PostgreSQL status
sudo systemctl status postgresql

# View health monitoring log
tail -f /var/log/mindflow/health.log

# Check disk usage
df -h

# Check memory usage
free -h

# Check running processes
htop
```

### Nginx Operations

```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# Restart Nginx
sudo systemctl restart nginx

# View access logs
sudo tail -f /var/log/nginx/mindflow_access.log

# View error logs
sudo tail -f /var/log/nginx/mindflow_error.log

# Check SSL certificate
sudo certbot certificates

# Renew SSL certificate (dry run)
sudo certbot renew --dry-run

# Force SSL renewal
sudo certbot renew --force-renewal
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u mindflow -n 50

# Check environment file
cat /opt/mindflow/backend/.env.production

# Test manually
cd /opt/mindflow/backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Check port conflicts
sudo ss -tlnp | grep 8000
```

### Database Connection Errors

```bash
# Test connection
PGPASSWORD='password' psql -U mindflow_app -d mindflow_prod -c "SELECT 1;"

# Check PostgreSQL running
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -c "\l" | grep mindflow

# Check user permissions
sudo -u postgres psql -c "\du" | grep mindflow
```

### 502 Bad Gateway

```bash
# Check application running
sudo systemctl status mindflow

# Check port binding
sudo ss -tlnp | grep 8000

# Check Nginx error logs
sudo tail -f /var/log/nginx/mindflow_error.log

# Test upstream directly
curl http://localhost:8000/health
```

### High Memory Usage

```bash
# Check process memory
ps aux --sort=-%mem | head

# Reduce workers (edit mindflow.service)
sudo vim /etc/systemd/system/mindflow.service
# Change --workers 2 to --workers 1
sudo systemctl daemon-reload
sudo systemctl restart mindflow
```

---

## Performance Tuning

### Database

```bash
# Check slow queries
sudo -u postgres psql mindflow_prod -c "
SELECT query, calls, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;"

# Vacuum database
sudo -u postgres psql mindflow_prod -c "VACUUM ANALYZE;"

# Check table sizes
sudo -u postgres psql mindflow_prod -c "
SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::text)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::text) DESC;"
```

### Application

```bash
# Check request times (requires access logs with response times)
sudo cat /var/log/nginx/mindflow_access.log | \
  awk '{print $NF}' | \
  sort -n | \
  awk 'BEGIN{sum=0; count=0} {sum+=$1; count++; values[count]=$1} END{
    print "Count:", count;
    print "Mean:", sum/count;
    print "Median:", values[int(count/2)];
    print "P95:", values[int(count*0.95)];
    print "P99:", values[int(count*0.99)];
  }'
```

---

## Security

### Update System Packages

```bash
# Update package list
sudo apt update

# Upgrade packages
sudo apt upgrade -y

# Reboot if kernel updated
sudo reboot
```

### Update Python Dependencies

```bash
cd /opt/mindflow/backend
sudo -u deploy uv sync --upgrade
sudo systemctl restart mindflow
```

### Rotate JWT Secret

```bash
# 1. Generate new secret
openssl rand -hex 32

# 2. Update .env.production
sudo -u deploy vim /opt/mindflow/backend/.env.production
# Update SECRET_KEY value

# 3. Restart service
sudo systemctl restart mindflow

# Note: This will invalidate all existing JWT tokens
# Users will need to log in again
```

### Review Firewall

```bash
# Check rules
sudo ufw status verbose

# Add rule
sudo ufw allow 8080/tcp

# Remove rule
sudo ufw delete allow 8080/tcp
```

---

## Backup & Restore

### Manual Backup

```bash
# Backup database
pg_dump -U mindflow_app mindflow_prod > /opt/backups/mindflow/backup_$(date +%Y%m%d_%H%M%S).sql

# Backup code and configuration
tar -czf /opt/backups/mindflow/code_$(date +%Y%m%d_%H%M%S).tar.gz \
  /opt/mindflow \
  --exclude='/opt/mindflow/backend/.venv' \
  --exclude='/opt/mindflow/backend/__pycache__'

# List backups
ls -lh /opt/backups/mindflow/
```

### Restore from Backup

```bash
# Stop application
sudo systemctl stop mindflow

# Restore database
psql -U mindflow_app mindflow_prod < /opt/backups/mindflow/backup_YYYYMMDD_HHMMSS.sql

# Restore code (if needed)
cd /opt
tar -xzf /opt/backups/mindflow/code_YYYYMMDD_HHMMSS.tar.gz

# Start application
sudo systemctl start mindflow
```

---

## Monitoring Alerts (Optional)

### Email Alerts

Edit `monitor.sh`:
```bash
ENABLE_EMAIL_ALERTS=true
ALERT_EMAIL="your-email@example.com"
```

### Slack Alerts

1. Create Slack webhook: https://api.slack.com/messaging/webhooks
2. Edit `monitor.sh`:
```bash
ENABLE_SLACK_ALERTS=true
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

---

## Cost Optimization

### Current Setup
- **$12/month**: DigitalOcean 2GB droplet
- **$0/month**: Let's Encrypt SSL
- **$0/month**: GitHub Actions (2000 min/month)
- **Total**: $12-14/month

### Scale Up When Needed

**4GB droplet** ($18/month):
```bash
# Resize via DigitalOcean dashboard
# Update workers in mindflow.service
sudo vim /etc/systemd/system/mindflow.service
# Change --workers 2 to --workers 4
sudo systemctl daemon-reload
sudo systemctl restart mindflow
```

---

## Support

### Logs to Check
1. Application: `sudo journalctl -u mindflow -n 100`
2. Nginx access: `sudo tail -f /var/log/nginx/mindflow_access.log`
3. Nginx error: `sudo tail -f /var/log/nginx/mindflow_error.log`
4. Health monitor: `tail -f /var/log/mindflow/health.log`
5. PostgreSQL: `sudo tail -f /var/log/postgresql/postgresql-15-main.log`

### Diagnostic Commands
```bash
# Full system check
echo "=== Service Status ==="
sudo systemctl status mindflow --no-pager
echo ""
echo "=== Health Check ==="
curl -s http://localhost:8000/health | jq
echo ""
echo "=== Database Connection ==="
PGPASSWORD='password' psql -U mindflow_app -d mindflow_prod -c "SELECT version();"
echo ""
echo "=== Disk Usage ==="
df -h
echo ""
echo "=== Memory Usage ==="
free -h
echo ""
echo "=== Recent Errors ==="
sudo journalctl -u mindflow -p err --since "1 hour ago" --no-pager
```

---

## Additional Resources

- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [DigitalOcean Documentation](https://docs.digitalocean.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

---

**Last Updated**: 2025-10-31
**Version**: 1.0.0
