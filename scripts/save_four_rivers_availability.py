from datetime import datetime
import importlib.util
import logging
from pathlib import Path
import sys

import pandas as pd

# relative locations to load supporting library from
pkg_name = "rec_gov_automate"

# if working locally for development, use relative location
src_pth = Path(__file__).parent.parent / "src"

# support relative imports
if not importlib.util.find_spec(pkg_name):
    sys.path.insert(0, str(src_pth))

# ensure the package can be imported
if not importlib.util.find_spec(pkg_name):
    raise EnvironmentError(
        f"""The package "{pkg_name} cannot be loaded. Please ensure it is available in ./src"""
    )

# import needed resources
from rec_gov_automate.main import get_fourrivers_availability
from rec_gov_automate.utils import format_pandas_for_logging

if __name__ == "__main__":

    # set logging level
    logging.basicConfig(level='INFO')

    # get the current date
    dt_now = datetime.now()

    # use the date to create the path for saving all searched availability
    data_dir = Path(__file__).parent.parent / "data"
    csv_name = dt_now.strftime("fourrivers_avail_%Y%m%dT%H%M%S.csv")
    csv_suffix = f"fourrivers/availability/year={dt_now.year}/month={dt_now.month:02d}/day={dt_now.day:02d}/{csv_name}"
    csv_pth = data_dir / csv_suffix

    # ensure the data directory exists
    if not csv_pth.parent.exists():
        csv_pth.parent.mkdir(parents=True)

    # get full dataframe of four rivers permit season availability
    full_df = get_fourrivers_availability(permit_season=True)

    # report total records count
    logging.info(f"Dataframe length: {len(full_df):,}")

    # reduce to just available dates and necessary columns
    avail_df = full_df.loc[
        full_df["remaining"] > 0,
        ["river", "launch_date", "total", "remaining", "days_to_launch"],
    ]

    # sort by date and river
    # avail_df.sort_values(by=["launch_date", "river"], inplace=True)
    avail_df.sort_values(by=["river", "launch_date"], inplace=True)

    # report available dates
    logging.info(f"Total available dates: {avail_df.shape[0]}")

    # format date columns for legibility
    avail_df["launch_date"] = pd.to_datetime(avail_df["launch_date"]).dt.date

    # log availability
    logging.info(format_pandas_for_logging(avail_df, "Four Rivers Availablity"))

    # save to csv
    avail_df.to_csv(csv_pth, encoding="utf-8", index=False)

    # useful for tracking successful completion
    logging.info(f"Successfully saved four rivers availability to {csv_pth}")
