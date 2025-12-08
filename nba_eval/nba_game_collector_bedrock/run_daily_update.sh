#!/bin/bash

################################################################################
# Daily Sports Betting Evaluation Pipeline - Automated Run Script
#
# This script runs the daily update pipeline with proper logging, error handling,
# and notifications. Designed to be run via cron or launchd.
#
# Usage:
#   ./run_daily_update.sh [options]
#
# Options:
#   --sport <nba|nhl|nfl|all>  Specify sport to update (default: all)
#   --date <YYYY-MM-DD>        Specify date to process (default: yesterday)
#   --notify                   Send email notification on failure
#   --verbose                  Enable verbose logging
################################################################################

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
LOG_FILE="${LOG_DIR}/daily_update_$(date +%Y%m%d).log"
ERROR_LOG="${LOG_DIR}/errors.log"
PYTHON_CMD="python3"
DAILY_UPDATE_SCRIPT="${SCRIPT_DIR}/core/daily_update.py"

# Email notification settings (optional)
NOTIFY_EMAIL="${NOTIFY_EMAIL:-}"
FROM_EMAIL="${FROM_EMAIL:-noreply@example.com}"

# Parse command line arguments
SPORT="all"
TARGET_DATE=""
NOTIFY=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --sport)
            SPORT="$2"
            shift 2
            ;;
        --date)
            TARGET_DATE="$2"
            shift 2
            ;;
        --notify)
            NOTIFY=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create log directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

# Error handling function
handle_error() {
    local exit_code=$1
    local error_message="$2"

    log "ERROR" "${error_message}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${error_message}" >> "${ERROR_LOG}"

    # Send notification if enabled
    if [[ "${NOTIFY}" == true ]] && [[ -n "${NOTIFY_EMAIL}" ]]; then
        send_notification "${error_message}"
    fi

    exit "${exit_code}"
}

# Send email notification
send_notification() {
    local error_message="$1"

    if command -v mail &> /dev/null; then
        echo "Daily sports update failed: ${error_message}" | \
            mail -s "Sports Betting Pipeline Failed" "${NOTIFY_EMAIL}"
        log "INFO" "Error notification sent to ${NOTIFY_EMAIL}"
    else
        log "WARN" "mail command not available, cannot send notification"
    fi
}

# Main execution
main() {
    log "INFO" "=========================================="
    log "INFO" "Starting daily sports data update"
    log "INFO" "Sport: ${SPORT}"
    log "INFO" "Date: ${TARGET_DATE:-yesterday}"
    log "INFO" "=========================================="

    # Check if Python script exists
    if [[ ! -f "${DAILY_UPDATE_SCRIPT}" ]]; then
        handle_error 1 "Daily update script not found: ${DAILY_UPDATE_SCRIPT}"
    fi

    # Check if required environment variables are set
    if [[ -z "${GCP_PROJECT_ID:-}" ]]; then
        log "WARN" "GCP_PROJECT_ID not set. Loading from .env if available."
        if [[ -f "${SCRIPT_DIR}/.env" ]]; then
            set -a
            source "${SCRIPT_DIR}/.env"
            set +a
            log "INFO" "Loaded environment variables from .env"
        else
            handle_error 1 "GCP_PROJECT_ID not set and .env file not found"
        fi
    fi

    # Build command
    CMD="${PYTHON_CMD} ${DAILY_UPDATE_SCRIPT} --sport ${SPORT}"
    if [[ -n "${TARGET_DATE}" ]]; then
        CMD="${CMD} --date ${TARGET_DATE}"
    fi

    log "INFO" "Executing: ${CMD}"

    # Run the update
    if [[ "${VERBOSE}" == true ]]; then
        ${CMD} 2>&1 | tee -a "${LOG_FILE}"
        exit_code=${PIPESTATUS[0]}
    else
        ${CMD} >> "${LOG_FILE}" 2>&1
        exit_code=$?
    fi

    # Check exit code
    if [[ ${exit_code} -eq 0 ]]; then
        log "INFO" "Daily update completed successfully"
        log "INFO" "=========================================="

        # Cleanup old logs (keep last 30 days)
        find "${LOG_DIR}" -name "daily_update_*.log" -mtime +30 -delete 2>/dev/null || true

        exit 0
    else
        handle_error ${exit_code} "Daily update failed with exit code ${exit_code}"
    fi
}

# Run main function
main
