# NBA Game Data Collection Skill

## Purpose
Extract NBA game results from COMPLETED games ONLY with 100% accurate structured data.

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
    "location": "Arena Name, City, State"
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
- Use web_search to find NBA games from the specified past date
- Search query format: "NBA games [DATE] results scores final"
- Verify multiple sources if available
- Confirm all games show "Final" status (not "In Progress", "Scheduled", or "Postponed")

### Step 2: Extract Required Information
For each game, collect:
- **game_date**: ISO format date (YYYY-MM-DD) of when game was played
- **home_team**: Full official team name (e.g., "Los Angeles Lakers", not "LAL")
- **away_team**: Full official team name
- **home_score**: Final score for home team (integer)
- **away_score**: Final score for away team (integer)
- **location**: Full arena name with city and state (e.g., "Crypto.com Arena, Los Angeles, CA")

### Step 3: Validation Rules
- Verify all scores are final (not in-progress or postponed)
- Confirm game actually occurred (not scheduled/canceled)
- Double-check home vs away team designation
- Ensure location matches the home team's arena
- All team names must use official NBA naming

### Step 4: Team Name Standardization
Use these official NBA team names:
- Atlanta Hawks
- Boston Celtics
- Brooklyn Nets
- Charlotte Hornets
- Chicago Bulls
- Cleveland Cavaliers
- Dallas Mavericks
- Denver Nuggets
- Detroit Pistons
- Golden State Warriors
- Houston Rockets
- Indiana Pacers
- LA Clippers
- Los Angeles Lakers
- Memphis Grizzlies
- Miami Heat
- Milwaukee Bucks
- Minnesota Timberwolves
- New Orleans Pelicans
- New York Knicks
- Oklahoma City Thunder
- Orlando Magic
- Philadelphia 76ers
- Phoenix Suns
- Portland Trail Blazers
- Sacramento Kings
- San Antonio Spurs
- Toronto Raptors
- Utah Jazz
- Washington Wizards

### Step 5: Arena Reference
Common NBA arenas for location field:
- Crypto.com Arena, Los Angeles, CA (Lakers, Clippers)
- Madison Square Garden, New York, NY (Knicks)
- TD Garden, Boston, MA (Celtics)
- United Center, Chicago, IL (Bulls)
- Chase Center, San Francisco, CA (Warriors)
- etc.

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
