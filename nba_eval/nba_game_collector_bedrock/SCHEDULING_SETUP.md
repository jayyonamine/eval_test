# Automated Daily Updates - Setup Guide

Complete guide for setting up automated daily sports data updates and evaluation.

## Overview

This guide shows you how to schedule the sports betting evaluation pipeline to run automatically every day, ensuring your data stays up-to-date without manual intervention.

## Components

1. **`run_daily_update.sh`** - Wrapper script with logging, error handling, and notifications
2. **Scheduler** - Cron (Linux) or launchd (macOS) to run the script daily
3. **Logs** - Automatic logging and cleanup of old logs

## Quick Start

### Option 1: macOS (launchd) - Recommended

```bash
# 1. Edit the plist file with your paths
nano scheduling/com.tenkiai.sports-eval.plist

# 2. Update these values:
#    - All paths to match your installation
#    - Hour/Minute for when to run (default: 6:00 AM)
#    - Environment variables (GCP_PROJECT_ID, AWS credentials)

# 3. Install the launchd job
cp scheduling/com.tenkiai.sports-eval.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.tenkiai.sports-eval.plist

# 4. Verify it's loaded
launchctl list | grep sports-eval
```

### Option 2: Linux/macOS (cron)

```bash
# 1. Open crontab editor
crontab -e

# 2. Add this line (runs daily at 6:00 AM):
0 6 * * * /path/to/eval_test/nba_eval/nba_game_collector_bedrock/run_daily_update.sh --sport all >> /path/to/logs/cron.log 2>&1

# 3. Save and exit
# Cron will automatically pick up the changes
```

## Detailed Setup

### 1. Configure Environment

Create or update your `.env` file:

```bash
cd /path/to/nba_game_collector_bedrock

# Create .env if it doesn't exist
cat > .env << 'EOF'
# GCP Configuration
GCP_PROJECT_ID=tenki-476718
GCP_CREDENTIALS_PATH=/path/to/credentials.json

# AWS Configuration (for Bedrock)
AWS_REGION=us-east-2
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0

# Email Notifications (optional)
NOTIFY_EMAIL=your-email@example.com
FROM_EMAIL=noreply@example.com
EOF

chmod 600 .env  # Protect sensitive data
```

### 2. Test the Script

Before scheduling, test the script manually:

```bash
# Test with verbose output
./run_daily_update.sh --verbose --sport nba

# Test all sports
./run_daily_update.sh --verbose

# Test specific date
./run_daily_update.sh --date 2025-12-08 --sport all

# Check logs
tail -f logs/daily_update_$(date +%Y%m%d).log
```

### 3. macOS launchd Setup (Detailed)

#### Step 1: Customize the plist file

Edit `scheduling/com.tenkiai.sports-eval.plist`:

```xml
<!-- Update these paths to match your installation -->
<key>ProgramArguments</key>
<array>
    <string>/Users/YOUR_USERNAME/path/to/run_daily_update.sh</string>
    <string>--sport</string>
    <string>all</string>
</array>

<key>WorkingDirectory</key>
<string>/Users/YOUR_USERNAME/path/to/nba_game_collector_bedrock</string>

<!-- Schedule: Hour (0-23) and Minute (0-59) -->
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>6</integer>  <!-- 6:00 AM -->
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

#### Step 2: Install the job

```bash
# Copy to LaunchAgents directory
cp scheduling/com.tenkiai.sports-eval.plist ~/Library/LaunchAgents/

# Load the job
launchctl load ~/Library/LaunchAgents/com.tenkiai.sports-eval.plist

# Verify it's loaded
launchctl list | grep sports-eval
```

#### Step 3: Manage the job

```bash
# Start immediately (for testing)
launchctl start com.tenkiai.sports-eval

# Stop the job
launchctl stop com.tenkiai.sports-eval

# Unload the job (disable scheduling)
launchctl unload ~/Library/LaunchAgents/com.tenkiai.sports-eval.plist

# Reload after changes
launchctl unload ~/Library/LaunchAgents/com.tenkiai.sports-eval.plist
launchctl load ~/Library/LaunchAgents/com.tenkiai.sports-eval.plist
```

#### Step 4: Check logs

```bash
# View launchd logs
tail -f logs/launchd.stdout.log
tail -f logs/launchd.stderr.log

# View script logs
tail -f logs/daily_update_$(date +%Y%m%d).log

# View error log
tail -f logs/errors.log
```

### 4. Linux Cron Setup (Detailed)

#### Step 1: Choose your schedule

Cron format: `minute hour day month weekday command`

Examples:
```bash
# Daily at 6:00 AM
0 6 * * * /path/to/run_daily_update.sh

# Daily at 3:30 AM
30 3 * * * /path/to/run_daily_update.sh

# Twice daily (6 AM and 6 PM)
0 6,18 * * * /path/to/run_daily_update.sh

# Weekdays only at 7 AM
0 7 * * 1-5 /path/to/run_daily_update.sh
```

#### Step 2: Edit crontab

```bash
# Open crontab editor
crontab -e

# Add your schedule (update path!)
0 6 * * * cd /path/to/nba_game_collector_bedrock && ./run_daily_update.sh --sport all

# Save and exit (:wq in vim)
```

#### Step 3: Verify cron job

```bash
# List your cron jobs
crontab -l

# Check cron service is running
systemctl status cron  # Ubuntu/Debian
systemctl status crond  # CentOS/RedHat
```

#### Step 4: Monitor logs

```bash
# Cron sends output to system mail by default
# Check mail
mail

# Or redirect to a log file
0 6 * * * /path/to/run_daily_update.sh >> /var/log/sports-eval.log 2>&1
```

## Script Options

The `run_daily_update.sh` script supports several options:

```bash
# Update all sports (default)
./run_daily_update.sh --sport all

# Update specific sport only
./run_daily_update.sh --sport nba
./run_daily_update.sh --sport nhl
./run_daily_update.sh --sport nfl

# Specify date to process
./run_daily_update.sh --date 2025-12-08

# Enable email notifications on failure
./run_daily_update.sh --notify

# Verbose output
./run_daily_update.sh --verbose

# Combine options
./run_daily_update.sh --sport nba --date 2025-12-08 --verbose --notify
```

## Logging

### Log Files

All logs are stored in the `logs/` directory:

```
logs/
├── daily_update_20251208.log  # Daily run logs
├── daily_update_20251209.log
├── errors.log                  # Errors only
├── launchd.stdout.log         # launchd output (macOS)
└── launchd.stderr.log         # launchd errors (macOS)
```

### Log Rotation

The script automatically:
- Creates a new log file each day
- Keeps logs for 30 days
- Deletes logs older than 30 days

### View Logs

```bash
# Today's log
tail -f logs/daily_update_$(date +%Y%m%d).log

# Recent errors
tail -20 logs/errors.log

# All logs from last 7 days
find logs/ -name "daily_update_*.log" -mtime -7 -exec cat {} \;

# Search for errors
grep -r "ERROR" logs/
```

## Email Notifications

### Setup

1. Set environment variables:
```bash
export NOTIFY_EMAIL=your-email@example.com
export FROM_EMAIL=noreply@yourdomain.com
```

2. Install mail command (if needed):
```bash
# macOS (usually pre-installed)
# No action needed

# Ubuntu/Debian
sudo apt-get install mailutils

# CentOS/RedHat
sudo yum install mailx
```

3. Run with `--notify` flag:
```bash
./run_daily_update.sh --notify
```

### Configure Mail Relay

For production use, configure a mail relay (e.g., SendGrid, AWS SES):

```bash
# Example: Configure postfix to use Gmail SMTP
# Edit /etc/postfix/main.cf
# Add:
relayhost = [smtp.gmail.com]:587
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_CAfile = /etc/ssl/certs/ca-bundle.crt
smtp_use_tls = yes
```

## Monitoring

### Check if Updates Are Running

```bash
# Check most recent log
ls -lt logs/daily_update_*.log | head -1

# Verify BigQuery was updated
python3 utils/verify_auto_population.py

# Check database directly
bq query --use_legacy_sql=false '
SELECT
    game_date,
    COUNT(*) as games
FROM `tenki-476718.nba_data.game_results`
GROUP BY game_date
ORDER BY game_date DESC
LIMIT 10
'
```

### Alert on Failures

Set up monitoring with:

1. **Email notifications** (built-in with `--notify`)
2. **Log monitoring** (e.g., Datadog, Splunk)
3. **Dead man's switch** (e.g., healthchecks.io)

Example healthchecks.io integration:

```bash
# Add to run_daily_update.sh after successful run
curl -fsS --retry 3 https://hc-ping.com/your-uuid-here
```

## Troubleshooting

### Script doesn't run

```bash
# Check if job is loaded (macOS)
launchctl list | grep sports-eval

# Check cron logs (Linux)
grep CRON /var/log/syslog  # Ubuntu/Debian
grep CRON /var/log/cron    # CentOS/RedHat

# Test script manually
./run_daily_update.sh --verbose
```

### Permission errors

```bash
# Make script executable
chmod +x run_daily_update.sh

# Check file permissions
ls -la run_daily_update.sh

# Check log directory permissions
ls -la logs/
```

### Environment variables not found

```bash
# Verify .env file exists
ls -la .env

# Check environment in script
# Add to run_daily_update.sh for debugging:
env | grep -E 'GCP|AWS' >> logs/env_debug.log
```

### launchd job not running (macOS)

```bash
# Check system logs
log show --predicate 'subsystem == "com.apple.launchd"' --info

# Check job status
launchctl print gui/$(id -u)/com.tenkiai.sports-eval

# Force run immediately
launchctl start com.tenkiai.sports-eval
```

## Best Practices

1. **Test first** - Always test manually before scheduling
2. **Monitor logs** - Check logs daily for the first week
3. **Set up notifications** - Get alerted when failures occur
4. **Backup data** - Ensure BigQuery has backups enabled
5. **Update schedules** - Adjust timing based on when games typically finish
6. **Review performance** - Check accuracy metrics regularly

## Scheduling Recommendations

### NBA
- Games typically finish by midnight ET
- **Recommended:** 6:00 AM ET (next day)

### NHL
- Games typically finish by 11:00 PM ET
- **Recommended:** 6:00 AM ET (next day)

### NFL
- Games typically finish by midnight ET
- Most games on Sunday, some Monday/Thursday
- **Recommended:** 6:00 AM ET (next day)

### All Sports
- **Recommended:** Single run at 6:00 AM ET daily
- Processes all completed games from previous day

## Support

If you encounter issues:

1. Check logs: `tail -f logs/errors.log`
2. Run manually with verbose: `./run_daily_update.sh --verbose`
3. Verify system health: `python3 utils/verify_auto_population.py`
4. Review this guide for troubleshooting steps

---

**Last Updated:** December 8, 2025
