# sportsdataverse.wnba package

## Submodules

## sportsdataverse.wnba.wnba_loaders module


### sportsdataverse.wnba.wnba_loaders.load_wnba_pbp(seasons: List[int])
Load WNBA play by play data going back to 2002

Example:

    wnba_df = sportsdataverse.wnba.load_wnba_pbp(seasons=range(2002,2022))

Args:

    seasons (list): Used to define different seasons. 2002 is the earliest available season.

Returns:

    pd.DataFrame: Pandas dataframe containing the
    play-by-plays available for the requested seasons.

Raises:

    ValueError: If season is less than 2002.


### sportsdataverse.wnba.wnba_loaders.load_wnba_player_boxscore(seasons: List[int])
Load WNBA player boxscore data

Example:

    wnba_df = sportsdataverse.wnba.load_wnba_player_boxscore(seasons=range(2002,2022))

Args:

    seasons (list): Used to define different seasons. 2002 is the earliest available season.

Returns:

    pd.DataFrame: Pandas dataframe containing the
    player boxscores available for the requested seasons.

Raises:

    ValueError: If season is less than 2002.


### sportsdataverse.wnba.wnba_loaders.load_wnba_schedule(seasons: List[int])
Load WNBA schedule data

Example:

    wnba_df = sportsdataverse.wnba.load_wnba_schedule(seasons=range(2002,2022))

Args:

    seasons (list): Used to define different seasons. 2002 is the earliest available season.

Returns:

    pd.DataFrame: Pandas dataframe containing the
    schedule for  the requested seasons.

Raises:

    ValueError: If season is less than 2002.


### sportsdataverse.wnba.wnba_loaders.load_wnba_team_boxscore(seasons: List[int])
Load WNBA team boxscore data

Example:

    wnba_df = sportsdataverse.wnba.load_wnba_team_boxscore(seasons=range(2002,2022))

Args:

    seasons (list): Used to define different seasons. 2002 is the earliest available season.

Returns:

    pd.DataFrame: Pandas dataframe containing the
    team boxscores available for the requested seasons.

Raises:

    ValueError: If season is less than 2002.

## sportsdataverse.wnba.wnba_pbp module


### sportsdataverse.wnba.wnba_pbp.espn_wnba_pbp(game_id: int, raw=False)
espn_wnba_pbp() - Pull the game by id. Data from API endpoints - wnba/playbyplay, wnba/summary

Args:

    game_id (int): Unique game_id, can be obtained from wnba_schedule().

Returns:

    Dict: Dictionary of game data with keys - “gameId”, “plays”, “winprobability”, “boxscore”, “header”,

        “broadcasts”, “videos”, “playByPlaySource”, “standings”, “leaders”, “seasonseries”, “timeouts”,
        “pickcenter”, “againstTheSpread”, “odds”, “predictor”, “espnWP”, “gameInfo”, “season”

Example:

    wnba_df = sportsdataverse.wnba.espn_wnba_pbp(game_id=401370395)


### sportsdataverse.wnba.wnba_pbp.helper_wnba_pbp(game_id, pbp_txt)

### sportsdataverse.wnba.wnba_pbp.helper_wnba_pbp_features(game_id, pbp_txt, gameSpread, homeFavorite, gameSpreadAvailable, homeTeamId, awayTeamId, homeTeamMascot, awayTeamMascot, homeTeamName, awayTeamName, homeTeamAbbrev, awayTeamAbbrev, homeTeamNameAlt, awayTeamNameAlt)

### sportsdataverse.wnba.wnba_pbp.helper_wnba_pickcenter(pbp_txt)

### sportsdataverse.wnba.wnba_pbp.wnba_pbp_disk(game_id, path_to_json)
## sportsdataverse.wnba.wnba_schedule module


### sportsdataverse.wnba.wnba_schedule.espn_wnba_calendar(season=None, ondays=None)
espn_wnba_calendar - look up the WNBA calendar for a given season

Args:

    season (int): Used to define different seasons. 2002 is the earliest available season.
    ondays (boolean): Used to return dates for calendar ondays

Returns:

    pd.DataFrame: Pandas dataframe containing calendar dates for the requested season.

Raises:

    ValueError: If season is less than 2002.


### sportsdataverse.wnba.wnba_schedule.espn_wnba_schedule(dates=None, season_type=None, limit=500)
espn_wnba_schedule - look up the WNBA schedule for a given season

Args:

    dates (int): Used to define different seasons. 2002 is the earliest available season.
    season_type (int): 2 for regular season, 3 for post-season, 4 for off-season.
    limit (int): number of records to return, default: 500.

Returns:

    pd.DataFrame: Pandas dataframe containing schedule dates for the requested season.

## sportsdataverse.wnba.wnba_teams module


### sportsdataverse.wnba.wnba_teams.espn_wnba_teams()
espn_wnba_teams - look up WNBA teams

Returns:

    pd.DataFrame: Pandas dataframe containing teams for the requested league.

## Module contents
