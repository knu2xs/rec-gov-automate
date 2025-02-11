from pathlib import Path

import pandas as pd

from rec_gov_automate.utils import get_recgov_credentials
from rec_gov_automate.availability import get_4rivers_permit_availability_by_month
from rec_gov_automate.reserve import (
    reserve_middle_fork_permit_date,
    remove_reservations,
)

# headless state for interactive testing
headless = True

# middle fork permit id on recreation.gov
permit_id = 234623

# December 12th is likely pretty reliable
month = 12
day = 12


def test_get_middle_fork_availability():
    # get available dates
    avail_df = get_4rivers_permit_availability_by_month(permit_id, start_month=month)

    assert isinstance(avail_df, pd.DataFrame)
    assert len(avail_df.index) > 0


def test_reserve_middle_fork_permit_date(secrets_path):

    # default to not passing
    reserved = False

    # get available dates
    avail_df = get_4rivers_permit_availability_by_month(permit_id, start_month=month)

    # filer to just the availability on the day of the month and available permits
    avail_df = avail_df.loc[
        (avail_df["date"].dt.day == day) & (avail_df["remaining"] > 0)
    ]

    # create boolean indicating if there is availability
    avail = avail_df.shape[0] == 1

    # read the secrets file and get credentials
    recgov_username, recgov_password = get_recgov_credentials(secrets_path)

    # if there is availability on the requested date
    if avail:

        # make the reservation
        reserved = reserve_middle_fork_permit_date(
            recgov_username, recgov_password, day, month, headless=headless
        )

    assert reserved

    # clean up reservations
    # remove_reservations(recgov_username, recgov_password)
