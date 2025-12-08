# Automatic Game ID Population

## Overview

The system now automatically populates `game_id` fields for all new games as they are added to BigQuery tables. Game IDs are fetched from the `forecasts_mike.relational_forecasts` table by matching on game date and team names.

## How It Works

### Architecture

```
┌─────────────────┐
│  NBA/NHL/NFL    │
│     Agent       │
│  (Collects      │
│   Game Data)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────────┐
│   BigQuery      │────▶ │  GameIdLookup        │
│   Writer        │      │  Utility             │
│                 │      │                      │
│  - Validates    │      │  - Queries forecasts │
│  - Looks up IDs │◀────│  - Matches games     │
│  - Inserts      │      │  - Returns game_ids  │
└────────┬────────┘      └──────────────────────┘
         │
         ▼
┌─────────────────┐
│   BigQuery      │
│   game_results  │
│   (WITH         │
│    game_id)     │
└─────────────────┘
```

### Process Flow

1. **Agent collects games** - NBA/NHL/NFL agents fetch game data from APIs
2. **Writer validates data** - BigQuery writer validates required fields
3. **Lookup game_ids** - Writer queries forecasts table to match games
4. **Insert with IDs** - Games are inserted into BigQuery WITH game_ids

### Matching Logic

Games are matched using:
- **Game Date** - Exact match on date
- **Away Team** - Standardized team name (handles "LA Clippers" ↔ "Los Angeles Clippers")
- **Home Team** - Standardized team name

When a match is found in the forecasts table, the `game_id` is automatically added to the game data before insertion.

## Files Modified

### New Files Created

1. **`game_id_lookup.py`** - Utility module for game_id lookups
   - `GameIdLookup` class - Main lookup functionality
   - `add_game_ids()` - Convenience function
   - Handles team name standardization
   - Supports NBA, NHL, NFL (currently only NBA has forecasts)

### Updated Files

2. **`bigquery_writer.py`** - BigQuery writer with automatic game_id lookup
   - Added `game_id` to table schema (NULLABLE STRING)
   - Integrated `GameIdLookup` utility
   - Added `sport` parameter to `__init__`
   - Automatically looks up game_ids before insertion

3. **`nba_agent.py`** - NBA game collection agent
   - Added `sport="nba"` parameter when initializing writer

4. **`nhl_agent.py`** - NHL game collection agent
   - Added `sport="nhl"` parameter when initializing writer

5. **`nfl_agent.py`** - NFL game collection agent
   - Added `sport="nfl"` parameter when initializing writer

## Usage

### Automatic Population (Default)

No code changes needed! The system automatically populates game_ids when you use the existing collection scripts:

```bash
# NBA games - game_ids automatically populated
python3 nba_agent.py

# NHL games - game_ids automatically populated (when forecasts available)
python3 nhl_agent.py

# NFL games - game_ids automatically populated (when forecasts available)
python3 nfl_agent.py
```

### Programmatic Usage

```python
from bigquery_writer import NBAGameBigQueryWriter

# Initialize writer with sport parameter
writer = NBAGameBigQueryWriter(
    project_id="your-project",
    dataset_id="nba_data",
    table_id="game_results",
    sport="nba"  # Enables automatic game_id lookup
)

# Insert games - game_ids automatically added
games_data = [...]  # Your game data
writer.insert_games(games_data)
```

### Manual Game ID Lookup

```python
from game_id_lookup import add_game_ids

# Add game_ids to a list of games
games_data = [
    {
        "game_date": "2025-12-06",
        "away_team": "Lakers",
        "home_team": "Celtics",
        ...
    }
]

# Automatically adds game_id field to each game
updated_games = add_game_ids(games_data, sport="nba")
```

## Testing

Run the integration test to verify everything works:

```bash
python3 test_game_id_integration.py
```

Expected output:
```
✅ TEST 1 PASSED - Game ID Lookup Utility
✅ TEST 2 PASSED - BigQuery Writer Integration
🎉 ALL TESTS PASSED!
```

## Database Schema

### Before (Old Schema)
```sql
CREATE TABLE game_results (
    game_date DATE,
    home_team STRING,
    away_team STRING,
    home_score INTEGER,
    away_score INTEGER,
    points_total INTEGER,
    location STRING,
    inserted_at TIMESTAMP
);
```

### After (New Schema)
```sql
CREATE TABLE game_results (
    game_date DATE,
    home_team STRING,
    away_team STRING,
    home_score INTEGER,
    away_score INTEGER,
    points_total INTEGER,
    location STRING,
    inserted_at TIMESTAMP,
    game_id STRING  -- ⬅️ NEW FIELD (automatically populated)
);
```

## Benefits

✅ **Automatic** - No manual intervention needed
✅ **Consistent** - All new games get game_ids when forecasts available
✅ **Backwards Compatible** - Existing games without game_ids remain valid
✅ **JOIN Ready** - Can immediately join with forecasts table
✅ **Zero Configuration** - Works out of the box

## Example Output

When collecting games, you'll see:

```
Starting NBA game collection for 2025-12-07...
Fetching NBA scores from ESPN API for 2025-12-07
Successfully collected 7 games for 2025-12-07

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
```

## Forecast Availability

Current forecast coverage (as of Dec 7, 2025):
- **NBA**: Dec 5-7 (26 games)
- **NHL**: Not yet available
- **NFL**: Not yet available

When forecasts are not available for a date, games are inserted with `game_id = NULL`.

## Future Enhancements

- Expand forecasts table to include NHL and NFL games
- Add game_id backfill for historical games
- Implement game_id generation for games without forecasts

## Support

For issues or questions:
1. Check integration tests: `python3 test_game_id_integration.py`
2. Review logs for "Game ID Lookup Results"
3. Verify forecasts table has data for target date
