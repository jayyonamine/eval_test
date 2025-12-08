# Multi-Sport Game Data Collection Guide

## Overview

This package now supports collecting game data for three major sports:
- **NBA** (Basketball)
- **NHL** (Hockey)
- **NFL** (Football)

Each sport has its own collector skill with sport-specific requirements and team information.

## Available Skills

### 1. NBA Game Collector
- **Skill File:** `nba_game_collector_skill.md`
- **Teams:** 30 NBA teams
- **Season:** October - April
- **Game Frequency:** Daily during season (10-15 games/night)
- **Typical Scores:** 95-130 points per team

### 2. NHL Game Collector
- **Skill File:** `nhl_game_collector_skill.md`
- **Teams:** 32 NHL teams
- **Season:** October - April
- **Game Frequency:** Daily during season (5-15 games/night)
- **Typical Scores:** 0-7 goals per team
- **Special Notes:** Includes overtime/shootout results

### 3. NFL Game Collector
- **Skill File:** `nfl_game_collector_skill.md`
- **Teams:** 32 NFL teams
- **Season:** September - January
- **Game Frequency:** Weekly schedule (13-16 games/week)
  - Thursday: 1 game
  - Sunday: 10-14 games
  - Monday: 1-2 games
  - Most days have NO games
- **Typical Scores:** 10-40 points per team

## Data Structure

All sports use the same consistent data structure:

```json
{
  "game_date": "YYYY-MM-DD",
  "home_team": "Full Team Name",
  "away_team": "Full Team Name",
  "home_score": 0,
  "away_score": 0,
  "points_total": 0,
  "location": "Arena/Stadium Name, City, State",
  "game_status": "Final"
}
```

## Using with Bedrock

### For NBA Games:
```python
agent = NBAGameCollectionAgent(
    aws_region=aws_region,
    skill_path="nba_game_collector_skill.md",
    aws_access_key=aws_access_key,
    aws_secret_key=aws_secret_key,
    model_id=model_id
)
games = agent.collect_games("2025-12-02")
```

### For NHL Games:
```python
agent = NHLGameCollectionAgent(
    aws_region=aws_region,
    skill_path="nhl_game_collector_skill.md",
    aws_access_key=aws_access_key,
    aws_secret_key=aws_secret_key,
    model_id=model_id
)
games = agent.collect_games("2025-12-02")
```

### For NFL Games:
```python
agent = NFLGameCollectionAgent(
    aws_region=aws_region,
    skill_path="nfl_game_collector_skill.md",
    aws_access_key=aws_access_key,
    aws_secret_key=aws_secret_key,
    model_id=model_id
)
games = agent.collect_games("2025-12-01")  # Sunday
```

## BigQuery Table Structure

### Recommended Approach: Separate Tables per Sport

```
tenki-476718.sports_data.nba_games
tenki-476718.sports_data.nhl_games
tenki-476718.sports_data.nfl_games
```

### Schema (Same for all sports):
```
game_date       DATE        REQUIRED
home_team       STRING      REQUIRED
away_team       STRING      REQUIRED
home_score      INTEGER     REQUIRED
away_score      INTEGER     REQUIRED
points_total    INTEGER     REQUIRED
location        STRING      REQUIRED
inserted_at     TIMESTAMP   REQUIRED
```

## Sport-Specific Considerations

### NBA
- **Season runs:** October 15 - April 15 (approx)
- **Games per day:** 10-15 during peak season
- **No games:** Christmas is light, All-Star break (mid-Feb)
- **Data collection:** Can run daily updates

### NHL
- **Season runs:** October 10 - April 20 (approx)
- **Games per day:** 5-15 during peak season
- **No games:** All-Star break (late Jan/early Feb)
- **Overtime:** Score includes OT/SO results
- **Data collection:** Can run daily updates

### NFL
- **Season runs:** Early September - Early January
- **Games per week:** 13-16 total
- **Schedule pattern:**
  - Most Thursdays: 1 game
  - Most Sundays: 10-14 games (1pm ET and 4pm ET windows, plus SNF)
  - Most Mondays: 1-2 games
  - Rest of week: NO GAMES
- **Data collection:** Should run on specific days only (Fri, Mon, Tue)

## Example: NFL-Specific Collection Schedule

```python
# NFL games should only be checked on specific days
from datetime import datetime

def should_collect_nfl(date):
    """Determine if NFL games might have occurred"""
    weekday = date.weekday()
    month = date.month

    # NFL season: September through January
    if month < 9 or month > 1:
        return False

    # Games occur Thu (3), Sun (6), Mon (0)
    if weekday in [3, 6, 0]:
        return True

    # Collect on Fri (4) for Thursday games
    # Collect on Tue (1) for Monday games
    if weekday in [4, 1]:
        return True

    return False
```

## Accuracy Requirements (ALL SPORTS)

**CRITICAL for all sports:**
1. ✅ ONLY collect data for games that have been completed
2. ✅ NEVER generate, estimate, or predict future games
3. ✅ Verify date is in the past before collection
4. ✅ Return empty array `[]` for dates with no games
5. ✅ All scores must show "Final" status
6. ✅ Validate all team names against official rosters
7. ✅ Include `points_total` field (sum of both scores)

## Migration Example: Adding NHL to Your System

```bash
# 1. Create NHL dataset and table
bq mk --dataset tenki-476718:nhl_data
bq mk --table tenki-476718:nhl_data.game_results \
    game_date:DATE,home_team:STRING,away_team:STRING,\
    home_score:INTEGER,away_score:INTEGER,points_total:INTEGER,\
    location:STRING,inserted_at:TIMESTAMP

# 2. Modify nba_agent.py for NHL (or create nhl_agent.py)
# Change skill_path to point to nhl_game_collector_skill.md

# 3. Run collection for NHL season
python3 generate_game_data.py --sport nhl \
    --start-date 2025-10-10 --end-date 2025-12-02 \
    --save-to-bigquery --seed 2025

# 4. Set up update script for daily NHL updates
python3 update_games.py --sport nhl
```

## Future Enhancements

Potential additions to support more sports:
- MLB (Baseball) - 162 games per team/season
- MLS (Soccer) - March through October
- WNBA (Women's Basketball) - May through September
- International soccer leagues
- College sports (NCAA)

## Key Differences Summary

| Sport | Teams | Games/Week | Season Length | Typical Score Range | Update Frequency |
|-------|-------|------------|---------------|---------------------|------------------|
| NBA   | 30    | 100-150    | 6 months      | 190-260 total       | Daily            |
| NHL   | 32    | 50-100     | 6 months      | 4-12 total          | Daily            |
| NFL   | 32    | 13-16      | 4 months      | 20-70 total         | 3x per week      |

## Support and Documentation

- NBA Implementation: See existing codebase
- NHL/NFL Implementation: Follow NBA pattern with sport-specific skill files
- Questions: Refer to skill .md files for detailed team lists and requirements

---

**Generated:** 2025-12-03
**Version:** 1.0
