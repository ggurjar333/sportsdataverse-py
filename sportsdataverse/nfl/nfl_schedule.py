import datetime

import pandas as pd
import polars as pl

from sportsdataverse.dl_utils import download


def espn_nfl_schedule(
    dates=None, week=None, season_type=None, groups=None, limit=500, return_as_pandas=False, **kwargs
) -> pl.DataFrame:
    """espn_nfl_schedule - look up the NFL schedule for a given season

    Args:
        dates (int): Used to define different seasons. 2002 is the earliest available season.
        week (int): Week of the schedule.
        season_type (int): 2 for regular season, 3 for post-season, 4 for off-season.
        limit (int): number of records to return, default: 500.
        return_as_pandas (bool): If True, returns a pandas dataframe. If False, returns a polars dataframe.

    Returns:
        pl.DataFrame: Polars dataframe containing schedule dates for the requested season. Returns None if no games
    """

    params = {"week": week, "dates": dates, "seasonType": season_type, "limit": limit}

    url = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    resp = download(url=url, params=params, **kwargs)

    ev = pd.DataFrame()
    events_txt = resp.json()
    events = events_txt.get("events")
    if events is None:
        return pd.DataFrame() if return_as_pandas else pl.DataFrame()
    if len(events) == 0:
        return pd.DataFrame() if return_as_pandas else pl.DataFrame()

    for event in events:
        event = scoreboard_event_parsing(event)
        x = pl.from_pandas(pd.json_normalize(event.get("competitions")[0], sep="_"))
        x = x.with_columns(
            game_id=(pl.col("id").cast(pl.Int32)),
            season=(event.get("season").get("year")),
            season_type=(event.get("season").get("type")),
            week=(event.get("week", {}).get("number")),
            home_linescores=pl.when(pl.col("status_type_description") == "Postponed")
            .then(None)
            .otherwise(pl.col("home_linescores")),
            away_linescores=pl.when(pl.col("status_type_description") == "Postponed")
            .then(None)
            .otherwise(pl.col("away_linescores")),
        ).with_columns(
            season=pl.col("season").cast(pl.Int32),
            season_type=pl.col("season_type").cast(pl.Int32),
            week=pl.col("week").cast(pl.Int32),
        )
        x = x[[s.name for s in x if s.null_count() != x.height]]
        ev = pd.concat([ev, x.to_pandas()], axis=0, ignore_index=True)
    ev = pl.from_pandas(ev)
    ev = ev.janitor.clean_names()

    return ev.to_pandas() if return_as_pandas else ev


def scoreboard_event_parsing(event):
    event.get("competitions")[0].get("competitors")[0].get("team").pop("links", None)
    event.get("competitions")[0].get("competitors")[1].get("team").pop("links", None)
    if event.get("competitions")[0].get("competitors")[0].get("homeAway") == "home":
        event = __extract_home_away(event, 0, "home")
        event = __extract_home_away(event, 1, "away")
    else:
        event = __extract_home_away(event, 0, "away")
        event = __extract_home_away(event, 1, "home")
    del_keys = ["geoBroadcasts", "headlines", "series", "situation", "tickets", "odds", "leaders"]
    for k in del_keys:
        event.get("competitions")[0].pop(k, None)
    event.get("competitions")[0]["notes_type"] = (
        event.get("competitions")[0]["notes"][0].get("type") if len(event.get("competitions")[0]["notes"]) > 0 else ""
    )
    event.get("competitions")[0]["notes_headline"] = (
        event.get("competitions")[0]["notes"][0].get("headline").replace('"', "")
        if len(event.get("competitions")[0]["notes"]) > 0
        else ""
    )
    event.get("competitions")[0]["broadcast_market"] = (
        event.get("competitions")[0].get("broadcasts", [])[0].get("market", "")
        if len(event.get("competitions")[0].get("broadcasts")) > 0
        else ""
    )
    event.get("competitions")[0]["broadcast_name"] = (
        event.get("competitions")[0].get("broadcasts", [])[0].get("names", [])[0]
        if len(event.get("competitions")[0].get("broadcasts")) > 0
        else ""
    )
    event.get("competitions")[0].pop("broadcasts", None)
    event.get("competitions")[0].pop("notes", None)
    event.get("competitions")[0].pop("competitors", None)
    return event


def __extract_home_away(event, arg1, arg2):
    event["competitions"][0][arg2] = event.get("competitions")[0].get("competitors")[arg1].get("team")
    event["competitions"][0][arg2]["score"] = event.get("competitions")[0].get("competitors")[arg1].get("score")
    event["competitions"][0][arg2]["winner"] = event.get("competitions")[0].get("competitors")[arg1].get("winner")
    # add winner back to main competitors if does not exist
    event["competitions"][0]["competitors"][arg1]["winner"] = (
        event.get("competitions")[0].get("competitors")[arg1].get("winner", False)
    )
    event["competitions"][0][arg2]["currentRank"] = (
        event.get("competitions")[0].get("competitors")[arg1].get("curatedRank", {}).get("current", 99)
    )
    event["competitions"][0][arg2]["linescores"] = (
        event.get("competitions")[0]
        .get("competitors")[arg1]
        .get("linescores", [{"value": 0}, {"value": 0}, {"value": 0}, {"value": 0}])
    )
    # add linescores back to main competitors if does not exist
    event["competitions"][0]["competitors"][arg1]["linescores"] = (
        event.get("competitions")[0]
        .get("competitors")[arg1]
        .get("linescores", [{"value": 0}, {"value": 0}, {"value": 0}, {"value": 0}])
    )
    event["competitions"][0][arg2]["records"] = (
        event.get("competitions")[0]
        .get("competitors")[arg1]
        .get(
            "records",
            [
                {"abbreviation": "Game", "name": "overall", "summary": "0-0", "type": "total"},
                {"abbreviation": "null", "name": "Home", "summary": "0-0", "type": "home"},
                {"abbreviation": "null", "name": "Road", "summary": "0-0", "type": "road"},
            ],
        )
    )
    return event


def espn_nfl_calendar(season=None, ondays=None, return_as_pandas=False, **kwargs) -> pl.DataFrame:
    """espn_nfl_calendar - look up the NFL calendar for a given season

    Args:
        season (int): Used to define different seasons. 2002 is the earliest available season.
        ondays (boolean): Used to return dates for calendar ondays
        return_as_pandas (bool): If True, returns a pandas dataframe. If False, returns a polars dataframe.

    Returns:
        pl.DataFrame: Polars dataframe containing calendar dates for the requested season.

    Raises:
        ValueError: If `season` is less than 2002.
    """
    if ondays is not None:
        full_schedule = __ondays_nfl_calendar(season, **kwargs)
    else:
        url = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        params = {"dates": season}
        resp = download(url=url, params=params, **kwargs)
        txt = resp.json()
        txt = txt.get("leagues")[0].get("calendar")
        full_schedule = pl.DataFrame()
        for i in range(len(txt)):
            if txt[i].get("entries", None) is not None:
                reg = pd.json_normalize(
                    data=txt[i],
                    record_path="entries",
                    meta=["label", "value", "startDate", "endDate"],
                    meta_prefix="season_type_",
                    record_prefix="week_",
                    errors="ignore",
                    sep="_",
                )
                full_schedule = pl.concat([full_schedule, pl.from_pandas(reg)], how="vertical")
        full_schedule = full_schedule.with_columns(season=season)
        full_schedule = full_schedule.janitor.clean_names()
        full_schedule = full_schedule.rename({"week_value": "week", "season_type_value": "season_type"})
    return full_schedule.to_pandas() if return_as_pandas else full_schedule


def __ondays_nfl_calendar(season, **kwargs):
    url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{season}/types/2/calendar/ondays"
    resp = download(url=url, **kwargs)
    if resp is not None:
        txt = resp.json().get("eventDate").get("dates")
        result = pl.DataFrame(txt, schema=["dates"])
        result = result.with_columns(dateURL=pl.col("dates").str.slice(0, 10))
        result = result.with_columns(
            url="http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=" + pl.col("dateURL")
        )

    return result


def most_recent_nfl_season():
    today = datetime.datetime.now()
    current_year = today.year
    current_month = today.month
    # current_day = today.day
    return current_year if current_month >= 9 else current_year - 1


def get_current_week():
    # Find first Monday of September in current season
    week1_sep = pd.to_datetime([f"{most_recent_nfl_season()}-09-0{num}" for num in range(1, 8)]).to_series()
    monday1_sep = week1_sep[week1_sep.dt.dayofweek == 0]

    # NFL season starts 3 days later
    first_game = monday1_sep
    first_game += pd.Timedelta(days=3)

    # current week number of nfl season is 1 + how many weeks have elapsed since first game
    current_week = int((pd.to_datetime("today") - first_game).dt.days / 7 + 1)

    # hardcoded week bounds because this whole date based thing has assumptions anyway
    current_week = max(current_week, 1)
    return min(current_week, 22)
