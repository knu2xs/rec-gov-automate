from datetime import datetime, timedelta
import logging
from pathlib import Path
import pytz

import pandas as pd

from rec_gov_automate import FourRivers, get_fourrivers_availability
from rec_gov_automate.utils.notification import send_sms

# path to find search csv with rivers and dates to search for
this_dir = Path(__file__).parent
search_csv = this_dir / "four_rivers_search.csv"
status_csv = this_dir / "reserve_status.csv"

# read in the dataframe with rivers and dates to search for
search_df = pd.read_csv(search_csv)

# get the availability data frame
avail_df = get_fourrivers_availability(permit_season=True, search_df=search_df)

# read in the status table...ensures not trying to double-reserve dates
if status_csv.exists():
    status_df = pd.read_csv(status_csv)

# if the status table does not already exist, create a dataframe from the search table to use
else:
    status_df = pd.DataFrame(search_df['search_group'].unique(), columns=['search_group'])
    status_df['secured_permit'] = False

# flag tracking if status changed
status_flg = False

# add the status data frame to the search data frame
search_df = search_df.merge(status_df, on='search_group', how='left')

# filter the search data frame to just the permits available and search groups without a permit
search_df = search_df.loc[~search_df['secured_permit']]

# if permits are available and desired, try to get one
if len(search_df.index) > 0:

    # iterate the search groups
    for search_group in search_df['search_group'].unique():

        # set a flag for reserved status in this serach group
        secured_permit = False

        # if there are any permits availble, iteratively try to retrive them
        for idx, avail_row in avail_df[avail_df['search_group'] == search_group].iterrows():
            
            # convert the series to a dict for failover property retrieval
            avail_dict = avail_row.to_dict()

            # create a river instance
            rvr = FourRivers._get_river(
                river_key=avail_row.river,
                trip_days=avail_dict.get('trip_days'),
                launch_location_code=avail_dict.get('putin_id'),
                takeout_location_code=avail_dict.get('takeout_id'),
                pickup_permit_location_code=avail_dict.get('permit_pickup_id')
            )

            # use the river instance to try and secure the permit
            secured_permit = rvr.reserve_date(
                day=avail_row.launch_date.day,
                month=avail_row.launch_date.month,
                year=avail_row.launch_date.year,
                recgov_username=avail_dict.get('recgov_user'),
                recgov_password=avail_row.get('recgov_pass'),
            )

            # if a permit is successfully secured
            if secured_permit:

                # set the status for this search group in the dataframe
                status_df.loc['search_group' == avail_row.search_group] = True

                # change the status changed flag
                status_flg = True

                # format the name of the river
                river_name = avail_row.river_key.replace("_", " ").title()

                # format the date
                dt_str = avail_row.launch_dt.strftime("%a %d%b")

                tm_str = (
                    datetime.now(tz=pytz.timezone("US/Pacific")) + timedelta(minutes=14)
                ).strftime("%H:%M")

                # create the message string
                msg_str = f'{river_name} permit for a {dt_str} launch is in your cart until {tm_str}\n\nhttps://recreation.gov/cart'

                # provide a notification
                send_sms(msg_str)

                # quit searching in this search group
                break

# Wite status out for next run if a permit was secured
if status_flg:
    status_df.to_csv(status_csv, encoding='utf-8')
