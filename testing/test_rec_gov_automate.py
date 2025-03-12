from datetime import datetime, timedelta

import pandas as pd
import pytz

from rec_gov_automate import FourRivers, get_fourrivers_availability
from rec_gov_automate.utils.reserve import clear_cart
from rec_gov_automate.utils.notification import (
    send_sms,
    send_gmail,
    send_pushover,
)

headless = True


def test_clear_cart():
    clear_cart(headless=False)


def test_reserve_river_permit_date_middle_fork():

    # date to try and reserve
    month = 12
    day = 12

    rvr = FourRivers.get_middle_fork()
    rvr.reserve_date(day, month)


def test_reserve_river_permit_date_main_salmon_and_nofify():

    # unique main salmon properties
    month = 12  # December
    day = 12

    rvr = FourRivers.get_main_salmon()
    rvr.reserve_date(day, month)

    dt_str = datetime(datetime.today().year, month, day).strftime("%a %d %b")
    tm_str = (
        datetime.now(tz=pytz.timezone("US/Pacific")) + timedelta(minutes=15)
    ).strftime("%H:%M")

    message_short = f"Main Salmon launch on {dt_str}"
    message = (
        message_short
        + f" is in your cart until {tm_str}.\n\nhttps://recreation.gov/cart"
    )

    send_pushover(message)
    send_gmail(
        "knu2xs@gmail.com",
        subject=message_short,
        body=message,
    )


def test_send_sms():

    message = "Test Recreation.gov Notification https://recreation.gov/cart"
    resp_lst = send_sms(message)

    assert all([resp.successful for resp in resp_lst])


def test_send_pushover():

    message = "Test Recreation.gov Notification"
    resp = send_pushover(message)


def test_search_using_dataframe(search_df: pd.DataFrame):

    avail_df = get_fourrivers_availability(search_df=search_df)
    assert len(avail_df.index) == 2


def test_try_reserve_cancellation_not_yet_released():

    from rec_gov_automate.utils.reserve import reserve_4rivers_permit_date

    river = "selway"
    month = 7
    day = 14
    headless = False

    rvr = FourRivers._get_river(river)

    status = reserve_4rivers_permit_date(
        permit_id=rvr.permit_id,
        day=day,
        month=month,
        launch_location_code=rvr.putin_code,
        takeout_location_code=rvr.takeout_code,
        pickup_permit_location_code=rvr.permit_pickup_location_code,
        trip_days=rvr.trip_days,
        headless=headless,
    )

    assert status is False


def test_try_reserve_outside_permit_season_available():

    from rec_gov_automate.utils.reserve import reserve_4rivers_permit_date

    river = "main_salmon"
    month = 12
    day = 25
    headless = False

    rvr = FourRivers._get_river(river)

    status = reserve_4rivers_permit_date(
        permit_id=rvr.permit_id,
        day=day,
        month=month,
        launch_location_code=rvr.putin_code,
        takeout_location_code=rvr.takeout_code,
        pickup_permit_location_code=rvr.permit_pickup_location_code,
        trip_days=rvr.trip_days,
        headless=headless,
    )

    assert status is True


def test_try_reserve_outside_permit_season_unavailable():

    from rec_gov_automate.utils.reserve import reserve_4rivers_permit_date

    river = "main_salmon"
    month = 9
    day = 3
    headless = False

    rvr = FourRivers._get_river(river)

    status = reserve_4rivers_permit_date(
        permit_id=rvr.permit_id,
        day=day,
        month=month,
        launch_location_code=rvr.putin_code,
        takeout_location_code=rvr.takeout_code,
        pickup_permit_location_code=rvr.permit_pickup_location_code,
        trip_days=rvr.trip_days,
        headless=headless,
    )

    assert status is True
