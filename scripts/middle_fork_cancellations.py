from pathlib import Path

from rec_gov_automate.utils import get_recgov_credentials
from rec_gov_automate.availability import get_river_permit_availability_by_month
from rec_gov_automate.reserve import reserve_middle_fork_permit_date


dir_prj = Path(__file__).parent.parent
secrets_pth = dir_prj / "config" / "secrets.ini"


# block to run
if __name__ == "__main__":

    # October 12th is likely pretty reliable
    month = 9
    day = 12

    # get available dates
    avail_df = get_river_permit_availability_by_month(234623, start_month=month)

    # filer to just the availability on the day of the month and available permits
    avail_df = avail_df.loc[
        (avail_df["date"].dt.day == day) & (avail_df["remaining"] > 0)
    ]

    # create boolean indicating if there is availability
    avail = avail_df.shape[0] == 1

    # if there is availability on the requested date
    if avail:

        # read the secrets file and get credentials
        recgov_username, recgov_password = get_recgov_credentials(secrets_pth)

        # make the reservation
        reserved = reserve_middle_fork_permit_date(
            recgov_username, recgov_password, day, month, headless=False
        )
