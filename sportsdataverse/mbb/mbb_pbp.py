from typing import Dict
import pandas as pd
import polars as pl
import numpy as np
import os
import json
import re
from typing import List, Callable, Iterator, Union, Optional, Dict
from sportsdataverse.dl_utils import download, flatten_json_iterative, key_check

def espn_mbb_pbp(game_id: int, raw = False, **kwargs) -> Dict:
    """espn_mbb_pbp() - Pull the game by id. Data from API endpoints: `mens-college-basketball/playbyplay`, `mens-college-basketball/summary`

    Args:
        game_id (int): Unique game_id, can be obtained from mbb_schedule().
        raw (bool): If True, returns the raw json from the API endpoint. If False, returns a cleaned dictionary of datasets.

    Returns:
        Dict: Dictionary of game data with keys: "gameId", "plays", "winprobability", "boxscore", "header", "broadcasts",
        "videos", "playByPlaySource", "standings", "leaders", "timeouts", "pickcenter", "againstTheSpread", "odds", "predictor",
        "espnWP", "gameInfo", "season"

    Example:
        `mbb_df = sportsdataverse.mbb.espn_mbb_pbp(game_id=401265031)`
    """
    # play by play
    pbp_txt = {'timeouts': {}}
    # summary endpoint for pickcenter array
    summary_url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={game_id}"
    summary_resp = download(summary_url, **kwargs)
    summary = summary_resp.json()
    incoming_keys_expected = [
        'boxscore', 'format', 'gameInfo', 'leaders', 'broadcasts',
        'predictor', 'pickcenter', 'againstTheSpread', 'odds', 'winprobability',
        'header', 'plays', 'article', 'videos', 'standings',
        'teamInfo', 'espnWP', 'season', 'timeouts'
    ]
    dict_keys_expected = [
        'plays', 'videos', 'broadcasts', 'pickcenter', 'againstTheSpread',
        'odds', 'winprobability', 'teamInfo', 'espnWP', 'leaders'
    ]
    array_keys_expected = [
        'boxscore','format', 'gameInfo',
        'predictor', 'article', 'header', 'season', 'standings'
    ]
    if raw == True:
        # reorder keys in raw format, appending empty keys which are defined later to the end
        pbp_json = {}
        for k in incoming_keys_expected:
            if k in summary.keys():
                pbp_json[k] = summary[k]
            else:
                pbp_json[k] = {} if k in dict_keys_expected else []
        return pbp_json

    for k in incoming_keys_expected:
        if k in summary.keys():
            pbp_txt[k] = summary[k]
        else:
            pbp_txt[k] = {} if k in dict_keys_expected else []

    for k in ['news','shop']:
        pbp_txt.pop(f'{k}', None)

    return helper_mbb_pbp(game_id, pbp_txt)

def mbb_pbp_disk(game_id, path_to_json):
    with open(os.path.join(path_to_json, f"{game_id}.json")) as json_file:
        pbp_txt = json.load(json_file)
    return pbp_txt

def helper_mbb_pbp(game_id, pbp_txt):
    gameSpread, overUnder, homeFavorite, gameSpreadAvailable = helper_mbb_pickcenter(pbp_txt)
    pbp_txt, gameSpread, overUnder, homeFavorite, gameSpreadAvailable, \
        homeTeamId, homeTeamMascot, homeTeamName,\
        homeTeamAbbrev, homeTeamNameAlt,\
        awayTeamId, awayTeamMascot, awayTeamName,\
        awayTeamAbbrev, awayTeamNameAlt = helper_mbb_game_data(pbp_txt, gameSpread, overUnder, homeFavorite, gameSpreadAvailable)

    if "plays" in pbp_txt.keys() and pbp_txt.get('header').get('competitions')[0].get('playByPlaySource') != 'none':
        pbp_txt = helper_mbb_pbp_features(game_id, pbp_txt, gameSpread, homeFavorite,
                                gameSpreadAvailable, homeTeamId, awayTeamId,
                                homeTeamMascot, awayTeamMascot, homeTeamName,
                                awayTeamName, homeTeamAbbrev, awayTeamAbbrev,
                                homeTeamNameAlt, awayTeamNameAlt)
    else:
        pbp_txt['plays'] = pl.DataFrame()
        pbp_txt['timeouts'] = {
            homeTeamId: {"1": [], "2": []},
            awayTeamId: {"1": [], "2": []},
        }
    # pbp_txt['plays'] = pbp_txt['plays'].replace({np.nan: None})
    return {
        "gameId": int(game_id),
        "plays": pbp_txt['plays'].to_dicts(),
        "winprobability": np.array(pbp_txt['winprobability']).tolist(),
        "boxscore": pbp_txt['boxscore'],
        "header": pbp_txt['header'],
        "format": pbp_txt['format'],
        "broadcasts": np.array(pbp_txt['broadcasts']).tolist(),
        "videos": np.array(pbp_txt['videos']).tolist(),
        "playByPlaySource": pbp_txt['playByPlaySource'],
        "standings": pbp_txt['standings'],
        "article": pbp_txt['article'],
        "leaders": np.array(pbp_txt['leaders']).tolist(),
        "timeouts": pbp_txt['timeouts'],
        "pickcenter": np.array(pbp_txt['pickcenter']).tolist(),
        "againstTheSpread": np.array(pbp_txt['againstTheSpread']).tolist(),
        "odds": np.array(pbp_txt['odds']).tolist(),
        "predictor": pbp_txt['predictor'],
        "espnWP": np.array(pbp_txt['espnWP']).tolist(),
        "gameInfo": pbp_txt['gameInfo'],
        "teamInfo": np.array(pbp_txt['teamInfo']).tolist(),
        "season": np.array(pbp_txt['season']).tolist(),
    }

def helper_mbb_game_data(pbp_txt, gameSpread, overUnder, homeFavorite, gameSpreadAvailable):
    pbp_txt['timeouts'] = {}
    pbp_txt['teamInfo'] = pbp_txt['header']['competitions'][0]
    pbp_txt['season'] = pbp_txt['header']['season']
    pbp_txt['playByPlaySource'] = pbp_txt['header']['competitions'][0]['playByPlaySource']
    pbp_txt['boxscoreSource'] = pbp_txt['header']['competitions'][0]['boxscoreSource']
    pbp_txt['gameSpreadAvailable'] = gameSpreadAvailable
    pbp_txt['gameSpread'] = gameSpread
    pbp_txt["homeFavorite"] = homeFavorite
    pbp_txt["homeTeamSpread"] = np.where(
        homeFavorite == True, abs(gameSpread), -1 * abs(gameSpread)
    )
    pbp_txt["overUnder"] = overUnder
    # Home and Away identification variables
    if pbp_txt['header']['competitions'][0]['competitors'][0]['homeAway']=='home':
        pbp_txt['header']['competitions'][0]['home'] = pbp_txt['header']['competitions'][0]['competitors'][0]['team']
        homeTeamId = int(pbp_txt['header']['competitions'][0]['competitors'][0]['team']['id'])
        homeTeamMascot = str(pbp_txt['header']['competitions'][0]['competitors'][0]['team']['name'])
        homeTeamName = str(pbp_txt['header']['competitions'][0]['competitors'][0]['team']['location'])
        homeTeamAbbrev = str(pbp_txt['header']['competitions'][0]['competitors'][0]['team']['abbreviation'])
        homeTeamNameAlt = re.sub("Stat(.+)", "St", homeTeamName)
        pbp_txt['header']['competitions'][0]['away'] = pbp_txt['header']['competitions'][0]['competitors'][1]['team']
        awayTeamId = int(pbp_txt['header']['competitions'][0]['competitors'][1]['team']['id'])
        awayTeamMascot = str(pbp_txt['header']['competitions'][0]['competitors'][1]['team']['name'])
        awayTeamName = str(pbp_txt['header']['competitions'][0]['competitors'][1]['team']['location'])
        awayTeamAbbrev = str(pbp_txt['header']['competitions'][0]['competitors'][1]['team']['abbreviation'])
        awayTeamNameAlt = re.sub("Stat(.+)", "St", awayTeamName)
    else:
        pbp_txt['header']['competitions'][0]['away'] = pbp_txt['header']['competitions'][0]['competitors'][0]['team']
        awayTeamId = int(pbp_txt['header']['competitions'][0]['competitors'][0]['team']['id'])
        awayTeamMascot = str(pbp_txt['header']['competitions'][0]['competitors'][0]['team']['name'])
        awayTeamName = str(pbp_txt['header']['competitions'][0]['competitors'][0]['team']['location'])
        awayTeamAbbrev = str(pbp_txt['header']['competitions'][0]['competitors'][0]['team']['abbreviation'])
        awayTeamNameAlt = re.sub("Stat(.+)", "St", awayTeamName)
        pbp_txt['header']['competitions'][0]['home'] = pbp_txt['header']['competitions'][0]['competitors'][1]['team']
        homeTeamId = int(pbp_txt['header']['competitions'][0]['competitors'][1]['team']['id'])
        homeTeamMascot = str(pbp_txt['header']['competitions'][0]['competitors'][1]['team']['name'])
        homeTeamName = str(pbp_txt['header']['competitions'][0]['competitors'][1]['team']['location'])
        homeTeamAbbrev = str(pbp_txt['header']['competitions'][0]['competitors'][1]['team']['abbreviation'])
        homeTeamNameAlt = re.sub("Stat(.+)", "St", homeTeamName)
    return pbp_txt, gameSpread, overUnder, homeFavorite, gameSpreadAvailable, homeTeamId,\
            homeTeamMascot,homeTeamName,homeTeamAbbrev,homeTeamNameAlt,\
            awayTeamId,awayTeamMascot,awayTeamName,awayTeamAbbrev,awayTeamNameAlt

def helper_mbb_pickcenter(pbp_txt):
    # Spread definition
    if len(pbp_txt.get("pickcenter",[])) > 1:
        homeFavorite = pbp_txt.get("pickcenter",{})[0].get("homeTeamOdds",{}).get("favorite","")
        if "spread" in pbp_txt.get("pickcenter",{})[1].keys():
            gameSpread = pbp_txt.get("pickcenter",{})[1].get("spread","")
            overUnder = pbp_txt.get("pickcenter",{})[1].get("overUnder","")
        else:
            gameSpread = pbp_txt.get("pickcenter",{})[0].get("spread","")
            overUnder = pbp_txt.get("pickcenter",{})[0].get("overUnder","")
        gameSpreadAvailable = True
            # self.logger.info(f"Spread: {gameSpread}, home Favorite: {homeFavorite}, ou: {overUnder}")
    else:
        gameSpread = 2.5
        overUnder = 140.5
        homeFavorite = True
        gameSpreadAvailable = False
    return gameSpread, overUnder, homeFavorite, gameSpreadAvailable

def helper_mbb_pbp_features(game_id, pbp_txt, gameSpread, homeFavorite, gameSpreadAvailable, homeTeamId, awayTeamId, homeTeamMascot, awayTeamMascot, homeTeamName, awayTeamName, homeTeamAbbrev, awayTeamAbbrev, homeTeamNameAlt, awayTeamNameAlt):
    pbp_txt['plays_mod'] = []
    for play in pbp_txt['plays']:
        p = flatten_json_iterative(play)
        pbp_txt['plays_mod'].append(p)
    pbp_txt['plays'] = pl.from_pandas(pd.json_normalize(pbp_txt,'plays_mod'))
    pbp_txt['plays'] = pbp_txt['plays'].with_columns(
        game_id = pl.lit(game_id).cast(pl.Int32),
        id = (pl.col('id').cast(pl.Int64)),
        season = pl.lit(pbp_txt['header']['season']['year']),
        seasonType = pl.lit(pbp_txt['header']['season']['type']),
        homeTeamId = pl.lit(homeTeamId),
        homeTeamName = pl.lit(homeTeamName),
        homeTeamMascot = pl.lit(homeTeamMascot),
        homeTeamAbbrev = pl.lit(homeTeamAbbrev),
        homeTeamNameAlt = pl.lit(homeTeamNameAlt),
        awayTeamId = pl.lit(awayTeamId),
        awayTeamName = pl.lit(awayTeamName),
        awayTeamMascot = pl.lit(awayTeamMascot),
        awayTeamAbbrev = pl.lit(awayTeamAbbrev),
        awayTeamNameAlt = pl.lit(awayTeamNameAlt),
        gameSpread = pl.lit(gameSpread).abs(),
        homeFavorite = pl.lit(homeFavorite),
        gameSpreadAvailable = pl.lit(gameSpreadAvailable),
    ).with_columns(
        homeTeamSpread = pl.when(pl.col('homeFavorite') == True)
            .then(pl.col('gameSpread'))
            .otherwise(-1*pl.col('gameSpread')),


    ).with_columns(
        pl.col("period.number").cast(pl.Int32).alias("period.number"),
        pl.col("period.number").cast(pl.Int32).alias("half"),
        pl.col("clock.displayValue").alias("time"),
        pl.col("clock.displayValue").str.split(':').list.to_struct(n_field_strategy="max_width").alias("clock.mm")
    ).with_columns(
        pl.col("clock.mm").struct.rename_fields(["clock.minutes", "clock.seconds"])
    ).unnest(
        "clock.mm"
    ).with_columns(
        pl.col("clock.minutes").cast(pl.Int32),
        pl.col("clock.seconds").cast(pl.Int32),
        pl.when((pl.col("type.text") == "ShortTimeOut")
            .and_(
                pl.col("text").str.to_lowercase().str.contains(str(homeTeamAbbrev).lower())
                .or_(
                    pl.col("text").str.to_lowercase().str.contains(str(homeTeamAbbrev).lower()),
                    pl.col("text").str.to_lowercase().str.contains(str(homeTeamName).lower()),
                    pl.col("text").str.to_lowercase().str.contains(str(homeTeamMascot).lower()),
                    pl.col("text").str.to_lowercase().str.contains(str(homeTeamNameAlt).lower())
                )
            ))
        .then(True)
        .otherwise(False)
        .alias("homeTimeoutCalled"),
        pl.when((pl.col("type.text") == "ShortTimeOut")
            .and_(
                pl.col("text").str.to_lowercase().str.contains(str(awayTeamAbbrev).lower())
                .or_(
                    pl.col("text").str.to_lowercase().str.contains(str(awayTeamAbbrev).lower()),
                    pl.col("text").str.to_lowercase().str.contains(str(awayTeamName).lower()),
                    pl.col("text").str.to_lowercase().str.contains(str(awayTeamMascot).lower()),
                    pl.col("text").str.to_lowercase().str.contains(str(awayTeamNameAlt).lower())
                )
            ))
        .then(True)
        .otherwise(False)
        .alias("awayTimeoutCalled"),
    ).with_columns(
        lag_period = pl.col("period.number").shift(1),
        lead_period = pl.col("period.number").shift(-1),
        lag_half = pl.col("half").shift(1),
        lead_half = pl.col("half").shift(-1),

    ).with_columns(

        (60 * pl.col("clock.minutes") + pl.col("clock.seconds")).alias("start.period_seconds_remaining"),
        pl.when(pl.col("period.number") == 1)
            .then(1200 + 60 * pl.col("clock.minutes") + pl.col("clock.seconds"))
            .otherwise(60 * pl.col("clock.minutes") + pl.col("clock.seconds"))
            .alias("start.game_seconds_remaining"),
    ).with_columns(
        pl.col("start.period_seconds_remaining").shift(-1).alias("end.period_seconds_remaining"),
        pl.col("start.game_seconds_remaining").shift(-1).alias("end.game_seconds_remaining"),
    )
    pbp_txt["timeouts"] = {
        homeTeamId: {"1": [], "2": []},
        awayTeamId: {"1": [], "2": []},
    }
    pbp_txt["timeouts"][homeTeamId]["1"] = (
        pbp_txt["plays"]
        .filter(
            (pl.col("homeTimeoutCalled") == True)
            .and_(pl.col("period.number") <= 1)
        )
        .get_column("id")
        .to_list()
    )
    pbp_txt["timeouts"][homeTeamId]["2"] = (
        pbp_txt["plays"]
        .filter(
            (pl.col("homeTimeoutCalled") == True)
            .and_(pl.col("period.number") > 1)
        )
        .get_column("id")
        .to_list()
    )
    pbp_txt["timeouts"][awayTeamId]["1"] = (
        pbp_txt["plays"]
        .filter(
            (pl.col("awayTimeoutCalled") == True)
            .and_(pl.col("period.number") <= 1)
        )
        .get_column("id")
        .to_list()
    )
    pbp_txt["timeouts"][awayTeamId]["2"] = (
        pbp_txt["plays"]
        .filter(
            (pl.col("awayTimeoutCalled") == True)
            .and_(pl.col("period.number") > 1)
        )
        .get_column("id")
        .to_list()
    )


    pbp_txt["plays"] = pbp_txt["plays"].with_row_count("game_play_number", 1)

    pbp_txt["plays"] = pbp_txt["plays"].with_columns(
        pl.when((pl.col("game_play_number") == 1)
                .or_((pl.col("lag_period") == 1)
                     .and_(pl.col("period.number") == 2)))
            .then(1200)
            .when((pl.col("lag_period") == 2)
                    .and_(pl.col("period.number") == 3))
            .then(300)
            .otherwise(pl.col("end.period_seconds_remaining"))
            .alias("end.period_seconds_remaining"),
        pl.when((pl.col("game_play_number") == 1))
            .then(2400)
            .when((pl.col("lag_period") == 1)
                     .and_(pl.col("period.number") == 2))
            .then(1200)
            .when((pl.col("lag_period") == (pl.col("period.number") - 1))
                    .and_(pl.col("period.number") >= 3))
            .then(300)
            .otherwise(pl.col("end.game_seconds_remaining"))
            .alias("end.game_seconds_remaining"),
    )

    return pbp_txt

