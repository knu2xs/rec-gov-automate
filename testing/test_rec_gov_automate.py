from rec_gov_automate.availability import get_river_permit_availability_by_month
from rec_gov_automate.reserve import reserve_4rivers_permit_date, remove_reservations
from rec_gov_automate.utils import get_recgov_credentials

headless = False


def test_remove_reservations(recgov_credentials):
    remove_reservations(*recgov_credentials, headless=False)


def test_reserve_river_permit_date_middle_fork(secrets_path):

    # unique middle fork properties
    permit_id = 234623  # middle fork
    month = 12  # December
    day = 12
    putin_id = 2100  # boundary creek
    takeout_id = 2108  # main
    pickup_permit_loc_id = 2300  # boundary creek
    days = 7

    # default to not passing
    reserved = False

    # get available dates
    avail_df = get_river_permit_availability_by_month(permit_id, start_month=month)

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
        reserved = reserve_4rivers_permit_date(
            permit_id,
            recgov_username,
            recgov_password,
            day,
            month,
            putin_id,
            takeout_id,
            pickup_permit_loc_id,
            days,
            headless=headless,
        )

    assert reserved


def test_reserve_river_permit_date_main_salmon(secrets_path):

    # unique middle fork properties
    permit_id = 234622  # main salmon
    month = 12  # December
    day = 12
    putin_id = 2400  # corn creek
    takeout_id = 2409  # carey creek
    pickup_permit_loc_id = 2412  # corn creek
    days = 7

    # default to not passing
    reserved = False

    # get available dates
    avail_df = get_river_permit_availability_by_month(permit_id, start_month=month)

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
        reserved = reserve_4rivers_permit_date(
            permit_id,
            recgov_username,
            recgov_password,
            day,
            month,
            putin_id,
            takeout_id,
            pickup_permit_loc_id,
            days,
            headless=headless,
        )

    assert reserved
