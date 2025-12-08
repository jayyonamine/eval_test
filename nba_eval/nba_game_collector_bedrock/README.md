# Sports Betting Evaluation Pipeline

Fully automated pipeline that collects game results, matches them with forecasts, and evaluates betting performance.

## Quick Start

### Daily Update (Recommended)
```bash
# Update all sports for yesterday's games
python3 core/daily_update.py

# Update specific sport only
python3 core/daily_update.py --sport nba

# Update specific date
python3 core/daily_update.py --date 2025-12-08
```

### Individual Sport Updates
```bash
# NBA only
python3 nba_agent.py

# NHL only
python3 nhl_agent.py

# NFL only
python3 nfl_agent.py
```

## What Happens Automatically

When you run the daily update, the pipeline:

1. **Collects game data** from official APIs (ESPN for NBA/NFL, NHL.com for NHL)
2. **Matches games** with forecasts using game_id lookup
3. **Inserts results** into BigQuery tables
4. **Calculates eval features** automatically:
   - `actual_team_away_points`
   - `actual_team_home_points`
   - `actual_points_total`
   - `actual_team_home_win`
   - `actual_points_total_over`
   - `tenki_bet_correct`
   - `kalshi_bet_correct`

**No manual intervention required!**

## System Architecture

```
┌─────────────────┐
│  ESPN/NHL APIs  │
│  (Real Data)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Sport Agents   │
│  (NBA/NHL/NFL)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Game ID Lookup │◄─────│  Forecasts Table │
└────────┬────────┘      └──────────────────┘
         │
         ▼
┌─────────────────┐
│  BigQuery       │
│  game_results   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Auto-Populate  │
│  Eval Features  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Forecasts      │
│  With Actuals   │
└─────────────────┘
```

## Project Structure

```
/core/                  - Core pipeline scripts
  daily_update.py       - Main orchestration script
  nba_agent.py          - NBA data collector
  nhl_agent.py          - NHL data collector
  nfl_agent.py          - NFL data collector
  game_id_lookup.py     - Game ID matcher
  bigquery_writer.py    - Database writer
  populate_actual_results_auto.py  - Eval calculator

/utils/                 - Utility scripts
  verify_auto_population.py        - Health check
  preview_bet_correctness.py       - Preview calculations

/tests/                 - Test scripts
  test_game_id_auto_populate.py
  test_game_id_integration.py

/archive/               - Legacy/one-time scripts
  (historical fixes and old code)

/docs/                  - Additional documentation
  COMPLETE_SYSTEM_SUMMARY.md       - Detailed system docs
  AUTOMATED_PIPELINE_SUMMARY.md    - Pipeline details
```

## Setup

### Prerequisites
- Python 3.9+
- Google Cloud Project with BigQuery enabled
- AWS credentials (for Bedrock integration, if applicable)

### Environment Variables
```bash
export GCP_PROJECT_ID=tenki-476718
export AWS_REGION=us-east-2
export BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
```

### Install Dependencies
```bash
pip3 install -r requirements.txt
```

## BigQuery Tables

### Game Results Tables
- `tenki-476718.nba_data.game_results` - NBA games
- `tenki-476718.nhl_data.game_results` - NHL games (when forecasts available)
- `tenki-476718.nfl_data.game_results` - NFL games (when forecasts available)

### Forecasts Table
- `tenki-476718.forecasts_mike.relational_forecasts`
  - Contains betting forecasts with game_id
  - Automatically populated with actual results
  - Includes bet correctness evaluations

## Verification

Check if the pipeline is working:
```bash
python3 utils/verify_auto_population.py
```

Expected output:
```
✅ SUCCESS - All games with forecasts have actual results populated!

Automatic population is working correctly:
  1. New games collected ✓
  2. game_ids auto-populated ✓
  3. Actual results auto-populated in forecasts ✓
```

## Performance Metrics

Query evaluation metrics:
```sql
SELECT
    COUNT(*) as total_bets,
    SUM(CASE WHEN tenki_bet_correct = 1 THEN 1 ELSE 0 END) as tenki_correct,
    SUM(CASE WHEN kalshi_bet_correct = 1 THEN 1 ELSE 0 END) as kalshi_correct,
    ROUND(100.0 * SUM(tenki_bet_correct) / COUNT(*), 2) as tenki_accuracy,
    ROUND(100.0 * SUM(kalshi_bet_correct) / COUNT(*), 2) as kalshi_accuracy
FROM `tenki-476718.forecasts_mike.relational_forecasts`
WHERE actual_team_away_points IS NOT NULL
```

## Troubleshooting

### Issue: No forecasts updated
**Solution:** Game hasn't been collected yet
```bash
python3 core/daily_update.py --sport nba
```

### Issue: Games collected but forecasts not updated
**Solution:** Run manual sync
```bash
python3 core/populate_actual_results_auto.py
```

### Issue: Authentication error
**Solution:** Re-authenticate with GCP
```bash
gcloud auth application-default login
```

## Multi-Sport Support

### Current Status
- ✅ **NBA** - Fully operational with forecasts
- ⏳ **NHL** - Ready (waiting for forecasts in table)
- ⏳ **NFL** - Ready (waiting for forecasts in table)

When NHL/NFL forecasts are added to the `relational_forecasts` table, the pipeline will automatically:
1. Match games by game_id
2. Populate actual results
3. Calculate bet correctness

No code changes needed!

## Key Features

- ✅ **100% Automated** - No manual steps required
- ✅ **Real-time Sync** - Forecasts updated immediately after games
- ✅ **Multi-Sport** - NBA, NHL, NFL support
- ✅ **Error Resilient** - Graceful handling of edge cases
- ✅ **Duplicate Prevention** - Auto-detects and skips duplicates
- ✅ **Performance Tracking** - Built-in accuracy metrics

## Bet Correctness Logic

### Over/Under Bets
```python
# Bet on OVER
if tenki_points_total_over_bet == 1:
    tenki_bet_correct = 1 if actual_points_total_over == 1 else 0

# Bet on UNDER
if tenki_points_total_over_bet == 0:
    tenki_bet_correct = 1 if actual_points_total_over == 0 else 0
```

### Team Winner Bets
```python
# Bet on HOME team
if tenki_team_home_winner_bet == 1:
    tenki_bet_correct = 1 if actual_team_home_win == 1 else 0
```

## Contributing

This is an automated evaluation system. When making changes:
1. Test with individual agents first
2. Verify with `utils/verify_auto_population.py`
3. Check calculations with `utils/preview_bet_correctness.py`

## License

Internal use only.

## Support

For issues or questions, check:
- `docs/COMPLETE_SYSTEM_SUMMARY.md` - Comprehensive documentation
- `docs/AUTOMATED_PIPELINE_SUMMARY.md` - Pipeline details

---

**Last Updated:** December 8, 2025
**Pipeline Status:** ✅ Fully Operational
