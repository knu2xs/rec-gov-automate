import datetime
import logging
import re

from playwright.sync_api import sync_playwright, Page
import pytz

from rec_gov_automate import FourRivers
from rec_gov_automate.utils.reserve import _get_recgov_credentials
from rec_gov_automate.utils.notification import send_sms

# variables for running - set these
river_slug = 'middle_fork'
launch_month = 7
launch_day = 7
recgov_user = None
recgov_pass = None
sms_number = None
headless = True


def login(page: Page):
    """Login if necessary if not already logged in."""
    # click the login button to present the modal
    login_ele = page.get_by_role("button", name="Sign Up or Log In")
    if login_ele.count() > 0:
        login_ele.click()

        # populate the information and log in
        page.get_by_label("Email* (Required)").fill(recgov_username)
        page.get_by_label("Password* (Required)").fill(recgov_password)
        page.get_by_role("button", name="Log In", exact=True).click()

    return page


# configure logging to know what is going on
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s: %(message)s')

# flag for tracking if successfully secured a permit
permit_secured = False

# get credentials if necessary
recgov_username, recgov_password = _get_recgov_credentials(
    recgov_user, recgov_pass
)

# default to current year
year = datetime.datetime.now().year

# create a datetime for the day being retrieved
dt = datetime.datetime(year, launch_month, launch_day)

# create a string of the datetime for reporting status
dt_str = dt.strftime("%a %d%b")

# get the sunday datetime for the date being retrieved
dt_sun = dt - datetime.timedelta(days=dt.weekday() + 1)

# create a river instance
rvr = FourRivers._get_river(river_slug)

# format the name of the river
river_name = rvr.permit_key.replace("_", " ").title()

# regex status patterns
date_re = rf"""((\b{dt.strftime("%B")}\b)|(\b{dt.strftime("%b")}\b))\s(({dt.day})|({dt.day:02d})),\s{dt.year:04d}"""
lottery_re = rf"""{date_re}\s-\sLottery"""
avail_re = rf"""{date_re}\s-\sAvailable"""
unaval_re = rf"""{date_re}\s-\sUnavailable"""

# create the url to retrieve
url = (
    f"https://www.recreation.gov/permits/{rvr.permit_id}/registration/detailed-availability"
    f"?date={dt_sun.year:04d}-{dt_sun.month:02d}-{dt_sun.day:02d}"
)

# initialize playwright
with sync_playwright() as pw:

    # create browser and page instances
    browser = pw.chromium.launch(headless=headless)
    page = browser.new_page()

    # load the landing page and login to speed up checkout when permit becomes available
    page.goto('https://www.recreation.gov')
    login(page)

    # keep trying to get a permit
    while not permit_secured:

        # load the page
        page.goto(url)

        # make sure logged in...just in case got logged out while script running
        login(page)

        # ensure date grid has loaded
        date_loc = page.get_by_label(re.compile(date_re))
        date_loc.hover()

        # first, check if it is not yet released, a lottery date (speeds up checking for cancellations on 15 Mar)
        if page.get_by_label(re.compile(lottery_re)).count() > 0:
            status = False
            logging.info(f'{river_name} launching on {dt_str} is still being held in the lottery.')

        # next, check if not available to avoid waiting for timeout when searching for available
        elif page.get_by_label(re.compile(unaval_re)).count() > 0:
            status = False
            logging.info(f'{river_name} launching on {dt_str} is "unavailable".')

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

                # give the page a chance to present the checkout so it is confirmed in the cart
                page.get_by_label('Cart - 1 item in cart.').hover()

                # close the browser
                browser.close()

                # change the secured status
                permit_secured = True

        # provide status update
        if not permit_secured:
            logging.debug(f'{river_name} launching on {dt_str} could not be secured.')

        # if got the permit
        else:

            # announce success
            logging.info(f'Secured {river_name} launching on {dt_str}.')

            # format the expiration time string
            tm_str = (
                    datetime.datetime.now(tz=pytz.timezone("US/Pacific")) + datetime.timedelta(minutes=14)
            ).strftime("%H:%M")

            # create the message string
            msg_str = f'{river_name} permit for a {dt_str} launch is in your cart until {tm_str}\nhttps://recreation.gov/cart'

            # send notification
            send_sms(msg_str, sms_number)
