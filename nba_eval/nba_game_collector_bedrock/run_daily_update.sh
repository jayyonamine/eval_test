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
#   --notify                   Send email notification (success and failure)
#   --notify-errors-only       Send email only on failures
#   --verbose                  Enable verbose logging
################################################################################

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
LOG_FILE="${LOG_DIR}/daily_update_$(date +%Y%m%d).log"
ERROR_LOG="${LOG_DIR}/errors.log"
SUMMARY_FILE="${LOG_DIR}/summary_$(date +%Y%m%d).txt"
PYTHON_CMD="python3"
DAILY_UPDATE_SCRIPT="${SCRIPT_DIR}/core/daily_update.py"

# Email notification settings (load from .env if available)
if [[ -f "${SCRIPT_DIR}/.env" ]]; then
    export $(grep -v '^#' "${SCRIPT_DIR}/.env" | xargs)
fi

NOTIFY_EMAIL="${NOTIFY_EMAIL:-}"
FROM_EMAIL="${FROM_EMAIL:-noreply@tenkiai.com}"

# Parse command line arguments
SPORT="all"
TARGET_DATE=""
NOTIFY=false
NOTIFY_ERRORS_ONLY=false
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
        --notify-errors-only)
            NOTIFY=true
            NOTIFY_ERRORS_ONLY=true
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

# If NOTIFY_EMAIL is set, enable notifications by default
if [[ -n "${NOTIFY_EMAIL}" ]] && [[ "${NOTIFY}" == false ]]; then
    NOTIFY=true
fi

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

# Extract summary from log
extract_summary() {
    local log_file="$1"
    local summary=""

    # Extract game counts from log
    local nba_inserted=$(grep -A 10 "NBA UPDATE" "${log_file}" 2>/dev/null | grep "Inserted:" | awk '{print $2}' || echo "0")
    local nhl_inserted=$(grep -A 10 "NHL UPDATE" "${log_file}" 2>/dev/null | grep "Inserted:" | awk '{print $2}' || echo "0")
    local nfl_inserted=$(grep -A 10 "NFL UPDATE" "${log_file}" 2>/dev/null | grep "Inserted:" | awk '{print $2}' || echo "0")

    local nba_duplicates=$(grep -A 10 "NBA UPDATE" "${log_file}" 2>/dev/null | grep "duplicates" | awk '{print $3}' | tr -d ')' || echo "0")
    local nhl_duplicates=$(grep -A 10 "NHL UPDATE" "${log_file}" 2>/dev/null | grep "duplicates" | awk '{print $3}' | tr -d ')' || echo "0")
    local nfl_duplicates=$(grep -A 10 "NFL UPDATE" "${log_file}" 2>/dev/null | grep "duplicates" | awk '{print $3}' | tr -d ')' || echo "0")

    # Extract forecast updates
    local forecasts_updated=$(grep "Populated actual results for" "${log_file}" 2>/dev/null | tail -1 | awk '{print $6}' || echo "0")

    # Build summary
    summary="Daily Sports Data Update Summary\n"
    summary+="Date: $(date '+%Y-%m-%d %H:%M:%S')\n"
    summary+="Target Date: ${TARGET_DATE:-yesterday}\n"
    summary+="\n"
    summary+="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    summary+="\n"

    if [[ "${SPORT}" == "all" ]] || [[ "${SPORT}" == "nba" ]]; then
        summary+="NBA:\n"
        summary+="  • New games inserted: ${nba_inserted}\n"
        summary+="  • Duplicates skipped: ${nba_duplicates}\n"
        summary+="\n"
    fi

    if [[ "${SPORT}" == "all" ]] || [[ "${SPORT}" == "nhl" ]]; then
        summary+="NHL:\n"
        summary+="  • New games inserted: ${nhl_inserted}\n"
        summary+="  • Duplicates skipped: ${nhl_duplicates}\n"
        summary+="\n"
    fi

    if [[ "${SPORT}" == "all" ]] || [[ "${SPORT}" == "nfl" ]]; then
        summary+="NFL:\n"
        summary+="  • New games inserted: ${nfl_inserted}\n"
        summary+="  • Duplicates skipped: ${nfl_duplicates}\n"
        summary+="\n"
    fi

    summary+="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    summary+="\n"
    summary+="Evaluation Features:\n"
    summary+="  • Forecast rows updated: ${forecasts_updated}\n"
    summary+="\n"
    summary+="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    summary+="\n"

    # Calculate totals
    local total_inserted=$((nba_inserted + nhl_inserted + nfl_inserted))
    local total_duplicates=$((nba_duplicates + nhl_duplicates + nfl_duplicates))

    summary+="Overall:\n"
    summary+="  • Total new games: ${total_inserted}\n"
    summary+="  • Total duplicates: ${total_duplicates}\n"
    summary+="  • Forecasts evaluated: ${forecasts_updated}\n"
    summary+="\n"

    echo -e "${summary}" > "${SUMMARY_FILE}"
    echo -e "${summary}"
}

# Send email notification
send_notification() {
    local subject="$1"
    local message="$2"
    local is_error="${3:-false}"

    # Skip success notifications if only errors are requested
    if [[ "${is_error}" == "false" ]] && [[ "${NOTIFY_ERRORS_ONLY}" == "true" ]]; then
        log "INFO" "Skipping success notification (errors-only mode)"
        return
    fi

    if [[ -z "${NOTIFY_EMAIL}" ]]; then
        log "WARN" "NOTIFY_EMAIL not set, cannot send notification"
        return
    fi

    if command -v mail &> /dev/null; then
        echo -e "${message}" | mail -s "${subject}" "${NOTIFY_EMAIL}"
        log "INFO" "Email notification sent to ${NOTIFY_EMAIL}"
    elif command -v sendmail &> /dev/null; then
        (
            echo "To: ${NOTIFY_EMAIL}"
            echo "From: ${FROM_EMAIL}"
            echo "Subject: ${subject}"
            echo ""
            echo -e "${message}"
        ) | sendmail -t
        log "INFO" "Email notification sent to ${NOTIFY_EMAIL} via sendmail"
    else
        log "WARN" "Neither mail nor sendmail command available, cannot send notification"
    fi
}

# Error handling function
handle_error() {
    local exit_code=$1
    local error_message="$2"

    log "ERROR" "${error_message}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${error_message}" >> "${ERROR_LOG}"

    # Send error notification
    if [[ "${NOTIFY}" == true ]] && [[ -n "${NOTIFY_EMAIL}" ]]; then
        local email_body="Sports Betting Evaluation Pipeline - ERROR\n\n"
        email_body+="An error occurred during the daily update:\n\n"
        email_body+="${error_message}\n\n"
        email_body+="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        email_body+="Recent log entries:\n\n"
        email_body+="$(tail -20 "${LOG_FILE}" 2>/dev/null || echo 'Log file not available')\n\n"
        email_body+="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        email_body+="Check full logs at:\n${LOG_FILE}\n"

        send_notification "⚠️ Sports Pipeline Failed - $(date +%Y-%m-%d)" "${email_body}" "true"
    fi

    exit "${exit_code}"
}

# Main execution
main() {
    log "INFO" "=========================================="
    log "INFO" "Starting daily sports data update"
    log "INFO" "Sport: ${SPORT}"
    log "INFO" "Date: ${TARGET_DATE:-yesterday}"
    log "INFO" "Notifications: ${NOTIFY} (Email: ${NOTIFY_EMAIL:-not set})"
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

        # Extract and display summary
        log "INFO" "Generating summary..."
        extract_summary "${LOG_FILE}"

        # Send success notification with summary
        if [[ "${NOTIFY}" == true ]] && [[ -n "${NOTIFY_EMAIL}" ]]; then
            local summary_content=$(cat "${SUMMARY_FILE}")
            local email_body="✅ Sports Betting Evaluation Pipeline - SUCCESS\n\n"
            email_body+="${summary_content}\n"
            email_body+="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            email_body+="All games processed successfully.\n"
            email_body+="Evaluation features calculated automatically.\n\n"
            email_body+="Full log: ${LOG_FILE}\n"

            send_notification "✅ Sports Pipeline Success - $(date +%Y-%m-%d)" "${email_body}" "false"
        fi

        # Cleanup old logs (keep last 30 days)
        find "${LOG_DIR}" -name "daily_update_*.log" -mtime +30 -delete 2>/dev/null || true
        find "${LOG_DIR}" -name "summary_*.txt" -mtime +30 -delete 2>/dev/null || true

        exit 0
    else
        handle_error ${exit_code} "Daily update failed with exit code ${exit_code}"
    fi
}

# Run main function
main
