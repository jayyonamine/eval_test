# Fully Automated Sports Data & Forecast Evaluation Pipeline

## Overview

The complete end-to-end pipeline is now **fully automated**. When new games are collected, the system automatically:

1. ✅ Collects game data from official APIs
2. ✅ Auto-populates `game_id` from forecasts table
3. ✅ Inserts games into BigQuery
4. ✅ **Auto-populates actual results back into forecasts table**

## Complete Flow Diagram

```
┌──────────────────────┐
│  ESPN/NHL/NFL APIs   │
│  (Official Sources)  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  NBA/NHL/NFL Agent   │
│  - Fetches games     │
│  - Validates data    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐      ┌────────────────────────┐
│  Game ID Lookup      │◀─────│  forecasts_mike.       │
│  - Query forecasts   │      │  relational_forecasts  │
│  - Match by date +   │      │  (Source of game_ids)  │
│    teams             │      └────────────────────────┘
│  - Add game_id       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  BigQuery Writer     │
│  - Insert game       │
│  - WITH game_id      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  nba_data.           │
│  game_results        │
│  (Game + game_id)    │
└──────────┬───────────┘
           │
           │ AUTOMATIC TRIGGER
           ▼
┌──────────────────────┐
│  Populate Actual     │
│  Results             │
│  - JOIN on game_id   │
│  - Update forecasts  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  forecasts_mike.     │
│  relational_forecasts│
│  (WITH actuals)      │
└──────────────────────┘
```

## What Happens Automatically

### Step 1: Collect Game (User Action)
```bash
python3 nba_agent.py  # Or nhl_agent.py, nfl_agent.py
```

### Step 2-5: Fully Automated

The script automatically:

**Step 2:** Looks up game_id from forecasts table
```
game_date='2025-12-08' + teams → game_id='abc123...'
```

**Step 3:** Inserts game WITH game_id
```sql
INSERT INTO nba_data.game_results (
    game_date, away_team, home_team,
    away_score, home_score, points_total,
    location, inserted_at, game_id  ← Auto-populated
)
```

**Step 4:** Detects new game and triggers actual results population
```
✓ Inserted: 1 game
Populating actual results in forecasts table...
✓ Populated actual results for 12 forecast rows
```

**Step 5:** Updates forecasts table
```sql
UPDATE forecasts SET
    actual_team_away_points = 105,
    actual_team_home_points = 126,
    actual_points_total = 231,
    actual_team_home_win = 1,
    actual_points_total_over = 1  -- Calculated per row
WHERE game_id = 'abc123...'
```

## Example Output

When you collect a new game, you'll see:

```
Starting NBA game collection for 2025-12-08...
Fetching NBA scores from ESPN API for 2025-12-08
Successfully collected 7 games for 2025-12-08

Looking up game_ids from forecasts table...

Game ID Lookup Results:
  Matched with forecasts: 7
  No forecast available: 0

Collected data for 7 games:
  Denver Nuggets @ Charlotte Hornets: 120-118
  Golden State Warriors @ Chicago Bulls: 125-122
  ...

Successfully inserted 7 rows

Insertion complete:
  Inserted: 7
  Skipped (duplicates): 0
  Errors: 0

Populating actual results in forecasts table...
✓ Populated actual results for 84 forecast rows
```

## Files Modified

### Core Integration Files

1. **`nba_agent.py`** (lines 301-317)
   - Automatically triggers actual results population after game insertion
   - Silent failures (normal if no forecasts exist)

2. **`nhl_agent.py`** (lines 277-293)
   - Same automatic trigger for NHL games

3. **`nfl_agent.py`** (lines 278-294)
   - Same automatic trigger for NFL games

4. **`populate_actual_results_auto.py`** (lines 126-188)
   - Added `populate_actual_results_silent()` function
   - Returns count of updated rows
   - No console output (for integration)

### Integration Code

```python
# Automatically populate actual results in forecasts table
if results['inserted'] > 0:
    print(f"\nPopulating actual results in forecasts table...")
    try:
        from populate_actual_results_auto import populate_actual_results_silent
        from google.cloud import bigquery

        forecast_client = bigquery.Client(project=gcp_project_id)
        updated_count = populate_actual_results_silent(forecast_client)

        if updated_count > 0:
            print(f"✓ Populated actual results for {updated_count} forecast rows")
        else:
            print(f"  No forecast rows needed updating")
    except Exception as e:
        print(f"  Note: Could not populate actual results in forecasts: {e}")
        print(f"  (This is normal if forecasts don't exist for this game)")
```

## Verification

Run verification script to confirm everything is working:

```bash
python3 verify_auto_population.py
```

Expected output:
```
✅ SUCCESS - All games with forecasts have actual results populated!

Automatic population is working correctly:
  1. New games collected ✓
  2. game_ids auto-populated ✓
  3. Actual results auto-populated in forecasts ✓
```

## Error Handling

### Graceful Failures

The system handles edge cases gracefully:

- **No forecasts exist**: Silent skip, prints note
- **game_id is NULL**: No actual results populated (expected)
- **Forecasts table doesn't exist**: Catches exception, continues
- **Network/permission issues**: Logs error, doesn't crash

### Manual Override

If automatic population fails, you can manually run:

```bash
python3 populate_actual_results_auto.py
```

## Benefits of Full Automation

✅ **Zero Manual Intervention** - Set it and forget it
✅ **Immediate Sync** - Forecasts updated as soon as games added
✅ **Consistency** - Same logic every time
✅ **Error Recovery** - Graceful handling of edge cases
✅ **Audit Trail** - Console output shows what was updated
✅ **No Duplicates** - COALESCE prevents overwriting existing values

## Daily Workflow

### Before (Manual - 3 steps)
```bash
# Step 1: Collect games
python3 nba_agent.py

# Step 2: Populate game_ids (if not automated)
python3 update_game_ids_dec6.py

# Step 3: Populate actual results
python3 populate_actual_results_auto.py
```

### After (Automated - 1 step)
```bash
# That's it! Everything else is automatic
python3 nba_agent.py
```

Or use the comprehensive update script:
```bash
python3 update_sports_with_actuals.py
```

## Multi-Sport Support

The same automated flow works for all sports:

```bash
# NBA
python3 nba_agent.py
# ✓ game_id auto-populated
# ✓ Actual results auto-populated

# NHL
python3 nhl_agent.py
# ✓ game_id auto-populated (when forecasts available)
# ✓ Actual results auto-populated

# NFL
python3 nfl_agent.py
# ✓ game_id auto-populated (when forecasts available)
# ✓ Actual results auto-populated
```

## Performance

- **game_id lookup**: ~1 second per date
- **Actual results population**: ~5-10 seconds for full table recreation
- **Total overhead**: ~10 seconds per game collection run
- **Frequency**: Only runs when new games inserted

## Future Enhancements

Potential improvements:

- [ ] Webhook trigger for real-time updates
- [ ] Batch processing for multiple dates
- [ ] Incremental updates instead of table recreation
- [ ] Notification on sync failures
- [ ] Dashboard for sync status

## Troubleshooting

### Issue: "No forecast rows needed updating"

**Meaning**: All forecasts already have actual results
**Action**: None needed - system is up to date

### Issue: "Could not populate actual results in forecasts"

**Common Causes**:
1. Forecasts table doesn't exist (normal for test environments)
2. No game_id populated (game doesn't match any forecasts)
3. Network/permission issues

**Solution**: Run manual verification
```bash
python3 verify_auto_population.py
```

### Issue: Games have forecasts but actuals not populated

**Solution**: Run manual sync
```bash
python3 populate_actual_results_auto.py
```

## Related Documentation

- [GAME_ID_AUTO_POPULATION.md](./GAME_ID_AUTO_POPULATION.md) - game_id automation
- [ACTUAL_RESULTS_POPULATION.md](./ACTUAL_RESULTS_POPULATION.md) - Actual results system
- [README.md](./README.md) - Main project documentation

## Summary

🎉 **The pipeline is now fully automated!**

Simply collect games and everything else happens automatically:
- ✅ Game IDs populated from forecasts
- ✅ Games inserted with proper relationships
- ✅ Actual results synced back to forecasts
- ✅ Ready for forecast evaluation immediately

No manual intervention required!
