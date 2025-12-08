# NHL Game Data Collection Skill

## Purpose
Extract NHL game results from COMPLETED games ONLY with 100% accurate structured data.

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
    "location": "Arena Name, City, State/Province"
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
- Use web_search to find NHL games from the specified past date
- Search query format: "NHL games [DATE] results scores final"
- Verify multiple sources if available
- Confirm all games show "Final" status (not "In Progress", "Scheduled", or "Postponed")

### Step 2: Extract Required Information
For each game, collect:
- **game_date**: ISO format date (YYYY-MM-DD) of when game was played
- **home_team**: Full official team name (e.g., "Los Angeles Kings", not "LAK")
- **away_team**: Full official team name
- **home_score**: Final score for home team (integer)
- **away_score**: Final score for away team (integer)
- **points_total**: Sum of home_score + away_score (integer)
- **location**: Full arena name with city and state/province (e.g., "Crypto.com Arena, Los Angeles, CA")

### Step 3: Validation Rules
- Verify all scores are final (not in-progress or postponed)
- Confirm game actually occurred (not scheduled/canceled)
- Double-check home vs away team designation
- Ensure location matches the home team's arena
- All team names must use official NHL naming
- **Include overtime/shootout results** - use final score regardless of how game ended

### Step 4: Team Name Standardization
Use these official NHL team names (32 teams):

**Eastern Conference - Atlantic Division:**
- Boston Bruins
- Buffalo Sabres
- Detroit Red Wings
- Florida Panthers
- Montreal Canadiens
- Ottawa Senators
- Tampa Bay Lightning
- Toronto Maple Leafs

**Eastern Conference - Metropolitan Division:**
- Carolina Hurricanes
- Columbus Blue Jackets
- New Jersey Devils
- New York Islanders
- New York Rangers
- Philadelphia Flyers
- Pittsburgh Penguins
- Washington Capitals

**Western Conference - Central Division:**
- Chicago Blackhawks
- Colorado Avalanche
- Dallas Stars
- Minnesota Wild
- Nashville Predators
- St. Louis Blues
- Utah Hockey Club
- Winnipeg Jets

**Western Conference - Pacific Division:**
- Anaheim Ducks
- Calgary Flames
- Edmonton Oilers
- Los Angeles Kings
- San Jose Sharks
- Seattle Kraken
- Vancouver Canucks
- Vegas Golden Knights

### Step 5: Arena Reference
Common NHL arenas for location field:
- Scotiabank Arena, Toronto, ON (Maple Leafs)
- Bell Centre, Montreal, QC (Canadiens)
- Madison Square Garden, New York, NY (Rangers)
- TD Garden, Boston, MA (Bruins)
- United Center, Chicago, IL (Blackhawks)
- Rogers Arena, Vancouver, BC (Canucks)
- Crypto.com Arena, Los Angeles, CA (Kings)
- T-Mobile Arena, Las Vegas, NV (Golden Knights)
- Climate Pledge Arena, Seattle, WA (Kraken)
- etc.

## NHL-Specific Notes
- NHL games can end in overtime or shootout - always use the final score
- NHL season typically runs from October through April (regular season)
- Playoffs run from April through June
- Games typically occur daily during season, with fewer on Mondays

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
