
# Actual Results Population System

## Overview

Automatically populates actual game results from `nba_data.game_results` into the `forecasts_mike.relational_forecasts` table. This enables forecast evaluation and betting analysis by comparing predicted odds with actual outcomes.

## Fields Populated

The system populates 5 actual result fields in the forecasts table:

| Field | Source | Logic |
|-------|--------|-------|
| `actual_team_away_points` | `game_results.away_score` | Direct copy |
| `actual_team_home_points` | `game_results.home_score` | Direct copy |
| `actual_points_total` | `game_results.points_total` | Direct copy |
| `actual_team_home_win` | Calculated | `1` if home won, `0` if away won |
| `actual_points_total_over` | Calculated per row | `1` if total > over line, `0` otherwise |

## How It Works

### Architecture

```
┌──────────────────┐
│  game_results    │
│  (Game IDs +     │
│   Actual Scores) │
└────────┬─────────┘
         │
         │ JOIN on game_id
         │
         ▼
┌──────────────────┐
│  Forecasts       │
│  Table           │
│                  │
│  Before:         │
│  actual_* = NULL │
│                  │
│  After:          │
│  actual_* = ✓    │
└──────────────────┘
```

### Matching Logic

For each game in `game_results` with a `game_id`:
1. Find ALL forecast rows with matching `game_id`
2. Populate actual scores (same for all rows with same game_id)
3. Calculate `actual_team_home_win` based on score comparison
4. Calculate `actual_points_total_over` individually for each row based on that row's over/under line

### Example

**Game:** Lakers @ Celtics: 105-126 (Total: 231)

**Forecast Rows:**
```
game_id: abc123... | Market: KXNBATOTAL-...-220
  points_total_over: 220.5
  actual_points_total_over: 1  (231 > 220.5 = OVER)

game_id: abc123... | Market: KXNBATOTAL-...-235
  points_total_over: 235.5
  actual_points_total_over: 0  (231 < 235.5 = UNDER)
```

## Usage

### Manual Execution

#### Preview Changes (Dry Run)
```bash
python3 preview_actual_results.py
```

Shows what will be updated without making changes.

#### Interactive Execution
```bash
python3 populate_actual_results.py
```

Prompts for confirmation before updating.

#### Automated Execution
```bash
python3 populate_actual_results_auto.py
```

Runs without prompts (use in automated pipelines).

#### Comprehensive Update (Recommended)
```bash
python3 update_sports_with_actuals.py
```

Does everything:
1. Updates game results for NBA/NHL/NFL
2. Populates game_ids automatically
3. Populates actual results in forecasts

### Integration Example

```python
from populate_actual_results_auto import populate_actual_results, validate_results
from google.cloud import bigquery

# After collecting new games
client = bigquery.Client(project="your-project")
populate_actual_results(client)
validate_results(client)
```

## Technical Details

### Why Table Recreation?

BigQuery's streaming buffer prevents UPDATE/DELETE operations on recently inserted data. To avoid this limitation, we use a table recreation approach:

1. Create temp table with actual results populated via JOIN
2. Drop original forecasts table
3. Recreate original table from temp
4. Drop temp table

This ensures:
- ✅ No streaming buffer conflicts
- ✅ All rows updated atomically
- ✅ COALESCE preserves existing actual values
- ✅ Works regardless of when data was inserted

### Query Pattern

```sql
CREATE OR REPLACE TABLE forecasts_temp AS
SELECT
    rf.* EXCEPT(actual_team_away_points, actual_team_home_points, ...),
    -- Use COALESCE to preserve existing values
    COALESCE(rf.actual_team_away_points, gr.away_score) as actual_team_away_points,
    COALESCE(rf.actual_team_home_points, gr.home_score) as actual_team_home_points,
    COALESCE(rf.actual_points_total, gr.points_total) as actual_points_total,
    COALESCE(rf.actual_team_home_win,
        CASE WHEN gr.home_score > gr.away_score THEN 1 ELSE 0 END
    ) as actual_team_home_win,
    COALESCE(rf.actual_points_total_over,
        CASE WHEN gr.points_total > rf.points_total_over THEN 1 ELSE 0 END
    ) as actual_points_total_over
FROM forecasts_mike.relational_forecasts rf
LEFT JOIN nba_data.game_results gr
    ON rf.game_id = gr.game_id
```

## Current Status (as of Dec 7, 2025)

```
Forecasts Table Summary:
├── Total unique games: 26
├── Games with actual results: 19
│   ├── Dec 5: 12 games ✓
│   └── Dec 6: 7 games ✓
├── Games without actual results: 7
│   └── Dec 7: 7 games (not played yet)
├── Total forecast rows: 396
└── Rows with actual results: 312
```

## Forecast Evaluation Use Cases

With actual results populated, you can now:

### 1. Evaluate Model Accuracy
```sql
SELECT
    AVG(CASE
        WHEN actual_team_home_win = tenki_team_home_winner_bet THEN 1.0
        ELSE 0.0
    END) as tenki_accuracy
FROM forecasts_mike.relational_forecasts
WHERE actual_team_home_win IS NOT NULL
```

### 2. Calculate Edge Profitability
```sql
SELECT
    AVG(CASE
        WHEN actual_points_total_over = 1 AND tenki_points_total_over_bet = 1 THEN 1.0
        WHEN actual_points_total_over = 0 AND tenki_points_total_over_bet = 0 THEN 1.0
        ELSE 0.0
    END) as over_under_accuracy
FROM forecasts_mike.relational_forecasts
WHERE actual_points_total_over IS NOT NULL
```

### 3. Compare Tenki vs Kalshi
```sql
SELECT
    COUNT(CASE WHEN actual_team_home_win = tenki_team_home_winner_bet THEN 1 END) as tenki_correct,
    COUNT(CASE WHEN actual_team_home_win = kalshi_team_home_winner_bet THEN 1 END) as kalshi_correct,
    COUNT(*) as total_bets
FROM forecasts_mike.relational_forecasts
WHERE actual_team_home_win IS NOT NULL
```

## Future Enhancements

- [ ] Extend to NHL and NFL (when forecasts available)
- [ ] Add automatic execution trigger after game collection
- [ ] Calculate profit/loss fields automatically
- [ ] Add bet outcome fields (win/loss/push)
- [ ] Track betting bankroll simulation

## Troubleshooting

### No Games Updated
**Issue:** Script completes but 0 rows updated

**Solution:**
- Check that games have `game_id` populated
- Verify forecasts exist for those games
- Run `preview_actual_results.py` to see what will match

### Streaming Buffer Error
**Issue:** "UPDATE or DELETE statement over table would affect rows in the streaming buffer"

**Solution:** Use `populate_actual_results_auto.py` which uses table recreation instead of UPDATE

### Missing game_id Values
**Issue:** Games in `game_results` don't have `game_id`

**Solution:**
1. Run `update_game_ids_dec6.py` to backfill historical game_ids
2. Ensure new games use the updated agents (automatic game_id population)

## Related Documentation

- [GAME_ID_AUTO_POPULATION.md](./GAME_ID_AUTO_POPULATION.md) - Automatic game_id population
- [README.md](./README.md) - Main project documentation

## Scripts Summary

| Script | Purpose | Use When |
|--------|---------|----------|
| `preview_actual_results.py` | Preview changes | Want to see what will update |
| `populate_actual_results.py` | Interactive update | Running manually |
| `populate_actual_results_auto.py` | Automated update | Running in pipeline |
| `update_sports_with_actuals.py` | Full pipeline | Want everything updated |

## Support

For issues:
1. Run preview script to check matching
2. Verify game_ids are populated
3. Check that forecasts exist for target games
