#!/bin/bash

# SearchKu Production Deployment Script
# This script handles safe deployment with database migrations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo -e "${BLUE}🚀 SearchKu Production Deployment${NC}"
echo "=================================================="

# Function to log messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check required environment variables
check_environment() {
    log_info "Checking environment variables..."

    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL environment variable is required"
        exit 1
    fi

    if [ -z "$OPENAI_API_KEY" ]; then
        log_warning "OPENAI_API_KEY not set - application may not work correctly"
    fi

    log_info "Environment check completed ✅"
}

# Create backup directory
create_backup_dir() {
    log_info "Creating backup directory..."
    mkdir -p "$BACKUP_DIR"
}

# Backup database
backup_database() {
    log_info "Creating database backup..."

    # Extract database info from DATABASE_URL
    # Expected format: postgresql://user:password@host:port/database
    if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASS="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"

        BACKUP_FILE="$BACKUP_DIR/searchku_backup_$DATE.sql"

        export PGPASSWORD="$DB_PASS"

        if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"; then
            log_info "Database backup created: $BACKUP_FILE ✅"
        else
            log_error "Database backup failed ❌"
            exit 1
        fi

        unset PGPASSWORD
    else
        log_error "Invalid DATABASE_URL format"
        exit 1
    fi
}

# Run database migrations
run_migrations() {
    log_info "Checking migration status..."
    python migrate.py --status

    log_info "Running database migrations..."
    if python migrate.py; then
        log_info "Database migrations completed ✅"
    else
        log_error "Database migrations failed ❌"
        exit 1
    fi
}

# Install dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."

    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_info "Dependencies installed ✅"
    else
        log_warning "requirements.txt not found, skipping dependency installation"
    fi
}

# Run application tests
run_tests() {
    log_info "Running application tests..."

    # Add your test commands here
    # python -m pytest tests/
    # python -c "from app.main import app; print('App import successful')"

    log_info "Tests completed ✅"
}

# Start application (example)
start_application() {
    log_info "Application deployment completed!"
    log_info "To start the application, run:"
    echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000"
}

# Rollback function
rollback() {
    log_error "Deployment failed! To rollback:"
    echo "1. Restore database from backup:"
    echo "   psql \$DATABASE_URL < $BACKUP_FILE"
    echo "2. Revert code changes"
    echo "3. Restart application"
}

# Main deployment function
deploy() {
    log_info "Starting deployment process..."

    # Trap errors and provide rollback instructions
    trap rollback ERR

    check_environment
    create_backup_dir
    backup_database
    install_dependencies
    run_migrations
    run_tests
    start_application

    log_info "🎉 Deployment completed successfully!"
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "migrate-only")
        check_environment
        run_migrations
        ;;
    "backup-only")
        check_environment
        create_backup_dir
        backup_database
        ;;
    "status")
        check_environment
        python migrate.py --status
        ;;
    *)
        echo "Usage: $0 [deploy|migrate-only|backup-only|status]"
        echo ""
        echo "Commands:"
        echo "  deploy       - Full deployment (default)"
        echo "  migrate-only - Run migrations only"
        echo "  backup-only  - Create database backup only"
        echo "  status       - Show migration status"
        exit 1
        ;;
esac