from datetime import datetime, timedelta
import json

import pandas as pd
import requests
import user_agent

campground_id = 232464  # klaloch
start_year = 2025
start_month = 5
start_day = 1

# create campground url using identifier
url_api = f'https://www.recreation.gov/api/camps/availability/campground/{campground_id}/month?start_date={start_year}-{start_month:02d}-{start_day:02d}T00%3A00%3A00.000Z'

# configure the headers
headers_dict = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
}

# get campground availability json
res = requests.get(url_api, headers=headers_dict)

# ensure valid response
if res.status_code == 200:
    
    # extract the JSON
    res_dict = res.json()

    pass

# handle any other response
else:
    pass
