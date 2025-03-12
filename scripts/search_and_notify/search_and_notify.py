from configparser import ConfigParser
from pathlib import Path

import pandas as pd

from rec_gov_automate import get_fourrivers_availability
from rec_gov_automate.utils.notification import send_sms

# path to find search csv with rivers and dates to search for
search_csv = Path(__file__).parent / "four_rivers_search.csv"


if __name__ == "__main__":

    # ensure the file exists
    if not search_csv.exists():
        raise FileNotFoundError(
            f"Cannot access {search_csv}. Please ensure this path exists and is accessible."
        )

    # read in the rivers and dates to search for
    search_df = pd.read_csv(search_csv)

    # find what is available and trim the schema
    avail_df = get_fourrivers_availability(permit_season=True, search_df=search_df).loc[
        :, ["river", "launch_date", "remaining"]
    ]

    # if anything is available
    if len(avail_df.index) > 0:

        # start writing the string to notify
        notify_str = "Four Rivers cancellations are available!\n\n"

        # iterate and format
        for _, river_key, launch_dt, permit_cnt in avail_df.itertuples():

            # format the name of the river
            river_name = river_key.replace("_", " ").title()

            # format the date
            dt_str = launch_dt.strftime("%a %d%b")

            # assemble the string
            avail_str = f"{river_name}: {dt_str} - {permit_cnt} permits\n"

            # add the string
            notify_str = notify_str + avail_str

        # send the notification
        send_sms(notify_str)
