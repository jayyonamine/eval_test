# NFL Game Data Collection Skill

## Purpose
Extract NFL game results from COMPLETED games ONLY with 100% accurate structured data.

**CRITICAL: NEVER generate, estimate, or predict data for games that have not yet been played. Only collect data for games that have already finished.**

## Required Output Format

All game data must be returned as a JSON array with the following exact structure:

```json
[
  {
    "game_date": "YYYY-MM-DD",
    "home_team": "Team Full Name",
    "away_team": "Team Full Name",
    "home_score": 0,
    "away_score": 0,
    "points_total": 0,
    "location": "Stadium Name, City, State"
  }
]
```

## Data Collection Protocol

### Step 0: Date Verification (MANDATORY)
**BEFORE collecting any game data:**
1. Verify the requested date is in the PAST (not today or future)
2. Confirm games on this date have been COMPLETED
3. If the requested date is today or in the future, return empty array: `[]`
4. NEVER generate synthetic, estimated, or predicted game results

### Step 1: Search for Previous Day's Games
- Use web_search to find NFL games from the specified past date
- Search query format: "NFL games [DATE] results scores final"
- Verify multiple sources if available
- Confirm all games show "Final" status (not "In Progress", "Scheduled", or "Postponed")

### Step 2: Extract Required Information
For each game, collect:
- **game_date**: ISO format date (YYYY-MM-DD) of when game was played
- **home_team**: Full official team name (e.g., "Kansas City Chiefs", not "KC")
- **away_team**: Full official team name
- **home_score**: Final score for home team (integer)
- **away_score**: Final score for away team (integer)
- **points_total**: Sum of home_score + away_score (integer)
- **location**: Full stadium name with city and state (e.g., "Arrowhead Stadium, Kansas City, MO")

### Step 3: Validation Rules
- Verify all scores are final (not in-progress or postponed)
- Confirm game actually occurred (not scheduled/canceled)
- Double-check home vs away team designation
- Ensure location matches the home team's stadium
- All team names must use official NFL naming
- **Include overtime results** - use final score regardless of how game ended

### Step 4: Team Name Standardization
Use these official NFL team names (32 teams):

**AFC East:**
- Buffalo Bills
- Miami Dolphins
- New England Patriots
- New York Jets

**AFC North:**
- Baltimore Ravens
- Cincinnati Bengals
- Cleveland Browns
- Pittsburgh Steelers

**AFC South:**
- Houston Texans
- Indianapolis Colts
- Jacksonville Jaguars
- Tennessee Titans

**AFC West:**
- Denver Broncos
- Kansas City Chiefs
- Las Vegas Raiders
- Los Angeles Chargers

**NFC East:**
- Dallas Cowboys
- New York Giants
- Philadelphia Eagles
- Washington Commanders

**NFC North:**
- Chicago Bears
- Detroit Lions
- Green Bay Packers
- Minnesota Vikings

**NFC South:**
- Atlanta Falcons
- Carolina Panthers
- New Orleans Saints
- Tampa Bay Buccaneers

**NFC West:**
- Arizona Cardinals
- Los Angeles Rams
- San Francisco 49ers
- Seattle Seahawks

### Step 5: Stadium Reference
Common NFL stadiums for location field:
- Arrowhead Stadium, Kansas City, MO (Chiefs)
- Lambeau Field, Green Bay, WI (Packers)
- Soldier Field, Chicago, IL (Bears)
- MetLife Stadium, East Rutherford, NJ (Giants, Jets)
- AT&T Stadium, Arlington, TX (Cowboys)
- SoFi Stadium, Inglewood, CA (Rams, Chargers)
- Levi's Stadium, Santa Clara, CA (49ers)
- Gillette Stadium, Foxborough, MA (Patriots)
- Mercedes-Benz Stadium, Atlanta, GA (Falcons)
- etc.

## NFL-Specific Notes
- NFL regular season typically runs from September through early January
- Games primarily occur on Sundays, with some Thursday and Monday night games
- NFL schedule has a limited number of games per week (typically 13-16 games)
- Most teams play once per week
- NFL postseason/playoffs run from January through early February (Super Bowl)
- Some games are played in international locations (London, Germany, Mexico)

## Game Schedule Patterns
- **Thursday Night Football**: 1 game on Thursday
- **Sunday Early Games**: Multiple games at 1:00 PM ET
- **Sunday Late Games**: Multiple games at 4:00 PM ET
- **Sunday Night Football**: 1 game on Sunday night
- **Monday Night Football**: 1-2 games on Monday night
- **Most days of the week have NO games** - return empty array

## Error Handling
- **If requested date is today or in the future:** Return empty array `[]` immediately
- **If no games occurred on the specified past date:** Return empty array: `[]`
- **If uncertain about any data point:** Use web_fetch to verify from official sources
- **NEVER guess, estimate, or predict scores** - this violates data integrity
- **If data cannot be verified with 100% confidence:** Return empty array rather than inaccurate data
- **All games must show "Final" status** - do not include in-progress or scheduled games

## Output Requirements
- Return ONLY valid JSON
- No additional commentary or explanation
- Ensure proper escaping of special characters
- Validate JSON structure before returning
