#!/bin/bash
#
# MindFlow Health Check Monitoring Script
#
# This script monitors the MindFlow API health endpoint and automatically
# restarts the service if it becomes unresponsive
#
# Add to crontab for automated monitoring:
# */5 * * * * /opt/mindflow/deployment/monitor.sh
#
# Usage: ./monitor.sh
#

set -u  # Exit on undefined variable

# Configuration
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
SERVICE_NAME="mindflow"
LOG_FILE="${LOG_FILE:-/var/log/mindflow/health.log}"
MAX_LOG_SIZE=10485760  # 10MB in bytes
TIMEOUT=10  # HTTP request timeout in seconds
MAX_FAILURES=3  # Number of consecutive failures before restart

# Alert configuration (optional)
ENABLE_EMAIL_ALERTS="${ENABLE_EMAIL_ALERTS:-false}"
ALERT_EMAIL="${ALERT_EMAIL:-admin@example.com}"
ENABLE_SLACK_ALERTS="${ENABLE_SLACK_ALERTS:-false}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

# Failure tracking file
FAILURE_COUNT_FILE="/tmp/mindflow_health_failures"

# Ensure log directory exists
LOG_DIR=$(dirname "$LOG_FILE")
if [[ ! -d "$LOG_DIR" ]]; then
    mkdir -p "$LOG_DIR"
fi

# Function to log messages with timestamp
log_message() {
    local level="$1"
    local message="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" >> "$LOG_FILE"
}

# Function to rotate log file if too large
rotate_log() {
    if [[ -f "$LOG_FILE" ]]; then
        local size=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)
        if [[ $size -gt $MAX_LOG_SIZE ]]; then
            mv "$LOG_FILE" "${LOG_FILE}.old"
            log_message "INFO" "Log rotated due to size limit"
        fi
    fi
}

# Function to send email alert (requires mail/sendmail)
send_email_alert() {
    local subject="$1"
    local body="$2"

    if [[ "$ENABLE_EMAIL_ALERTS" == "true" ]] && command -v mail &> /dev/null; then
        echo "$body" | mail -s "$subject" "$ALERT_EMAIL"
        log_message "INFO" "Email alert sent to $ALERT_EMAIL"
    fi
}

# Function to send Slack alert
send_slack_alert() {
    local message="$1"
    local color="${2:-danger}"  # danger (red), warning (yellow), good (green)

    if [[ "$ENABLE_SLACK_ALERTS" == "true" ]] && [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        local payload=$(cat <<EOF
{
    "attachments": [{
        "color": "$color",
        "title": "MindFlow Alert",
        "text": "$message",
        "footer": "MindFlow Monitoring",
        "ts": $(date +%s)
    }]
}
EOF
)
        curl -s -X POST -H 'Content-type: application/json' \
            --data "$payload" "$SLACK_WEBHOOK_URL" > /dev/null 2>&1
        log_message "INFO" "Slack alert sent"
    fi
}

# Function to get current failure count
get_failure_count() {
    if [[ -f "$FAILURE_COUNT_FILE" ]]; then
        cat "$FAILURE_COUNT_FILE"
    else
        echo "0"
    fi
}

# Function to increment failure count
increment_failure_count() {
    local count=$(get_failure_count)
    count=$((count + 1))
    echo "$count" > "$FAILURE_COUNT_FILE"
    echo "$count"
}

# Function to reset failure count
reset_failure_count() {
    echo "0" > "$FAILURE_COUNT_FILE"
}

# Function to check service status
is_service_running() {
    systemctl is-active --quiet "$SERVICE_NAME"
}

# Function to restart service
restart_service() {
    log_message "WARN" "Attempting to restart $SERVICE_NAME service..."

    if sudo systemctl restart "$SERVICE_NAME"; then
        log_message "INFO" "Service restart successful"

        # Wait for service to start
        sleep 5

        # Verify service is running
        if is_service_running; then
            log_message "INFO" "Service is now running"
            reset_failure_count

            # Send success alert
            send_email_alert "MindFlow Service Restarted" \
                "The MindFlow service was automatically restarted at $(date) and is now healthy."
            send_slack_alert "Service automatically restarted and is now healthy :white_check_mark:" "good"

            return 0
        else
            log_message "ERROR" "Service failed to start after restart"
            return 1
        fi
    else
        log_message "ERROR" "Failed to restart service"
        return 1
    fi
}

# Function to check health endpoint
check_health() {
    local response_code
    local response_body

    # Perform HTTP request with timeout
    response_code=$(curl -s -o /tmp/health_response.txt -w "%{http_code}" \
        --max-time "$TIMEOUT" \
        --connect-timeout 5 \
        "$HEALTH_URL" 2>/dev/null || echo "000")

    response_body=$(cat /tmp/health_response.txt 2>/dev/null || echo "")
    rm -f /tmp/health_response.txt

    # Check if response code is 200 and body contains "healthy"
    if [[ "$response_code" == "200" ]] && echo "$response_body" | grep -q "healthy"; then
        return 0
    else
        log_message "ERROR" "Health check failed: HTTP $response_code"
        return 1
    fi
}

# Function to collect diagnostic information
collect_diagnostics() {
    local diag_file="/tmp/mindflow_diagnostics_$(date +%Y%m%d_%H%M%S).txt"

    {
        echo "=== MindFlow Diagnostics ==="
        echo "Timestamp: $(date)"
        echo ""

        echo "=== Service Status ==="
        systemctl status "$SERVICE_NAME" --no-pager || true
        echo ""

        echo "=== Recent Logs (last 50 lines) ==="
        journalctl -u "$SERVICE_NAME" -n 50 --no-pager || true
        echo ""

        echo "=== System Resources ==="
        free -h
        df -h
        echo ""

        echo "=== Network ==="
        ss -tlnp | grep 8000 || echo "Port 8000 not listening"
        echo ""

        echo "=== Process ==="
        ps aux | grep uvicorn | grep -v grep || echo "No uvicorn process found"
        echo ""
    } > "$diag_file"

    log_message "INFO" "Diagnostics collected: $diag_file"
    echo "$diag_file"
}

# Main monitoring logic
main() {
    # Rotate log if needed
    rotate_log

    # Check if service is running
    if ! is_service_running; then
        log_message "ERROR" "Service $SERVICE_NAME is not running"

        # Collect diagnostics
        diag_file=$(collect_diagnostics)

        # Attempt restart
        if restart_service; then
            log_message "INFO" "Service recovered successfully"
        else
            send_email_alert "MindFlow Service Down" \
                "The MindFlow service is not running and failed to restart. Diagnostics: $diag_file"
            send_slack_alert "Service is down and failed to restart :x:\nDiagnostics: $diag_file" "danger"
        fi
        return
    fi

    # Check health endpoint
    if check_health; then
        log_message "INFO" "Health check passed"
        reset_failure_count
    else
        # Health check failed
        local failures=$(increment_failure_count)
        log_message "WARN" "Health check failed (attempt $failures/$MAX_FAILURES)"

        if [[ $failures -ge $MAX_FAILURES ]]; then
            log_message "ERROR" "Health check failed $MAX_FAILURES consecutive times"

            # Collect diagnostics
            diag_file=$(collect_diagnostics)

            # Send alert before restart
            send_email_alert "MindFlow Health Check Failed" \
                "Health check failed $MAX_FAILURES consecutive times. Attempting automatic restart. Diagnostics: $diag_file"
            send_slack_alert "Health check failed $MAX_FAILURES times :warning:\nAttempting automatic restart..." "warning"

            # Attempt restart
            if restart_service; then
                log_message "INFO" "Service recovered after health check failures"
            else
                send_email_alert "MindFlow Service Recovery Failed" \
                    "Failed to recover service after health check failures. Manual intervention required. Diagnostics: $diag_file"
                send_slack_alert "Service recovery failed :x:\nManual intervention required!\nDiagnostics: $diag_file" "danger"
            fi
        fi
    fi
}

# Run main function
main

# Exit successfully (important for cron)
exit 0
