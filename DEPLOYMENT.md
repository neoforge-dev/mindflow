# MindFlow Production Deployment Guide

Complete guide for deploying MindFlow to production with automated CI/CD.

**Stack:** FastAPI + PostgreSQL + Docker + Caddy + DigitalOcean + GitHub Actions

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Manual Deployment (First Time)](#manual-deployment-first-time)
3. [Automated Deployment (CI/CD)](#automated-deployment-cicd)
4. [Monitoring & Maintenance](#monitoring--maintenance)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts & Tools
- ✅ GitHub account (repository owner/admin access)
- ✅ DigitalOcean account with billing configured
- ✅ `doctl` CLI installed and authenticated
- ✅ Domain name (or use DigitalOcean DNS)
- ✅ SSH access to deployment server

### Local Development Tools
```bash
# Install doctl (macOS)
brew install doctl

# Authenticate with DigitalOcean
doctl auth init

# Verify connection
doctl account get
```

---

## Manual Deployment (First Time)

### Phase 1: Create DigitalOcean Infrastructure (10 minutes)

#### Step 1: Create Droplet

```bash
# Create 2GB droplet in Frankfurt
doctl compute droplet create mindflow-prod \
  --image ubuntu-22-04-x64 \
  --size s-2vcpu-2gb \
  --region fra1 \
  --ssh-keys $(doctl compute ssh-key list --format ID --no-header) \
  --wait

# Get droplet IP
DROPLET_IP=$(doctl compute droplet list mindflow-prod --format PublicIPv4 --no-header)
echo "Droplet IP: $DROPLET_IP"
```

#### Step 2: Configure DNS

```bash
# Add A records for your domain
doctl compute domain records create neoforge.dev \
  --record-type A \
  --record-name mindflow \
  --record-data $DROPLET_IP \
  --record-ttl 3600

doctl compute domain records create neoforge.dev \
  --record-type A \
  --record-name api.mindflow \
  --record-data $DROPLET_IP \
  --record-ttl 3600
```

**URLs:**
- Frontend: `https://mindflow.neoforge.dev`
- API: `https://api.mindflow.neoforge.dev`

#### Step 3: Configure Cloud Firewall

```bash
# Create firewall rules
doctl compute firewall create mindflow-fw \
  --name "MindFlow Production" \
  --inbound-rules "protocol:tcp,ports:22,sources:addresses:YOUR_IP_HERE protocol:tcp,ports:80,sources:addresses:0.0.0.0/0 protocol:tcp,ports:443,sources:addresses:0.0.0.0/0" \
  --outbound-rules "protocol:icmp,destinations:addresses:0.0.0.0/0 protocol:tcp,ports:all,destinations:addresses:0.0.0.0/0 protocol:udp,ports:all,destinations:addresses:0.0.0.0/0" \
  --droplet-ids $(doctl compute droplet list mindflow-prod --format ID --no-header)
```

**Security Notes:**
- Replace `YOUR_IP_HERE` with your actual IP for SSH access
- Port 22 (SSH): Restricted to your IP
- Ports 80/443 (HTTP/HTTPS): Open to public
- All outbound traffic: Allowed

---

### Phase 2: Server Setup (15 minutes)

#### Step 1: Initial Server Configuration

```bash
# SSH into the droplet
ssh root@$DROPLET_IP

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Verify installations
docker --version
docker compose version
```

#### Step 2: Create Application User

```bash
# Create mindflow user with docker permissions
useradd -m -s /bin/bash -G docker,sudo mindflow

# Set password (optional, for emergency access)
passwd mindflow

# Configure SSH access
mkdir -p /home/mindflow/.ssh
cp ~/.ssh/authorized_keys /home/mindflow/.ssh/
chown -R mindflow:mindflow /home/mindflow/.ssh
chmod 700 /home/mindflow/.ssh
chmod 600 /home/mindflow/.ssh/authorized_keys
```

#### Step 3: Harden SSH

```bash
# Edit SSH configuration
nano /etc/ssh/sshd_config

# Update these settings:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes

# Restart SSH
systemctl restart sshd
```

#### Step 4: Configure UFW Firewall

```bash
# Enable UFW
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status
```

---

### Phase 3: Application Deployment (20 minutes)

#### Step 1: Create Application Directory

```bash
# Exit root session, SSH as mindflow user
exit
ssh mindflow@$DROPLET_IP

# Create application directory
sudo mkdir -p /opt/mindflow
sudo chown mindflow:mindflow /opt/mindflow
cd /opt/mindflow
```

#### Step 2: Generate OAuth Keys

```bash
# Generate RS256 key pair for OAuth 2.1
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -pubout -in private_key.pem -out public_key.pem

# View keys (save for .env file)
cat private_key.pem
cat public_key.pem
```

#### Step 3: Create Environment File

```bash
# Create .env file
nano /opt/mindflow/.env
```

```bash
# Database Configuration
POSTGRES_DB=mindflow
POSTGRES_USER=mindflow
POSTGRES_PASSWORD=$(openssl rand -base64 32)
DATABASE_URL=postgresql+asyncpg://mindflow:PASSWORD_HERE@postgres:5432/mindflow

# Application Security
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# OAuth 2.1 Configuration
OAUTH_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
[paste from private_key.pem]
-----END PRIVATE KEY-----"

OAUTH_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
[paste from public_key.pem]
-----END PUBLIC KEY-----"

JWT_ALGORITHM=RS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# OAuth Client Credentials
OAUTH_CLIENT_ID=chatgpt_mindflow
OAUTH_CLIENT_SECRET=$(openssl rand -hex 32)
REFRESH_TOKEN_ROTATION_ENABLED=true

# MCP Configuration
MCP_SERVER_NAME="MindFlow Task Manager"
MCP_SERVER_VERSION="1.0.0"
MCP_ENABLE_TASK_WIDGETS=true
MCP_MAX_TASKS_PER_REQUEST=50

# GitHub Container Registry
GITHUB_REPOSITORY=YOUR_GITHUB_USERNAME/mindflow
```

**Security:**
```bash
# Secure the environment file
chmod 600 /opt/mindflow/.env
```

#### Step 4: Deploy Application Files

```bash
# From your local machine
cd /Users/bogdan/work/neoforge-dev/mindflow

# Deploy files to server
rsync -avz --exclude='.git' --exclude='backend/.venv' --exclude='__pycache__' \
  docker-compose.prod.yml Caddyfile frontend/ \
  mindflow@$DROPLET_IP:/opt/mindflow/

# Deploy backend configuration
rsync -avz backend/alembic/ backend/alembic.ini \
  mindflow@$DROPLET_IP:/opt/mindflow/backend/
```

#### Step 5: Start Services

```bash
# SSH back into server
ssh mindflow@$DROPLET_IP
cd /opt/mindflow

# Log in to GitHub Container Registry
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Pull latest image
docker compose -f docker-compose.prod.yml pull

# Start services
docker compose -f docker-compose.prod.yml up -d

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

#### Step 6: Run Database Migrations

```bash
# Run Alembic migrations
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# Verify database tables
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U mindflow -d mindflow -c "\dt"
```

---

### Phase 4: Verification (5 minutes)

#### Health Checks

```bash
# API health check
curl https://api.mindflow.neoforge.dev/health

# Expected response:
# {
#   "status": "healthy",
#   "version": "2.0.0",
#   "environment": "production",
#   "checks": {
#     "database": "healthy"
#   }
# }

# OpenAPI docs
open https://api.mindflow.neoforge.dev/docs

# Frontend
open https://mindflow.neoforge.dev
```

#### SSL Certificate Verification

```bash
# Check Caddy logs for certificate issuance
docker logs mindflow-caddy | grep "certificate obtained"

# Verify SSL with curl
curl -vI https://api.mindflow.neoforge.dev/health 2>&1 | grep "SSL certificate"
```

---

## Automated Deployment (CI/CD)

### Phase 1: GitHub Setup (10 minutes)

#### Step 1: Create GitHub Repository Secrets

Navigate to: **Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

```yaml
SSH_PRIVATE_KEY: <dedicated-deploy-key>
DROPLET_IP: 64.226.98.180
DEPLOY_USER: mindflow
```

**Generate dedicated SSH key for CI/CD:**

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy_key

# Add public key to server
ssh-copy-id -i ~/.ssh/github_deploy_key.pub mindflow@64.226.98.180

# Copy private key for GitHub secret
cat ~/.ssh/github_deploy_key
# Add to GitHub as SSH_PRIVATE_KEY
```

#### Step 2: Create Production Environment

Navigate to: **Settings → Environments → New environment**

1. Environment name: `production`
2. Environment protection rules:
   - ✅ Required reviewers (optional)
   - ✅ Wait timer: 5 minutes (optional)
3. Environment secrets:

```yaml
DATABASE_URL: postgresql+asyncpg://mindflow:PASSWORD@postgres:5432/mindflow
POSTGRES_PASSWORD: <from-server-.env>
SECRET_KEY: <from-server-.env>
OAUTH_CLIENT_ID: chatgpt_mindflow
OAUTH_CLIENT_SECRET: <from-server-.env>
```

#### Step 3: Enable GitHub Packages (GHCR)

Navigate to: **Settings → Actions → General → Workflow permissions**

- Select: **Read and write permissions**
- ✅ Allow GitHub Actions to create and approve pull requests

---

### Phase 2: GitHub Actions Workflow (Done)

The workflow file `.github/workflows/deploy-production.yml` handles:

✅ **Automated Testing**
- Unit tests with code coverage
- Linting and formatting checks
- Database integration tests

✅ **Docker Image Building**
- Multi-stage builds for optimization
- Push to GitHub Container Registry
- Automatic tagging (SHA, branch, latest)
- Build cache for faster builds

✅ **Zero-Downtime Deployment**
- Database migrations before deployment
- Rolling updates with health checks
- Automatic rollback on failure
- Post-deployment smoke tests

✅ **Security**
- Secrets management via GitHub
- Non-root container execution
- Vulnerability scanning
- Signed container attestations

---

### Phase 3: Install Docker Rollout on Server (5 minutes)

```bash
# SSH into server
ssh mindflow@64.226.98.180

# Install docker-rollout plugin
mkdir -p ~/.docker/cli-plugins
curl -sSL https://raw.githubusercontent.com/wowu/docker-rollout/main/docker-rollout \
  -o ~/.docker/cli-plugins/docker-rollout
chmod +x ~/.docker/cli-plugins/docker-rollout

# Verify installation
docker rollout --version
```

**What is docker-rollout?**
- Zero-downtime deployment tool
- Starts new containers before stopping old ones
- Monitors health checks during rollout
- Automatically reverts on failure

---

### Phase 4: Deployment Workflow

#### Automatic Deployment (Recommended)

```bash
# Make changes to code
git add .
git commit -m "feat: add new feature"

# Push to main branch
git push origin main

# GitHub Actions automatically:
# 1. Runs tests
# 2. Builds Docker image
# 3. Pushes to GHCR
# 4. Deploys to production
# 5. Runs health checks
# 6. Rolls back on failure
```

#### Manual Deployment

Navigate to: **Actions → Deploy to Production → Run workflow**

Select branch and click **Run workflow**

---

## Monitoring & Maintenance

### Daily Operations

#### View Application Logs

```bash
# SSH into server
ssh mindflow@64.226.98.180
cd /opt/mindflow

# API logs
docker compose -f docker-compose.prod.yml logs -f api

# Caddy logs
docker compose -f docker-compose.prod.yml logs -f caddy

# Database logs
docker compose -f docker-compose.prod.yml logs -f postgres
```

#### Monitor Resource Usage

```bash
# Container stats
docker stats

# Disk usage
df -h

# Memory usage
free -h

# Docker system usage
docker system df
```

#### Database Backups

```bash
# Create backup
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U mindflow mindflow > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U mindflow mindflow < backup_20250103_120000.sql
```

### Weekly Tasks

- ✅ Review application logs for errors
- ✅ Check disk space usage
- ✅ Verify SSL certificate expiry
- ✅ Review security updates

```bash
# Check for security updates
ssh mindflow@64.226.98.180
sudo apt update
sudo apt list --upgradable
```

### Monthly Tasks

- ✅ Rotate OAuth secrets
- ✅ Review and archive old logs
- ✅ Test backup restoration
- ✅ Review GitHub Actions usage limits

---

## Troubleshooting

### Issue: Deployment Failed

**Symptoms:** GitHub Actions workflow fails

**Diagnosis:**
```bash
# Check GitHub Actions logs
# Navigate to: Actions → Deploy to Production → Latest run

# Check server logs
ssh mindflow@64.226.98.180
docker compose -f /opt/mindflow/docker-compose.prod.yml logs --tail=100
```

**Solutions:**
1. Check if server is accessible: `ssh mindflow@$DROPLET_IP`
2. Verify Docker is running: `docker ps`
3. Check environment variables: `docker compose -f docker-compose.prod.yml config`
4. Review GitHub Secrets are set correctly

---

### Issue: SSL Certificate Not Working

**Symptoms:** Browser shows "Certificate Invalid" or connection errors

**Diagnosis:**
```bash
# Check Caddy logs
docker logs mindflow-caddy | grep -i "error\|certificate"

# Test domain DNS resolution
dig api.mindflow.neoforge.dev +short
# Should return: 64.226.98.180
```

**Solutions:**
1. Verify DNS records point to correct IP
2. Wait for DNS propagation (up to 48 hours)
3. Check ports 80/443 are open: `sudo ufw status`
4. Restart Caddy: `docker compose -f docker-compose.prod.yml restart caddy`

---

### Issue: Database Connection Failed

**Symptoms:** API returns 503, health check shows database unhealthy

**Diagnosis:**
```bash
# Check if PostgreSQL is running
docker compose -f docker-compose.prod.yml ps postgres

# Test database connection
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U mindflow -d mindflow -c "SELECT 1"
```

**Solutions:**
1. Verify DATABASE_URL in `.env` is correct
2. Check PostgreSQL logs: `docker compose logs postgres`
3. Restart database: `docker compose restart postgres`
4. Verify migrations ran: `docker compose exec api alembic current`

---

### Issue: Out of Disk Space

**Symptoms:** Docker operations fail, can't create new containers

**Diagnosis:**
```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df
```

**Solutions:**
```bash
# Remove unused Docker resources
docker system prune -af --volumes

# Remove old images (keep last 3)
docker images | grep 'ghcr.io' | tail -n +4 | awk '{print $3}' | xargs docker rmi

# Archive and compress old logs
cd /opt/mindflow
tar -czf logs_$(date +%Y%m%d).tar.gz *.log
rm *.log
```

---

### Issue: Migrations Fail

**Symptoms:** `alembic upgrade head` returns errors

**Diagnosis:**
```bash
# Check current migration state
docker compose -f docker-compose.prod.yml exec api alembic current

# View migration history
docker compose -f docker-compose.prod.yml exec api alembic history
```

**Solutions:**
```bash
# Option 1: Fix migration conflict
# Manually edit migration file to resolve conflicts

# Option 2: Rollback and retry
docker compose -f docker-compose.prod.yml exec api alembic downgrade -1
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# Option 3: Nuclear option (DESTRUCTIVE - development only)
# Drop database and recreate
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d postgres
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

---

## Security Best Practices

### Secrets Rotation Schedule

- **SECRET_KEY:** Rotate every 90 days
- **OAUTH_CLIENT_SECRET:** Rotate every 90 days
- **POSTGRES_PASSWORD:** Rotate every 90 days
- **SSH_PRIVATE_KEY:** Rotate every 180 days

### Hardening Checklist

- ✅ UFW firewall enabled
- ✅ SSH key authentication only (no passwords)
- ✅ Root login disabled
- ✅ Non-root user in Docker containers
- ✅ Environment variables in `.env` (not in code)
- ✅ HTTPS enforced via Caddy
- ✅ Regular security updates
- ✅ Database not exposed to public
- ✅ Rate limiting enabled in FastAPI
- ✅ CORS configured for specific origins

---

## Performance Optimization

### Recommended Droplet Sizes

| Traffic | Users | Droplet Size | Monthly Cost |
|---------|-------|--------------|--------------|
| Development | 1-10 | 2GB RAM, 2 vCPU | $18/month |
| **Production (Current)** | 10-100 | 2GB RAM, 2 vCPU | $18/month |
| High Traffic | 100-1000 | 4GB RAM, 2 vCPU | $36/month |
| Enterprise | 1000+ | 8GB RAM, 4 vCPU | $72/month |

### Scaling Strategy

**Vertical Scaling (Easier):**
```bash
# Resize droplet via doctl
doctl compute droplet-action resize <droplet-id> --size s-2vcpu-4gb --wait
```

**Horizontal Scaling (Advanced):**
- Add load balancer
- Deploy multiple API instances
- Use managed PostgreSQL database
- Implement Redis for caching

---

## Rollback Procedures

### Automatic Rollback

GitHub Actions automatically rolls back on:
- ❌ Health check failure
- ❌ Smoke test failure
- ❌ Migration error

### Manual Rollback

```bash
# SSH into server
ssh mindflow@64.226.98.180
cd /opt/mindflow

# List available images
docker images ghcr.io/YOUR_USERNAME/mindflow/backend

# Find previous SHA or tag
# Example: main-a1b2c3d

# Update docker-compose.prod.yml
nano docker-compose.prod.yml
# Change: image: ghcr.io/.../backend:main-a1b2c3d

# Deploy previous version
docker rollout -f docker-compose.prod.yml api

# Verify rollback
curl https://api.mindflow.neoforge.dev/health
```

---

## Cost Optimization

### Monthly Costs (Estimated)

- DigitalOcean Droplet: **$18/month**
- DigitalOcean Bandwidth: **Included (1TB)**
- Domain (neoforge.dev): **$12/year** = $1/month
- **Total:** ~$19/month

### Free Resources

- ✅ GitHub Container Registry (unlimited for public repos)
- ✅ GitHub Actions (2,000 minutes/month free)
- ✅ Let's Encrypt SSL certificates
- ✅ Caddy web server
- ✅ PostgreSQL (self-hosted)

---

## Maintenance Schedule

### Daily
- Monitor application logs for errors

### Weekly
- Review disk usage
- Check for security updates
- Verify backups

### Monthly
- Test backup restoration
- Rotate secrets (if scheduled)
- Review GitHub Actions usage
- Update dependencies

### Quarterly
- Security audit
- Performance review
- Cost optimization review

---

## Next Steps

After successful deployment:

1. ✅ **Set up monitoring** - Consider Sentry, Prometheus, or DigitalOcean Monitoring
2. ✅ **Configure automated backups** - Database backups to DigitalOcean Spaces
3. ✅ **Add staging environment** - Clone workflow for pre-production testing
4. ✅ **Implement rate limiting** - Protect API from abuse
5. ✅ **Set up uptime monitoring** - UptimeRobot or similar
6. ✅ **Create runbook** - Document incident response procedures
7. ✅ **Enable 2FA** - On all accounts (GitHub, DigitalOcean)

---

## Support & Resources

### Documentation
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Docker Compose Production](https://docs.docker.com/compose/production/)
- [Caddy Documentation](https://caddyserver.com/docs/)
- [DigitalOcean Tutorials](https://docs.digitalocean.com/)

### Monitoring
- [DigitalOcean Monitoring](https://cloud.digitalocean.com/monitoring)
- [GitHub Actions Logs](https://github.com/YOUR_USERNAME/mindflow/actions)

### Emergency Contacts
- DigitalOcean Support: https://cloud.digitalocean.com/support
- GitHub Support: https://support.github.com

---

## Changelog

### 2025-01-03 - Production Deployment v2.0
- ✅ Migrated from Google Sheets to FastAPI + PostgreSQL
- ✅ Implemented OAuth 2.1 with PKCE
- ✅ Configured automated CI/CD with GitHub Actions
- ✅ Set up zero-downtime deployments with docker-rollout
- ✅ Deployed to mindflow.neoforge.dev with HTTPS

### Previous Versions
- v1.0 (2024): Google Sheets + Apps Script + Custom GPT (Deprecated)

---

**Deployed successfully?** Issues or suggestions? Open a [GitHub issue](https://github.com/YOUR_USERNAME/mindflow/issues)!
