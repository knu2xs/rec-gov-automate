from configparser import ConfigParser
from pathlib import Path

import pandas as pd

from rec_gov_automate import get_fourrivers_availability
from rec_gov_automate.utils.notification import send_pushover

# path to config file
config_pth = Path(__file__).parent / 'config.ini'


if __name__ == "__main__":

    # get the pushover api key (channel to use) from the config
    config = ConfigParser()
    config.read(config_pth)
    pushover_api_key = config.get('RECGOV', 'PUSHOVER_API_KEY')

    # find what is available and trim the schema
    avail_df = get_fourrivers_availability(permit_season=True)

    # filter to just those with availablity and clean up the schema
    avail_df = avail_df.loc[avail_df['remaining'] > 0, ["river", "launch_date", "remaining"]]

    # if anything is available
    if len(avail_df.index) > 0:

        # start writing the string to notify
        notify_str = "Four Rivers cancellations are available!\n\n"

        # iterate and format
        for _, river, launch_dt, permit_cnt in avail_df.itertuples():

            # format the name of the river
            river_name = river.replace("_", " ").title()

            # format the date
            dt_str = launch_dt.strftime("%a %d%b")

            # assemble the string
            if permit_cnt == 1:
                avail_str = f"{river_name}: {dt_str} - {permit_cnt} permit\n"
            else:
                avail_str = f"{river_name}: {dt_str} - {permit_cnt} permits\n"

            # add the string
            notify_str = notify_str + avail_str

        # send the notification
        send_pushover(notify_str, api_token=pushover_api_key)
