import logging
import math
import os
from datetime import datetime, timedelta
import re
from typing import Optional, Union

from playwright.sync_api import sync_playwright

__all__ = [
    "reserve_4rivers_permit_date",
    "clear_cart",
]


def _get_recgov_credentials(
    recgov_username: Optional[str],
    recgov_password: Optional[str],
) -> tuple[str, str]:
    """Helper to get recgov credentials from environment variables or allow user to specify them."""
    # cast inputs to None if NaN
    if isinstance(recgov_username, float):
        if math.isnan(recgov_username):
            recgov_username = None

    if isinstance(recgov_password, float):
        if math.isnan(recgov_password):
            recgov_password = None

    # try to retrieve credentials for recreation.gov if not provided
    if (recgov_password is None and recgov_username is not None) or (
        recgov_password is not None and recgov_username is None
    ):
        raise ValueError(
            "If providing recreation.gov credentials, recgov_password and recgov_username must be set."
        )
    elif recgov_password is None and recgov_username is None:
        # load the variables
        recgov_username = os.environ.get("RECGOV_USERNAME")
        recgov_password = os.environ.get("RECGOV_PASSWORD")

    if recgov_username is None or recgov_password is None:
        raise EnvironmentError(
            "Cannot load Recreation.gov credentials from environment variables, RECGOV_USERNAME and RECGOV_PASSWORD, "
            "and recgov_password and recgov_username are not provided in the input arguments. Hence, cannot log into "
            "Recreation.gov."
        )

    return recgov_username, recgov_password


def reserve_4rivers_permit_date(
    permit_id: Union[str, int],
    day: int,
    month: int,
    launch_location_code: Union[str, int],
    takeout_location_code: Union[str, int],
    pickup_permit_location_code: Union[str, int],
    trip_days: Optional[int],
    year: Optional[int] = None,
    recgov_username: Optional[str] = None,
    recgov_password: Optional[str] = None,
    headless: Optional[bool] = True,
) -> bool:
    """
    Reserve four rivers river permit for a specific date.

    Args:
        permit_id: Unique permit ID on Recreation.gov.
        day: Day of reservation.
        month: Month of reservation.
        recgov_username: Username for Recreation.gov.
        recgov_password: Password for Recreation.gov.
        launch_location_code: Launch location code...has to be derived from inspecting the reservation page.
        takeout_location_code: Takeout location code...has to be derived from inspecting the reservation page.
        pickup_permit_location_code: Code for location where permit will be picked up location code...has to be
          derived from inspecting the reservation page.
        year: Year of reservation. Defaults to current year.
        trip_days: Trip duration in days. Defaults to 7.
        headless: Whether to use the browser headless mode. Default is True.
    """
    # get credentials if necessary
    recgov_username, recgov_password = _get_recgov_credentials(
        recgov_username, recgov_password
    )

    # default to current year
    if year is None:
        year = datetime.now().year

    # create a datetime for the day being retrieved
    dt = datetime(year, month, day)

    # get the sunday datetime for the date being retrieved
    dt_sun = dt - timedelta(days=dt.weekday() + 1)

    # create the url to retrieve
    url = (
        f"https://www.recreation.gov/permits/{permit_id}/registration/detailed-availability"
        f"?date={dt_sun.year:04d}-{dt_sun.month:02d}-{dt_sun.day:02d}"
    )

    # create a playwright page to use
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url)

        # regex for getting availability cell date, letting it load
        date_re = rf"""((\b{dt.strftime("%B")}\b)|(\b{dt.strftime("%b")}\b))\s{dt.day:02d},\s{dt.year:04d}"""
        date_loc = page.get_by_label(re.compile(date_re))
        date_loc.hover()

        # regex status patterns
        lottery_re = rf"""{date_re}\s-\sLottery"""
        avail_re = rf"""{date_re}\s-\sAvailable"""
        unaval_re = rf"""{date_re}\s-\sUnavailable"""

        # first, check if it is not yet released, a lottery date (speeds up checking for cancellations on 15 Mar)
        if page.get_by_label(re.compile(lottery_re)).count() > 0:
            status = False

        # next, check if not available to avoid waiting for timeout when searching for available
        elif page.get_by_label(re.compile(unaval_re)).count() > 0:
            status = False

        # if not lottery status or unavailable, try to reserve the date
        else:

            # try to get the date being searched for
            avail_loc = page.get_by_label(re.compile(avail_re))

            # if the date is not available, set status to return...accounting for not getting caught above
            if avail_loc.count() == 0:
                status = False

            # if the date is available
            else:

                # select the date
                avail_loc.click()

                # click the book now button
                page.get_by_role("button", name="Book Now").click()

                # modal div will be presented to log in

                # populate the information and log in
                page.get_by_label("Email* (Required)").fill(recgov_username)
                page.get_by_label("Password* (Required)").fill(recgov_password)
                page.get_by_role("button", name="Log In", exact=True).click()

                # permit will be put in cart, and form page will be loaded to input details for permit
                status = True

                # try to autofill permit information
                try:

                    # set launch location
                    if not headless:
                        page.get_by_label(
                            "Launch Location* (Required)"
                        ).scroll_into_view_if_needed()

                    page.get_by_label("Launch Location* (Required)").select_option(
                        str(launch_location_code)
                    )

                    # set take-out
                    if not headless:
                        page.get_by_label(
                            "Take-out Location* (Required)"
                        ).scroll_into_view_if_needed()

                    page.get_by_label("Take-out Location* (Required)").select_option(
                        str(takeout_location_code)
                    )

                    # open calendar selector
                    if not headless:
                        page.get_by_role(
                            "button", name="Exit Date (Required)"
                        ).scroll_into_view_if_needed()
                    else:
                        page.get_by_role("button", name="Exit Date (Required)").hover()

                    page.get_by_role("button", name="Exit Date (Required)").click()

                    # create string to select date by the div label
                    dt_exit = dt + timedelta(days=trip_days - 1)
                    dt_exit_re = rf"""((\b{dt_exit.strftime("%B")}\b)|(\b{dt_exit.strftime("%b")}\b))\s{dt_exit.day:02d},\s{dt_exit.year:04d}\s-\sAvailable"""

                    # select and click the exit date, which closes the calendar selector
                    if not headless:
                        page.get_by_label(
                            re.compile(dt_exit_re)
                        ).scroll_into_view_if_needed()
                    else:
                        page.get_by_label(re.compile(dt_exit_re)).hover()

                    page.get_by_label(re.compile(dt_exit_re)).click()

                    # select one craft, a single raft
                    if not headless:
                        page.get_by_label("Type* (Required)").scroll_into_view_if_needed()

                    page.get_by_label("Type* (Required)").select_option("10")

                    # click to add single watercraft
                    if not headless:
                        page.get_by_label("Type* (Required)").scroll_into_view_if_needed()

                    page.get_by_label("Add watercraft").click()

                    # try to find element to select issuing station - may not be present if only one issuing station
                    sel_station = page.get_by_label("Station Location* (Required)")

                    # if possible to select issuing station
                    if sel_station.count() > 0:

                        # select issuing station if possible
                        if not headless:
                            page.get_by_label(
                                "Station Location* (Required)"
                            ).scroll_into_view_if_needed()

                        page.get_by_label("Station Location* (Required)").select_option(
                            str(pickup_permit_location_code)
                        )

                    # click terms block
                    if not headless:
                        page.get_by_label(
                            "Need to Know", exact=True
                        ).scroll_into_view_if_needed()

                    page.get_by_label("Need to Know", exact=True).click()

                    # scroll all terms
                    page.mouse.wheel(delta_x=0, delta_y=700)

                    # click scroll the terms
                    if not headless:
                        page.locator("label").filter(
                            has_text="Yes, I have read and agree to"
                        ).locator("span").first.scroll_into_view_if_needed()

                    # click acceptance of terms
                    page.locator("label").filter(
                        has_text="Yes, I have read and agree to"
                    ).locator("span").first.check()

                    # click view cart to commit trip properties (speeds up checkout later)
                    page.get_by_test_id("OrderDetailsSummary-cart-btn").click()

                except Exception as e:
                    logging.warning('Could not autofill trip properties, but was able to reserve permit.')

        # close the browser
        browser.close()

        return status


def clear_cart(
    recgov_username: Optional[str] = None,
    recgov_password: Optional[str] = None,
    headless: Optional[bool] = True,
):
    """
    Remove all reservations from a recreation.gov account cart.

    Args:
        recgov_username: Username of the recreation.gov account.
        recgov_password: Password of the recreation.gov account.
        headless: Boolean to enable headless mode. Defaults to True.

    Returns:
        Reservation count removed.
    """
    # get credentials if necessary
    recgov_username, recgov_password = _get_recgov_credentials(
        recgov_username, recgov_password
    )

    # open playwright page to recreation.gov homepage
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto("https://recreation.gov")

        # open modal to log in, and do so
        page.get_by_label("Sign Up or Log In").click()
        page.get_by_label("Email* (Required)").fill(recgov_username)
        page.get_by_label("Password* (Required)").fill(recgov_password)
        page.get_by_role("button", name="Log In", exact=True).click()

        # navigate to the current cart
        page.get_by_label("Cart").click()

        # counter to track removed reservation count
        cnt = 0

        # iteratively remove all reservations
        for remove_btn in page.get_by_label("Remove Reservation").all():
            remove_btn.click()
            page.get_by_role("button", name="Yes").click()

            # increment count
            cnt += 1

        # close the browser
        browser.close()

        return cnt
