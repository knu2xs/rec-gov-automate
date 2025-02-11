import logging
from datetime import datetime, timezone
from functools import cache
from typing import Optional, Union

import pandas as pd
import requests
from dateutil.relativedelta import FR, relativedelta

from .utils.availability import get_4rivers_permit_availability_by_month, _headers_dict
from .utils.reserve import reserve_4rivers_permit_date

__all__ = ["FourRivers"]

# four rivers permit ids correlating to those on recreation.gov
permit_ids = {
    "selway": 234624,
    "main_salmon": 234622,
    "middle_fork": 234623,
    "hells_canyon": 234625,
}

default_codes = {
    "main_salmon": [
        2400,  # putin - corn creek
        2409,  # takeout - carey creek
        2412,  # permit pickup - corn creek
    ],
    "middle_fork": [
        2100,  # putin - boundary creek
        2108,  # takeout - cache bar
        2300,  # permit pickup - boundary creek
    ],
    "hells_canyon": [
        2600,  # putin - hells canyon creek launch
        2603,  # takeout - heller bar
        2600,  # permit pickup - hells canyon creek launch
    ],
    "selway": [
        2000,  # putin - paradise
        2004,  # takeout - race creek
        2000,  # permit pickup - paradise
    ],
}

# create timestamps for the start and the end of the permit season
current_year = datetime.now().year

# Hells' Canyon start date is the Friday prior to Memorial Day, so calculate this
start_date = datetime(datetime.today().year, 5, 31) + relativedelta(weekday=FR(-2))

permit_seasion_dict = {
    "main_salmon": [
        # 28May - 03Sep
        pd.to_datetime(f"{current_year}-05-28", utc=True),
        pd.to_datetime(f"{current_year}-09-03", utc=True),
    ],
    "middle_fork": [
        # 28May - 03Sep
        pd.to_datetime(f"{current_year}-05-28", utc=True),
        pd.to_datetime(f"{current_year}-09-03", utc=True),
    ],
    "hells_canyon": [
        # Friday prior to Memorial Day - 03Sep
        pd.to_datetime(
            datetime(datetime.today().year, 5, 31) + relativedelta(weekday=FR(-2)),
            utc=True,
        ),
        pd.to_datetime(f"{current_year}-09-03", utc=True),
    ],
    "selway": [
        # 15May - 31Jul
        pd.to_datetime(f"{current_year}-05-15", utc=True),
        pd.to_datetime(f"{current_year}-07-31", utc=True),
    ],
}


class FourRivers:

    def __init__(
        self,
        permit_id: int,
        trip_days: Optional[int] = 7,
        putin_code: Optional[Union[str, int]] = None,
        takeout_code: Optional[Union[str, int]] = None,
        permit_pickup_location_code: Optional[Union[str, int]] = None,
    ):
        """

        Args:
            trip_days: Trip duration in days. Defaults to 7.
            putin_code: Launch location code...has to be derived from inspecting the reservation page.
            takeout_code: Takeout location code...has to be derived from inspecting the reservation page.
            permit_pickup_location_code: Code for location where permit will be picked up location code...has to be
              derived from inspecting the reservation page.
        """
        self.permit_id = permit_id
        self.trip_days = trip_days

        # reverse lookup to save river key
        self.permit_key = list(permit_ids.keys())[
            list(permit_ids.values()).index(permit_id)
        ]

        # lookup default location codes if not provided
        if putin_code is None:
            self.putin_code = default_codes.get(self.permit_key)[0]
        else:
            self.putin_code = putin_code

        if takeout_code is None:
            self.takeout_code = default_codes.get(self.permit_key)[1]
        else:
            self.takeout_code = takeout_code

        if permit_pickup_location_code is None:
            self.permit_pickup_location_code = default_codes.get(self.permit_key)[2]
        else:
            self.permit_pickup_location_code = permit_pickup_location_code

    def __repr__(self):
        return f"FourRivers ({self.permit_id})"

    @classmethod
    def _get_river(
        cls,
        river_key: str,
        trip_days: Optional[int] = 7,
        launch_location_code: Optional[Union[str, int]] = None,
        takeout_location_code: Optional[Union[str, int]] = None,
        pickup_permit_location_code: Optional[Union[str, int]] = None,
    ) -> "FourRivers":
        """

        Args:
            river_key: River ID from Recreation.gov
            trip_days: Trip duration in days. Defaults to 7.
            launch_location_code: Launch location code...has to be derived from inspecting the reservation page.
            takeout_location_code: Takeout location code...has to be derived from inspecting the reservation page.
            pickup_permit_location_code: Code for location where permit will be picked up location code...has to be
              derived from inspecting the reservation page.
        """

        # validate key
        if river_key not in permit_ids.keys():
            raise ValueError(
                f"River key {river_key} is not an available river key {permit_ids.keys()}"
            )

        return cls(
            permit_ids[river_key],
            trip_days,
            launch_location_code,
            takeout_location_code,
            pickup_permit_location_code,
        )

    @classmethod
    def get_middle_fork(
        cls,
        trip_days: Optional[int] = 7,
        launch_location_code: Optional[Union[str, int]] = None,
        takeout_location_code: Optional[Union[str, int]] = None,
        pickup_permit_location_code: Optional[Union[str, int]] = None,
    ) -> "FourRivers":
        """

        Args:
            trip_days: Trip duration in days. Defaults to 7.
            launch_location_code: Launch location code...has to be derived from inspecting the reservation page.
            takeout_location_code: Takeout location code...has to be derived from inspecting the reservation page.
            pickup_permit_location_code: Code for location where permit will be picked up location code...has to be
              derived from inspecting the reservation page.
        """
        return cls(
            permit_ids["middle_fork"],
            trip_days,
            launch_location_code,
            takeout_location_code,
            pickup_permit_location_code,
        )

    @classmethod
    def get_main_salmon(
        cls,
        trip_days: Optional[int] = 7,
        launch_location_code: Optional[Union[str, int]] = None,
        takeout_location_code: Optional[Union[str, int]] = None,
        pickup_permit_location_code: Optional[Union[str, int]] = None,
    ) -> "FourRivers":
        """

        Args:
            trip_days: Trip duration in days. Defaults to 7.
            launch_location_code: Launch location code...has to be derived from inspecting the reservation page.
            takeout_location_code: Takeout location code...has to be derived from inspecting the reservation page.
            pickup_permit_location_code: Code for location where permit will be picked up location code...has to be
              derived from inspecting the reservation page.
        """
        river = cls(
            permit_ids["main_salmon"],
            trip_days,
            launch_location_code,
            takeout_location_code,
            pickup_permit_location_code,
        )
        return river

    @classmethod
    def get_hells_canyon(
        cls,
        trip_days: Optional[int] = 7,
        launch_location_code: Optional[Union[str, int]] = None,
        takeout_location_code: Optional[Union[str, int]] = None,
        pickup_permit_location_code: Optional[Union[str, int]] = None,
    ) -> "FourRivers":
        """

        Args:
            trip_days: Trip duration in days. Defaults to 7.
            launch_location_code: Launch location code...has to be derived from inspecting the reservation page.
            takeout_location_code: Takeout location code...has to be derived from inspecting the reservation page.
            pickup_permit_location_code: Code for location where permit will be picked up location code...has to be
              derived from inspecting the reservation page.
        """
        river = cls(
            permit_ids["hells_canyon"],
            trip_days,
            launch_location_code,
            takeout_location_code,
            pickup_permit_location_code,
        )
        return river

    @classmethod
    def get_selway(
        cls,
        trip_days: Optional[int] = 7,
        launch_location_code: Optional[Union[str, int]] = None,
        takeout_location_code: Optional[Union[str, int]] = None,
        pickup_permit_location_code: Optional[Union[str, int]] = None,
    ) -> "FourRivers":
        """

        Args:
            trip_days: Trip duration in days. Defaults to 7.
            launch_location_code: Launch location code...has to be derived from inspecting the reservation page.
            takeout_location_code: Takeout location code...has to be derived from inspecting the reservation page.
            pickup_permit_location_code: Code for location where permit will be picked up location code...has to be
              derived from inspecting the reservation page.
        """
        river = cls(
            permit_ids["selway"],
            trip_days,
            launch_location_code,
            takeout_location_code,
            pickup_permit_location_code,
        )
        return river

    @cache
    def _get_details(self) -> dict:
        """Get details dictionary for river."""
        # create url using reach id
        url = f"https://www.recreation.gov/api/permits/{self.permit_id}/details"

        # make the request
        res = requests.get(url, headers=_headers_dict)

        # handle anything other than what we need
        if res.status_code != 200:
            raise Exception(f"Cannot retrieve details for {self.permit_key}")

        # get json response as dictionary
        return res.json()

    @property
    def _detail_entrances(self):
        """List of entrance dictionaries from details dictionary."""
        # pull entrances out of details
        return self._get_details().get("payload").get("entrances")

    @property
    def putins(self):
        """Dictionary of putin codes and descriptions."""
        # pull entrances out of details
        putin_dict = {
            int(val.get("id")): val.get("name")
            for val in self._detail_entrances
            if val.get("is_entry")
        }
        return putin_dict

    @property
    def takeouts(self):
        """Dictionary of takeout codes and descriptions."""
        takeout_dict = {
            int(val.get("id")): val.get("name")
            for val in self._detail_entrances
            if val.get("is_exit")
        }
        return takeout_dict

    @property
    def permit_pickup_locations(self):
        """Dictionary of permit pickup location codes and descriptions."""
        permit_pickup_dict = {
            int(val.get("id")): val.get("name")
            for val in self._detail_entrances
            if val.get("is_issue_station")
        }
        return permit_pickup_dict

    @cache
    def get_all_month_availability(
        self, month: int, year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get *all* availability for a given month, including unavailable dates.
        """
        return get_4rivers_permit_availability_by_month(
            self.permit_id, month, year, False
        )

    def get_month_availability(
        self, month: int, year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get availability for a given month.

        .. note::

            Only returns available dates. If wanting to get availability, including unavailable dates,
            use :meth:`get_all_month_availability`.

        """
        # get available dates
        avail_df = self.get_all_month_availability(month)

        # filter to just those available
        avail_df = avail_df.loc[avail_df["remaining"] > 0]

        return avail_df

    def check_availability(
        self, day: int, month: int, year: Optional[int] = None
    ) -> bool:
        """Check availability for a specific month and day."""
        avail_df = self.get_month_availability(month)

        # filter the data frame to the specific date
        avail_df = avail_df.loc[
            (avail_df["date"].dt.day == day) & (avail_df["remaining"] > 0)
        ]

        # if the data frame has a record left, the date is available
        avail = avail_df.shape[0] == 1

        return avail

    def get_permit_season_availability(self) -> pd.DataFrame:
        """Get available permits for current year's permit season."""
        # get the start and end dates for the permit season
        start_date, end_date = permit_seasion_dict.get(self.permit_key)

        # get the month range to retrieve
        start_month = start_date.month
        end_month = end_date.month

        # retrieve inclusive dataframe of all availability
        permit_df = pd.concat(
            [
                self.get_all_month_availability(mth)
                for mth in range(start_month, end_month + 1)
            ]
        )

        # filter the dataframe to just the permit controlled season
        permit_df = permit_df.loc[
            (permit_df["date"] >= start_date) & (permit_df["date"] <= end_date)
        ].reset_index(drop=True)

        # add retrieval timestamp and days to launch metrics
        permit_df["retrive_timestamp"] = datetime.now(tz=timezone.utc)
        permit_df["days_to_launch"] = (
            permit_df.date - permit_df.retrive_timestamp
        ).dt.days

        # add the name of the river as well
        permit_df.insert(0, "river", self.permit_key)

        return permit_df

    def reserve_date(
        self,
        day: int,
        month: int,
        year: Optional[int] = None,
        recgov_username: Optional[str] = None,
        recgov_password: Optional[str] = None,
        headless: Optional[bool] = True,
    ) -> bool:
        """Reserve date for the river."""
        # default to this year if not provided
        if year is None:
            year = datetime.now().year

        # check if the date is available
        avail = self.check_availability(day, month)

        if not avail:
            logging.info(
                datetime(year, month, day).strftime("%B %d, %Y")
                + " not available for "
                + self.permit_key
            )

            status = False

        else:
            reserve_4rivers_permit_date(
                permit_id=self.permit_id,
                day=day,
                month=month,
                launch_location_code=self.putin_code,
                takeout_location_code=self.takeout_code,
                pickup_permit_location_code=self.permit_pickup_location_code,
                trip_days=self.trip_days,
                year=year,
                recgov_username=recgov_username,
                recgov_password=recgov_password,
                headless=headless,
            )

            logging.info(
                datetime(year, month, day).strftime("%B %d, %Y")
                + "reserved for "
                + self.permit_key
            )

            status = True

        return status
