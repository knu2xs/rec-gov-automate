import logging
from datetime import datetime
from typing import Optional

import pandas as pd
import pytz
import requests

__all__ = [
    "get_campground_availability_by_month",
    "filter_campsites_to_available_weekends",
    "get_4rivers_permit_availability_by_month",
]


# configure the headers
_headers_dict = {"Content-Type": "application/json", "User-Agent": "Chrome/132.0.0.0"}


def get_campground_availability_by_month(
    campground_id: int,
    start_month: int,
    start_year: Optional[int] = None,
    only_available: Optional[bool] = True,
) -> pd.DataFrame:
    """
    Get availability of campground at a given month.

    Args:
        campground_id: Recreation.gov campground ID.
        start_month: Month being searched.
        start_year: Year being searched. Defaults to the current year.
        only_available: If True, only available sites will be returned.

    Returns:
        Availability of campground at a given year and month as a Pandas data frame.
    """
    # provide default year
    if start_year is None:
        start_year = datetime.now().year

    # create campground url using identifier
    url_api = (
        f"https://www.recreation.gov/api/camps/availability/campground/{campground_id}/month"
        f"?start_date={start_year}-{start_month:02d}-01T00%3A00%3A00.000Z"
    )

    # get campground availability json
    res = requests.get(url_api, headers=_headers_dict)

    # extract the JSON as a dictionary
    res_dict = res.json()

    # from the dict, extract the dictionary of campsites
    campsites = res_dict.get("campsites")

    # create a data frame and switch the columns and headers to be more usable
    df = pd.DataFrame(campsites).transpose()

    # peel off the nested columns
    avail_srs = df.loc[:, "availabilities"]
    quant_srs = df.loc[:, "quantities"]

    # create an availability type data frame by campsite and date
    avail_df = avail_srs.apply(lambda val: val.items()).explode().to_frame()
    avail_df[["dt", "avail_status"]] = avail_df.apply(
        lambda r: r.iloc[0], axis=1, result_type="expand"
    )
    avail_df.drop(columns="availabilities", inplace=True)
    avail_df.set_index("dt", append=True, inplace=True)

    # create an availability quantity data frame by campsite and date as well
    quant_df = quant_srs.apply(lambda val: val.items()).explode().to_frame()
    quant_df[["dt", "avail_quantity"]] = quant_df.apply(
        lambda r: r.iloc[0], axis=1, result_type="expand"
    )
    quant_df.drop(columns="quantities", inplace=True)
    quant_df.set_index("dt", append=True, inplace=True)

    # combine the availability type and quantity data frames
    avail_df = (
        avail_df.join(quant_df, how="outer")
        .reset_index()
        .rename(columns={"level_0": "campsite_id"})
        .set_index("campsite_id")
    )

    # keep columns with useful information for filtering
    keep_cols = [
        "campsite_id",
        "site",
        "loop",
        "campsite_reserve_type",
        "campsite_type",
        "type_of_use",
        "min_num_people",
        "max_num_people",
        "capacity_rating",
    ]

    # add the useful information for filtering
    campsite_df = avail_df.merge(df[keep_cols], on="campsite_id", how="left")
    campsite_df["dt"] = pd.to_datetime(campsite_df["dt"])

    # add day of the week for visibility
    campsite_df["day_of_week"] = campsite_df["dt"].dt.dayofweek

    # if filtering to just available sites, do it
    if only_available:
        campsite_df = campsite_df.loc[campsite_df["avail_status"] == "Available"]

    # clean up the index
    campsite_df.reset_index(inplace=True, drop=True)

    return campsite_df


def filter_campsites_to_available_weekends(campsite_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to *just* campsites available on the weekend, consecutive Friday and Saturday nights.

    .. note::

        If searching for availability at the beginning of the availability window, *do not* use this function. At the
        beginning of the availability window only Friday will be available. Saturday will not yet be reservable *unless*
        you reserve for Friday and stay through Saturday.

    Args:
        campsite_df: Campsite availability dataframe.

    Returns:

    """
    # get campsites available on Friday and Saturday
    weekend_df = campsite_df.loc[
        (campsite_df["day_of_week"] >= 5) & (campsite_df["avail_status"] == "Available")
    ]

    # sort values to ensure records are sequential by date
    weekend_df = weekend_df.sort_values(["campsite_id", "dt"])

    # get date from row below
    weekend_df["date_shift"] = weekend_df.groupby("campsite_id")["dt"].shift(1)

    # get difference in days between current and following row date
    weekend_df["date_diff"] = (weekend_df["dt"] - weekend_df["date_shift"]).dt.days

    # if the date difference is either null (first date in series) or greater than one, flag as new group
    weekend_df["new_group"] = (weekend_df["date_diff"].isna()) | (
        weekend_df["date_diff"] != 1
    )

    # group by the campsite and get the running total of new_group (bool true = 1)
    weekend_df["group_id"] = weekend_df.groupby("campsite_id")["new_group"].cumsum()

    # get a dataframe of the unique camps' consecutive availability
    weekend_df = (
        weekend_df.groupby(["campsite_id", "group_id"])
        .agg(
            start_date=("dt", "min"),
            end_date=("dt", "max"),
            consecutive_days=("dt", "count"),
        )
        .reset_index()
    )

    # filter to just those with more than one day
    weekend_df = weekend_df.loc[
        weekend_df["consecutive_days"] > 1, ["campsite_id", "start_date", "end_date"]
    ].reset_index(drop=True)

    # add the campsite details back on for potential follow-on filtering
    camp_meta_df = campsite_df.drop(
        columns=["dt", "day_of_week", "avail_status", "avail_quantity"], errors="ignore"
    ).drop_duplicates()
    weekend_df = weekend_df.merge(camp_meta_df, on="campsite_id", how="left")

    return weekend_df


def get_4rivers_permit_availability_by_month(
    permit_id: int,
    start_month: int,
    start_year: Optional[int] = None,
    only_available: Optional[bool] = True,
) -> pd.DataFrame:
    """
    Get availability of river permit at a given year and month.

    Args:
        permit_id: Recreation.gov river permit ID.
        start_month: Month being searched.
        start_year: Year being searched.
        only_available: If True, only available dates will be returned. This is the default.

    Returns:

    """
    # if no year is provided, default to current year
    if start_year is None:
        start_year = datetime.now().year

    # construct the url to retrieve
    url_api = (
        f"https://www.recreation.gov/api/permits/{permit_id}/availability/month?"
        f"start_date={start_year}-{start_month:02d}-01T00:00:00.000Z"
        "&commercial_acct=false"
        # '&is_lottery=false'
    )

    # make the call to get the data
    res = requests.get(url_api, headers=_headers_dict)

    # handle problems when they arise
    if res.status_code != 200:
        logging.error(
            f"Encountered an error retrieving {url_api}\n{res.json().get('error')}"
        )
        avail_df = pd.DataFrame(
            columns=["total", "remaining", "show_walkup", "is_secret_quota"]
        )

    else:

        # unpack the data to a dictionary
        res_dict = res.json()

        # pull out the availability from the response
        avail_dict = res_dict.get("payload").get("availability")

        # unpack the date availability
        dates_dict = avail_dict.get(next(iter(avail_dict))).get("date_availability")

        # create a data frame from the availability
        avail_df = pd.DataFrame(dates_dict).transpose()

        # if nothing is available create empty dataframe for returning
        if len(avail_df.index) == 0:
            avail_df = pd.DataFrame(
                columns=[
                    "launch_date",
                    "total",
                    "remaining",
                    "show_walkup",
                    "is_secret_quota",
                ]
            )

        else:
            # pull the dates out of the index so easier to work with later
            avail_df.reset_index(names=["launch_date"], inplace=True)

            # cast the date to datetime in mountain time since this is where the USFS offices are
            avail_df["launch_date"] = pd.to_datetime(avail_df["launch_date"])

            # use only useful columns
            avail_df = avail_df.loc[:, ["launch_date", "total", "remaining"]]

            # filter to just available dates if desired
            if only_available:
                avail_df = avail_df.loc[avail_df["remaining"] > 0]

    return avail_df
