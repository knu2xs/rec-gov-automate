from configparser import ConfigParser
from datetime import datetime, timedelta
from pathlib import Path
import re
from typing import Union
from warnings import warn


from playwright.sync_api import sync_playwright, Page, Mouse

year = 2025
month = 5
day = 4
headless = False
trip_days = 7

dir_prj = Path(__file__).parent.parent
secrets_pth = dir_prj / 'config' / 'secrets.ini'

def get_recgov_credentials(secrets_path: Path) -> tuple[str, str]:
    """Get the username and password as a tuple for Recreation.gov from the ``secrets.ini`` config file."""
    # ensure the secrets.ini file exists
    if not secrets_path.exists():
        raise FileNotFoundError(f'Cannot locate secrets.ini config file at {secrets_path}')
    
    # initialize variables
    recgov_username, recgov_password = None, None
    
    # read in the secrets file
    with open(secrets_path, 'r') as secrets_f:
        secrets_config = ConfigParser()
        secrets_config.read_file(secrets_f)

        # retrieve the username and password
        recgov_username = secrets_config.get('DEFAULT', 'RECGOV_USERNAME')
        recgov_password = secrets_config.get('DEFAULT', 'RECGOV_PASSWORD')

        if recgov_username is None and recgov_password is None:
            warn(f'Null values retrieved from secrets for username and password from {secrets_path}')
        elif recgov_password is None:
            warn(f'Null password retrieved from {secrets_path}')
        elif recgov_password is None:
            warn(f'Null username retrieved from {secrets_path}')

    return recgov_username, recgov_password


def get_permit_home_url(permit_id: Union[str, int]) -> str:
    """Create the river permit string."""
    url = f"https://www.recreation.gov/permits/{permit_id}"
    return url


# block to run
if __name__ == '__main__':

    # get run timestamp
    dt_now = datetime.now()

    # get the current month; necessary because the month being shown is the current month
    now_month_str = dt_now.strftime('%B')

    # url to use
    url = get_permit_home_url(234623)

    # create a playwright page to use
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url)
        
        # get available dates for the displayed month
        avail_loc = page.get_by_label(re.compile(" - Available"))
        avail_all = avail_loc.all()

        # iterate available dates
        for avail in avail_all:

            # 
            pass

        # close the browser
        browser.close()