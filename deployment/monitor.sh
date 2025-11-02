#!/bin/bash

# MindFlow Health Monitoring Script
# Monitors application health and automatically restarts on failure
# Usage: Run via cron every 5 minutes
#   */5 * * * * /opt/mindflow/deployment/monitor.sh

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

# Health check endpoint
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"

# Timeout for health check (seconds)
TIMEOUT=10

# Number of consecutive failures before restart
MAX_FAILURES=3

# Log file
LOG_FILE="/var/log/mindflow/health.log"
LOG_MAX_SIZE=10485760  # 10MB

# Failure count file
FAILURE_COUNT_FILE="/tmp/mindflow_failures"

# Alert configuration (optional)
ENABLE_EMAIL_ALERTS=false
ALERT_EMAIL=""
ENABLE_SLACK_ALERTS=false
SLACK_WEBHOOK_URL=""

# ============================================================================
# LOGGING
# ============================================================================

log() {
    local level=$1
    shift
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $*" >> "$LOG_FILE"
}

log_info() {
    log "INFO" "$@"
}

log_warn() {
    log "WARN" "$@"
}

log_error() {
    log "ERROR" "$@"
}

# ============================================================================
# LOG ROTATION
# ============================================================================

rotate_log_if_needed() {
    if [ -f "$LOG_FILE" ]; then
        local log_size=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
        if [ "$log_size" -gt "$LOG_MAX_SIZE" ]; then
            mv "$LOG_FILE" "${LOG_FILE}.$(date +%Y%m%d_%H%M%S)"
            touch "$LOG_FILE"
            chown deploy:deploy "$LOG_FILE" 2>/dev/null || true
            log_info "Log rotated (size: $log_size bytes)"
        fi
    else
        mkdir -p "$(dirname "$LOG_FILE")"
        touch "$LOG_FILE"
        chown deploy:deploy "$LOG_FILE" 2>/dev/null || true
    fi
}

# ============================================================================
# FAILURE COUNTER
# ============================================================================

get_failure_count() {
    if [ -f "$FAILURE_COUNT_FILE" ]; then
        cat "$FAILURE_COUNT_FILE"
    else
        echo 0
    fi
}

increment_failure_count() {
    local count=$(get_failure_count)
    count=$((count + 1))
    echo $count > "$FAILURE_COUNT_FILE"
    echo $count
}

reset_failure_count() {
    echo 0 > "$FAILURE_COUNT_FILE"
}

# ============================================================================
# HEALTH CHECK
# ============================================================================

check_health() {
    local response
    local http_code

    # Perform health check
    response=$(curl -s -w "\n%{http_code}" --max-time "$TIMEOUT" "$HEALTH_URL" 2>&1)
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "200" ]; then
        # Parse JSON response (requires jq, or just check for "ok")
        if echo "$response" | head -n-1 | grep -q '"status":"ok"'; then
            return 0  # Healthy
        else
            log_warn "Health check returned 200 but status is not 'ok'"
            return 1  # Unhealthy
        fi
    else
        log_error "Health check failed with HTTP code: $http_code"
        return 1  # Unhealthy
    fi
}

# ============================================================================
# SERVICE STATUS
# ============================================================================

check_service_status() {
    if systemctl is-active --quiet mindflow; then
        return 0  # Running
    else
        log_error "Service is not running"
        return 1  # Not running
    fi
}

# ============================================================================
# RESTART SERVICE
# ============================================================================

restart_service() {
    log_warn "Attempting to restart mindflow service..."

    # Get diagnostic info before restart
    log_info "Service status before restart:"
    systemctl status mindflow --no-pager >> "$LOG_FILE" 2>&1 || true

    log_info "Last 20 lines of service logs:"
    journalctl -u mindflow -n 20 --no-pager >> "$LOG_FILE" 2>&1 || true

    # Restart service
    if systemctl restart mindflow; then
        log_info "Service restarted successfully"

        # Wait for service to stabilize
        sleep 5

        # Verify service is running
        if systemctl is-active --quiet mindflow; then
            log_info "Service is running after restart"
            reset_failure_count
            send_alert "✅ MindFlow service restarted successfully"
            return 0
        else
            log_error "Service failed to start after restart"
            send_alert "❌ MindFlow service restart failed"
            return 1
        fi
    else
        log_error "Failed to restart service"
        send_alert "❌ MindFlow service restart command failed"
        return 1
    fi
}

# ============================================================================
# ALERTS
# ============================================================================

send_email_alert() {
    local message=$1

    if [ "$ENABLE_EMAIL_ALERTS" = true ] && [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "MindFlow Alert" "$ALERT_EMAIL" 2>/dev/null || \
            log_warn "Failed to send email alert"
    fi
}

send_slack_alert() {
    local message=$1

    if [ "$ENABLE_SLACK_ALERTS" = true ] && [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || \
            log_warn "Failed to send Slack alert"
    fi
}

send_alert() {
    local message=$1
    log_info "Alert: $message"
    send_email_alert "$message"
    send_slack_alert "$message"
}

# ============================================================================
# MAIN MONITORING LOGIC
# ============================================================================

main() {
    # Rotate log if needed
    rotate_log_if_needed

    # Log monitoring start
    log_info "Starting health check..."

    # Check if service is running
    if ! check_service_status; then
        log_error "Service is not running, attempting restart..."
        restart_service
        exit 0
    fi

    # Perform health check
    if check_health; then
        # Service is healthy
        local prev_failures=$(get_failure_count)
        if [ "$prev_failures" -gt 0 ]; then
            log_info "Service recovered after $prev_failures failure(s)"
            send_alert "✅ MindFlow service recovered (was failing for $prev_failures check(s))"
        fi
        reset_failure_count
        log_info "Health check passed ✓"
        exit 0
    else
        # Service is unhealthy
        local failures=$(increment_failure_count)
        log_warn "Health check failed (failure $failures/$MAX_FAILURES)"

        if [ "$failures" -ge "$MAX_FAILURES" ]; then
            log_error "Max failures reached ($MAX_FAILURES), restarting service..."
            send_alert "⚠️ MindFlow service unhealthy for $failures consecutive checks, restarting..."
            restart_service
        else
            log_warn "Waiting for more failures before restarting (threshold: $MAX_FAILURES)"
        fi
        exit 1
    fi
}

# ============================================================================
# ERROR HANDLING
# ============================================================================

trap 'log_error "Script interrupted"; exit 1' INT TERM

# ============================================================================
# RUN
# ============================================================================

main "$@"
