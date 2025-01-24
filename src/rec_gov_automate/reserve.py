from datetime import datetime, timedelta
import re
from typing import Optional

from playwright.sync_api import sync_playwright

__all__ = ["reserve_middle_fork_permit_date"]


def reserve_middle_fork_permit_date(
    recgov_username: str,
    recgov_password: str,
    day: int,
    month: int,
    year: Optional[int] = None,
    trip_days: Optional[int] = 7,
    headless: Optional[bool] = True,
) -> bool:
    """
    Reserve Middle Fork river permit for a specific date.

    Args:
        recgov_username: Username for Recreation.gov.
        recgov_password: Password for Recreation.gov.
        day: Day of reservation.
        month: Month of reservation.
        year: Year of reservation. Defaults to current year.
        trip_days: Trip duration in days. Defaults to 7.
        headless: Whether to use the browser headless mode. Default is True.

    Returns:

    """
    permit_id = 234623

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

        # try to get the date being searched for
        avail_re = rf"""((\b{dt.strftime("%B")}\b)|(\b{dt.strftime("%b")}\b))\s{dt.day:02d},\s{dt.year:04d}\s-\sAvailable"""
        loc = page.get_by_label(re.compile(avail_re))

        # gives the page a moment to load content
        loc.hover()

        # if the date is not available, set status to return
        if loc.count() == 0:
            status = False

        # if the date is available
        else:

            # select the date
            loc.click()

            # click the book now button
            page.get_by_role("button", name="Book Now").click()

            # modal div will be presented to log in

            # populate the information and log in
            page.get_by_label("Email* (Required)").fill(recgov_username)
            page.get_by_label("Password* (Required)").fill(recgov_password)
            page.get_by_role("button", name="Log In", exact=True).click()

            # permit will be put in cart, and form page will be loaded to input details for permit

            # launch at boundary creek
            if not headless:
                page.get_by_label(
                    "Launch Location* (Required)"
                ).scroll_into_view_if_needed()

            page.get_by_label("Launch Location* (Required)").select_option("2100")

            # take-out at cache bar boat ramp
            if not headless:
                page.get_by_label(
                    "Take-out Location* (Required)"
                ).scroll_into_view_if_needed()

            page.get_by_label("Take-out Location* (Required)").select_option("2108")

            # open calendar selector
            if not headless:
                page.get_by_role(
                    "button", name="Exit Date (Required)"
                ).scroll_into_view_if_needed()
            else:
                page.get_by_role("button", name="Exit Date (Required)").hover()

            page.get_by_role("button", name="Exit Date (Required)").click()

            # create string to select date by the div label
            dt_exit = dt + timedelta(days=trip_days)
            # dt_exit_str = dt_exit.strftime(r"%A, %b %-d, %Y - Available")
            dt_exit_re = rf"""((\b{dt_exit.strftime("%B")}\b)|(\b{dt_exit.strftime("%b")}\b))\s{dt_exit.day:02d},\s{dt_exit.year:04d}\s-\sAvailable"""

            # select and click the exit date, which closes the calendar selector
            if not headless:
                page.get_by_label(re.compile(dt_exit_re)).scroll_into_view_if_needed()
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

            # pick up permit at boundary creek (issuing station)
            if not headless:
                page.get_by_label(
                    "Station Location* (Required)"
                ).scroll_into_view_if_needed()

            page.get_by_label("Station Location* (Required)").select_option("2300")

            # click terms block
            if not headless:
                page.get_by_label(
                    "Need to Know", exact=True
                ).scroll_into_view_if_needed()

            page.get_by_label("Need to Know", exact=True).click()

            # scroll all terms
            page.mouse.wheel(delta_x=0, delta_y=700)

            # click acceptance of terms
            if not headless:
                page.locator("label").filter(
                    has_text="Yes, I have read and agree to"
                ).locator("span").first.scroll_into_view_if_needed()

            page.locator("label").filter(
                has_text="Yes, I have read and agree to"
            ).locator("span").first.check()

            # click view cart to commit trip properties (speeds up checkout later)
            page.get_by_test_id("OrderDetailsSummary-cart-btn").click()

            # set status to return
            status = True

        # close the browser
        browser.close()

        return status


def remove_reservations(
    recgov_username: str, recgov_password: str, headless: Optional[bool] = True
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
