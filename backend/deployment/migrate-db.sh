#!/bin/bash
#
# MindFlow Database Setup and Migration Script
#
# This script creates the production database, user, and grants necessary permissions
# Run as user with sudo privileges
#
# Usage: ./migrate-db.sh
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

# Configuration
DB_NAME="${DB_NAME:-mindflow_prod}"
DB_USER="${DB_USER:-mindflow_app}"
DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -hex 16)}"
POSTGRES_USER="postgres"

log_info "=== MindFlow Database Setup ==="
echo ""
log_info "Database Name: $DB_NAME"
log_info "Database User: $DB_USER"
echo ""

# Check if PostgreSQL is running
if ! systemctl is-active --quiet postgresql; then
    log_error "PostgreSQL is not running. Start it with: sudo systemctl start postgresql"
    exit 1
fi

# Check if database already exists
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    log_warn "Database '$DB_NAME' already exists"
    read -p "Do you want to recreate it? This will DELETE all data! (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Dropping existing database..."
        sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;"
        sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;"
        log_success "Existing database and user dropped"
    else
        log_warn "Skipping database creation"
        exit 0
    fi
fi

# Create database and user
log_info "Creating database and user..."
sudo -u postgres psql <<EOF
-- Create database with UTF-8 encoding
CREATE DATABASE $DB_NAME
    WITH ENCODING='UTF8'
    LC_COLLATE='en_US.UTF-8'
    LC_CTYPE='en_US.UTF-8'
    TEMPLATE=template0;

-- Create application user with password
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';

-- Grant connect privilege
GRANT CONNECT ON DATABASE $DB_NAME TO $DB_USER;

-- Connect to the new database
\c $DB_NAME

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO $DB_USER;

-- Grant table permissions (for existing tables)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO $DB_USER;

-- Grant sequence permissions (for existing sequences)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;

-- Grant permissions for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $DB_USER;

-- Grant permissions for future sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO $DB_USER;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Display summary
\l $DB_NAME
\du $DB_USER
EOF

log_success "Database created successfully"

# Save credentials to file
CREDS_FILE="$HOME/mindflow_db_credentials.txt"
cat > "$CREDS_FILE" <<EOF
MindFlow Database Credentials
=============================
Generated: $(date)

Database Name: $DB_NAME
Database User: $DB_USER
Database Password: $DB_PASSWORD

Connection String (asyncpg):
DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME

Connection String (psycopg2):
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME

Connection Test:
PGPASSWORD='$DB_PASSWORD' psql -U $DB_USER -d $DB_NAME -c "SELECT version();"

=============================
IMPORTANT: Keep this file secure!
Delete after adding to .env.production
=============================
EOF

chmod 600 "$CREDS_FILE"
log_success "Credentials saved to: $CREDS_FILE"

# Test database connection
log_info "Testing database connection..."
if PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
    log_success "Database connection successful"
else
    log_error "Database connection failed"
    exit 1
fi

# Display instructions
echo ""
log_success "=== Database Setup Complete ==="
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Add DATABASE_URL to .env.production:"
echo "     DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME"
echo ""
echo "  2. Run database migrations:"
echo "     cd /opt/mindflow/backend"
echo "     uv run alembic upgrade head"
echo ""
echo "  3. Verify tables created:"
echo "     PGPASSWORD='$DB_PASSWORD' psql -U $DB_USER -d $DB_NAME -c '\dt'"
echo ""
echo -e "${RED}Security Note:${NC}"
echo "  - Credentials saved to: $CREDS_FILE"
echo "  - File permissions: 600 (read/write for owner only)"
echo "  - Delete this file after adding to .env.production"
echo "  - Never commit credentials to version control"
echo ""
log_success "Database setup completed successfully!"
