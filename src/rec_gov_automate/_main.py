import logging
from datetime import date, datetime, timezone
from functools import cache, cached_property
import  math
from multiprocessing import Pool, Manager
import time
from typing import Optional, Union

import pandas as pd
import requests
from dateutil.relativedelta import FR, relativedelta

from .utils import availability
from .utils import reserve

__all__ = ["FourRivers", "get_fourrivers_availability"]

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
        # 20Jun - 03Sep
        pd.to_datetime(f"{current_year}-06-20", utc=True),
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
        trip_days: Optional[int] = None,
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

        # reverse lookup to save river key
        self.permit_key = list(permit_ids.keys())[
            list(permit_ids.values()).index(permit_id)
        ]

        # initially set to just input parameters...will lookup properties if necessary later...speeds up initialization
        self._trip_days = trip_days
        self._putin_code = putin_code
        self._takeout_code = takeout_code
        self._permit_pickup_location_code = permit_pickup_location_code

    @cached_property
    def trip_days(self) -> int:
        """Trip duration in days."""
        if self._trip_days is None or math.isnan(self._trip_days):
            self._trip_days = 7
        return self._trip_days

    @cached_property
    def putin_code(self) -> int:
        """Code to use for selecting the putin location."""
        if self._putin_code is None or math.isnan(self._putin_code):
            self._putin_code = default_codes.get(self.permit_key)[0]
        return self._putin_code

    @cached_property
    def takeout_code(self) -> int:
        """Code to suse for selecting the takeout location."""
        if self._takeout_code is None or math.isnan(self._takeout_code):
            self._takeout_code = default_codes.get(self.permit_key)[1]
        return self._takeout_code

    @cached_property
    def permit_pickup_location_code(self) -> int:
        if self._permit_pickup_location_code is None or math.isnan(self._permit_pickup_location_code):
            self._permit_pickup_location_code = default_codes.get(self.permit_key)[2]
        return self._permit_pickup_location_code

    def __repr__(self):
        return f"FourRivers - {self.permit_key} ({self.permit_id})"

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
        res = requests.get(url, headers=availability._headers_dict)

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
        return availability.get_4rivers_permit_availability_by_month(
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
        avail_df = self.get_all_month_availability(month, year)

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
            (avail_df["launch_date"].dt.day == day) & (avail_df["remaining"] > 0)
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
            (permit_df["launch_date"] >= start_date)
            & (permit_df["launch_date"] <= end_date)
        ].reset_index(drop=True)

        # add retrieval timestamp and days to launch metrics
        permit_df["retrieve_timestamp"] = datetime.now(tz=timezone.utc)
        permit_df["days_to_launch"] = (
            permit_df.launch_date - permit_df.retrieve_timestamp
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

        # variable to set if successful
        success_flag = False

        if not avail:
            logging.debug(
                datetime(year, month, day).strftime("%B %d, %Y")
                + " not available for "
                + self.permit_key
            )

        else:
            # make a couple of attempts to make reservation
            attempt_cnt = 0
            while attempt_cnt < 3 and not success_flag:
                try:
                    avail_status = reserve.reserve_4rivers_permit_date(
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

                    # if available, set status
                    if avail_status:
                        success_flag = True

                        logging.info(
                            datetime(year, month, day).strftime("%B %d, %Y")
                            + "reserved for "
                            + self.permit_key
                        )

                    # if not available, break out of retry loop
                    else:
                        break

                except Exception as e:
                    attempt_cnt += 1

        return success_flag

    def reserve_date_parallel(
        self,
        day: int,
        month: int,
        year: Optional[int] = None,
        recgov_username: Optional[str] = None,
        recgov_password: Optional[str] = None,
        headless: Optional[bool] = True,
        max_duration: float = 300.0,
        num_workers: int = 20,
        stagger_delay: float = 0.1,
    ) -> bool:
        """
        Reserve date for the river using parallel processes.

        This function spawns multiple concurrent processes attempting to reserve a permit.
        Processes start with a staggered delay and continue recycling until one succeeds
        or the maximum duration is reached.

        Args:
            day: Day of the month for launch date.
            month: Month for launch date.
            year: Year for launch date. Defaults to current year.
            recgov_username: Recreation.gov username for authentication.
            recgov_password: Recreation.gov password for authentication.
            headless: Run browser in headless mode. Defaults to True.
            max_duration: Maximum time in seconds to continue attempting. Defaults to 300.0 (5 minutes).
            num_workers: Number of concurrent worker processes. Defaults to 20.
            stagger_delay: Delay in seconds between starting each worker. Defaults to 0.1.

        Returns:
            bool: True if a permit was successfully reserved, False otherwise.

        !!! warning
            This function spawns multiple browser instances concurrently which may consume
            significant system resources. Adjust `num_workers` based on your system capabilities.

        ```python
        # Example usage
        rvr = FourRivers._get_river('middle_fork')
        success = rvr.reserve_date_parallel(
            day=15,
            month=7,
            year=2026,
            recgov_username='user@example.com',
            recgov_password='password123',
            max_duration=600.0  # 10 minutes
        )
        ```
        """
        # Default to this year if not provided
        if year is None:
            year = datetime.now().year

        # Check if the date is available first
        avail = self.check_availability(day, month)
        if not avail:
            logging.debug(
                datetime(year, month, day).strftime("%B %d, %Y")
                + " not available for "
                + self.permit_key
            )
            return False

        logging.info(
            f"Starting parallel reservation attempts for {datetime(year, month, day).strftime('%B %d, %Y')} "
            f"on {self.permit_key} with {num_workers} workers for up to {max_duration} seconds"
        )

        # Create a manager for shared state
        manager = Manager()
        success_flag = manager.Value('b', False)
        
        # Create a wrapper function for multiprocessing
        def _reserve_wrapper(args):
            """Wrapper function that can be pickled for multiprocessing."""
            worker_id, shared_success = args
            
            # Check if another process already succeeded
            if shared_success.value:
                return False
            
            try:
                result = reserve.reserve_4rivers_permit_date(
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
                
                # If successful, update shared flag
                if result and not shared_success.value:
                    shared_success.value = True
                    logging.info(
                        f"Worker {worker_id}: Successfully reserved "
                        f"{datetime(year, month, day).strftime('%B %d, %Y')} for {self.permit_key}"
                    )
                
                return result
                
            except Exception as e:
                logging.debug(f"Worker {worker_id}: Exception occurred - {str(e)}")
                return False

        start_time = time.time()
        worker_count = 0
        active_jobs = []
        
        # Create process pool
        with Pool(processes=num_workers) as pool:
            try:
                # Main loop: keep spawning workers until success or timeout
                while not success_flag.value and (time.time() - start_time) < max_duration:
                    
                    # Clean up completed jobs
                    active_jobs = [job for job in active_jobs if not job.ready()]
                    
                    # Spawn new workers to maintain pool size
                    while len(active_jobs) < num_workers and not success_flag.value:
                        worker_count += 1
                        job = pool.apply_async(_reserve_wrapper, ((worker_count, success_flag),))
                        active_jobs.append(job)
                        logging.debug(f"Spawned worker {worker_count}")
                        
                        # Stagger the starts
                        time.sleep(stagger_delay)
                    
                    # Brief sleep to avoid busy waiting
                    time.sleep(0.05)
                    
                    # Check if any job succeeded
                    for job in active_jobs:
                        if job.ready():
                            try:
                                if job.get(timeout=0):
                                    success_flag.value = True
                                    break
                            except Exception:
                                pass
                
                # Terminate all remaining jobs
                pool.terminate()
                pool.join()
                
            except KeyboardInterrupt:
                logging.info("Parallel reservation interrupted by user")
                pool.terminate()
                pool.join()
                return False

        elapsed_time = time.time() - start_time
        
        if success_flag.value:
            logging.info(
                f"Successfully reserved {datetime(year, month, day).strftime('%B %d, %Y')} "
                f"for {self.permit_key} after {elapsed_time:.2f} seconds with {worker_count} total attempts"
            )
        else:
            logging.info(
                f"Failed to reserve {datetime(year, month, day).strftime('%B %d, %Y')} "
                f"for {self.permit_key} after {elapsed_time:.2f} seconds with {worker_count} total attempts"
            )
        
        return success_flag.value


def get_fourrivers_availability(
    permit_season: bool = False,
    only_available: bool = False,
    year: Optional[int] = None,
    search_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Helper to retrieve all dates for four rivers availability.

    Args:
        permit_season: Filter to just the permit controlled season dates. (default: ``False``)
        only_available: Filter to just dates with available permits. (default: ``False``)
        year: Filter to only include dates for specific year. (default: current year)
        search_df: Search dataframe formatted to use for searching for available dates. (default: ``None``)
    """
    # if a search data frame is provided, only get dates and rivers being requested
    if isinstance(search_df, pd.DataFrame):

        # add current year to search dataframe if not already provided
        if "year" not in search_df.columns:
            search_df["year"] = date.today().year

        # if year in dataframe, ensure values are populated
        else:
            search_df["year"].fillna(date.today().year, inplace=True)

        # get unique river, year and month combinations
        query_df = search_df[["river_key", "year", "month"]].drop_duplicates()

        # variable for river instance
        rvr: FourRivers = None

        # iterate the rivers, years and months to only make the minimum requests to the website
        for idx, river_key, year, month in query_df.itertuples():

            # create river instance if a new river
            if getattr(rvr, "river_key", "NaN") != river_key:
                rvr = FourRivers._get_river(river_key)

            # retrieve the data frame
            tmp_df = rvr.get_all_month_availability(month, year)

            # add the river key to the schema
            tmp_df.insert(0, "river", river_key)

            # if the first pass, assign to output
            if idx == 0:
                avail_df = tmp_df

            # add for remaining months
            else:
                avail_df = pd.concat([avail_df, tmp_df], ignore_index=True)

    # if only retrieving during the permit season
    elif permit_season:
        avail_df = pd.concat(
            [
                FourRivers(permit_id).get_permit_season_availability()
                for permit_id in permit_ids.values()
            ]
        ).reset_index(drop=True)

    else:
        # if not provided, get the current year
        year = date.today().year if year is None else year

        # iterate the four rivers' permit ids and create a full availability data frame for each
        for idx, permit_id in enumerate(permit_ids.values()):

            # instantiate the object instance
            rvr = FourRivers(permit_id)

            # get the data for the river
            tmp_df = pd.concat(
                (rvr.get_all_month_availability(month, year) for month in range(1, 13))
            )

            # add the river key onto the data frame
            tmp_df.insert(0, "river", rvr.permit_key)

            # if the first pass, set the data frame to the final variable
            if idx == 0:
                avail_df = tmp_df.copy(deep=True)
            else:
                avail_df = pd.concat([avail_df, tmp_df], ignore_index=True)

    # if a valid search dataframe is provided, use it
    if isinstance(search_df, pd.DataFrame):

        # add the date column to the search dataframe
        search_df["launch_date"] = pd.to_datetime(
            search_df[["year", "month", "day"]], utc=True
        )

        # remove extra date columns
        search_df.drop(columns=["year", "month", "day"], inplace=True)

        # rename river key to make the table join easier
        avail_df.rename(columns={"river": "river_key"}, inplace=True)

        # remove unneeded columns
        avail_df.drop(
            columns=["show_walkup", "is_secret_quota"], inplace=True, errors="ignore"
        )

        # combine the data frames to get just available dates to try and reserve
        avail_df = search_df.merge(avail_df, on=["river_key", "launch_date"], how="left")

        # rename river key for consistency with other outputs
        avail_df.rename(columns={'river_key': 'river'}, inplace=True)

    # if only retrieving available dates or searching for specific availability, filter to just these
    if only_available or isinstance(search_df, pd.DataFrame):
        avail_df = avail_df.loc[avail_df["remaining"] > 0]

    # clean up the index
    avail_df.reset_index(drop=True, inplace=True)

    return avail_df
