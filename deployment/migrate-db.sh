#!/bin/bash

# MindFlow Database Migration Script
# Creates PostgreSQL database, user, and runs Alembic migrations
# Usage: sudo bash migrate-db.sh

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

log_info "Starting database setup..."

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_NAME="mindflow_prod"
DB_USER="mindflow_app"
DB_PASSWORD=$(openssl rand -hex 32)
CREDENTIALS_FILE="/opt/mindflow/backend/.db_credentials"
ENV_FILE="/opt/mindflow/backend/.env.production"

log_info "Database configuration:"
log_info "  Database: $DB_NAME"
log_info "  User: $DB_USER"
log_info "  Password: [GENERATED - will be saved to $CREDENTIALS_FILE]"

# ============================================================================
# CREATE DATABASE
# ============================================================================

log_info "Creating PostgreSQL database..."

# Check if database exists
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    log_warn "Database '$DB_NAME' already exists"
    read -p "Do you want to drop and recreate it? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;"
        log_info "Database dropped"
    else
        log_info "Keeping existing database"
    fi
fi

# Create database if it doesn't exist
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME WITH ENCODING='UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8' TEMPLATE=template0;"
    log_info "Database '$DB_NAME' created"
fi

# ============================================================================
# CREATE USER
# ============================================================================

log_info "Creating PostgreSQL user..."

# Check if user exists
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    log_warn "User '$DB_USER' already exists, updating password"
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
else
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    log_info "User '$DB_USER' created"
fi

# ============================================================================
# GRANT PERMISSIONS
# ============================================================================

log_info "Granting database permissions..."

# Grant connect permission
sudo -u postgres psql -c "GRANT CONNECT ON DATABASE $DB_NAME TO $DB_USER;"

# Grant schema permissions
sudo -u postgres psql -d "$DB_NAME" -c "GRANT USAGE, CREATE ON SCHEMA public TO $DB_USER;"

# Grant table permissions (for existing tables)
sudo -u postgres psql -d "$DB_NAME" -c "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO $DB_USER;"

# Grant sequence permissions (for auto-increment columns)
sudo -u postgres psql -d "$DB_NAME" -c "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;"

# Grant default privileges for future tables
sudo -u postgres psql -d "$DB_NAME" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $DB_USER;"
sudo -u postgres psql -d "$DB_NAME" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO $DB_USER;"

log_info "Permissions granted"

# ============================================================================
# SAVE CREDENTIALS
# ============================================================================

log_info "Saving credentials to $CREDENTIALS_FILE..."

cat > "$CREDENTIALS_FILE" <<EOF
# MindFlow Database Credentials
# Generated: $(date)
# WARNING: Keep this file secure! chmod 600 recommended

DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
EOF

chown deploy:deploy "$CREDENTIALS_FILE"
chmod 600 "$CREDENTIALS_FILE"

log_info "Credentials saved and secured (chmod 600)"

# ============================================================================
# UPDATE .env.production
# ============================================================================

if [ -f "$ENV_FILE" ]; then
    log_info "Updating DATABASE_URL in $ENV_FILE..."

    # Backup original file
    cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

    # Update DATABASE_URL (escape special characters in password)
    ESCAPED_PASSWORD=$(echo "$DB_PASSWORD" | sed 's/[&/\]/\\&/g')
    sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://$DB_USER:$ESCAPED_PASSWORD@localhost:5432/$DB_NAME|" "$ENV_FILE"

    log_info ".env.production updated"
else
    log_warn "$ENV_FILE not found. You'll need to create it manually."
    log_info "Copy from: /opt/mindflow/deployment/env.production.template"
fi

# ============================================================================
# TEST CONNECTION
# ============================================================================

log_info "Testing database connection..."

if PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h localhost -c "SELECT version();" > /dev/null 2>&1; then
    log_info "✓ Database connection successful!"
else
    log_error "✗ Database connection failed!"
    log_error "Please check the credentials in $CREDENTIALS_FILE"
    exit 1
fi

# ============================================================================
# RUN ALEMBIC MIGRATIONS
# ============================================================================

log_info "Running Alembic migrations..."

cd /opt/mindflow/backend

if [ -d ".venv" ]; then
    # Activate virtual environment
    source .venv/bin/activate

    # Export DATABASE_URL for Alembic
    export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"

    # Run migrations
    if uv run alembic upgrade head; then
        log_info "✓ Migrations completed successfully!"
    else
        log_error "✗ Migrations failed!"
        log_error "Check the logs above for details"
        exit 1
    fi

    deactivate
else
    log_warn "Virtual environment not found at /opt/mindflow/backend/.venv"
    log_warn "Run migrations manually:"
    log_warn "  cd /opt/mindflow/backend"
    log_warn "  source .venv/bin/activate"
    log_warn "  uv run alembic upgrade head"
fi

# ============================================================================
# VERIFY SCHEMA
# ============================================================================

log_info "Verifying database schema..."

TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h localhost -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")

log_info "Found $TABLE_COUNT tables in database"

if [ "$TABLE_COUNT" -gt 0 ]; then
    log_info "Tables created:"
    PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h localhost -c "\dt"
else
    log_warn "No tables found. Migrations may not have run successfully."
fi

# ============================================================================
# SUMMARY
# ============================================================================

log_info "=========================================="
log_info "Database setup complete!"
log_info "=========================================="
log_info ""
log_info "Database details:"
log_info "  Name: $DB_NAME"
log_info "  User: $DB_USER"
log_info "  Host: localhost"
log_info "  Port: 5432"
log_info ""
log_info "Credentials saved to:"
log_info "  $CREDENTIALS_FILE (chmod 600)"
log_info ""
log_info ".env.production updated with:"
log_info "  DATABASE_URL=postgresql://$DB_USER:****@localhost:5432/$DB_NAME"
log_info ""
log_info "Tables created: $TABLE_COUNT"
log_info ""
log_info "Test connection:"
log_info "  PGPASSWORD='$DB_PASSWORD' psql -U $DB_USER -d $DB_NAME -h localhost"
log_info ""
log_info "Next steps:"
log_info "  1. Verify .env.production has correct DATABASE_URL"
log_info "  2. Start the application: sudo systemctl start mindflow"
log_info "  3. Check logs: sudo journalctl -u mindflow -f"
log_info ""
log_info "=========================================="
