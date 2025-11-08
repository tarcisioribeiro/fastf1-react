"""
Client for Jolpica F1 API (Ergast-compatible)
Provides historical F1 data from 1950 onwards.
"""
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from time import sleep

logger = logging.getLogger('data_collector')


class JolpicaF1Client:
    """Client for accessing Jolpica F1 API (Ergast-compatible endpoint)."""

    BASE_URL = "http://api.jolpi.ca/ergast/f1"

    def __init__(self, rate_limit_delay: float = 0.5):
        """
        Initialize Jolpica F1 API client.

        Args:
            rate_limit_delay: Delay in seconds between API requests to avoid rate limiting
        """
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FastF1-Historical-Data-Collector/1.0'
        })

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make HTTP GET request to API with rate limiting.

        Args:
            endpoint: API endpoint path
            params: Optional query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.BASE_URL}/{endpoint}.json"

        try:
            # Rate limiting
            sleep(self.rate_limit_delay)

            logger.debug(f"Requesting: {url} with params: {params}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data.get('MRData', {})

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {url}: {e}")
            raise

    def get_seasons(self) -> List[Dict]:
        """
        Get all available seasons.

        Returns:
            List of season dictionaries with 'season', 'url' fields
        """
        data = self._make_request("seasons", params={'limit': 1000})
        return data.get('SeasonTable', {}).get('Seasons', [])

    def get_races(self, year: int) -> List[Dict]:
        """
        Get all races for a specific season.

        Args:
            year: Season year

        Returns:
            List of race dictionaries
        """
        data = self._make_request(f"{year}")
        return data.get('RaceTable', {}).get('Races', [])

    def get_race_results(self, year: int, round_num: int) -> List[Dict]:
        """
        Get race results for a specific race.

        Args:
            year: Season year
            round_num: Round number

        Returns:
            List of result dictionaries
        """
        data = self._make_request(f"{year}/{round_num}/results")
        races = data.get('RaceTable', {}).get('Races', [])

        if races:
            return races[0].get('Results', [])
        return []

    def get_qualifying_results(self, year: int, round_num: int) -> List[Dict]:
        """
        Get qualifying results for a specific race.

        Args:
            year: Season year
            round_num: Round number

        Returns:
            List of qualifying result dictionaries
        """
        data = self._make_request(f"{year}/{round_num}/qualifying")
        races = data.get('RaceTable', {}).get('Races', [])

        if races:
            return races[0].get('QualifyingResults', [])
        return []

    def get_sprint_results(self, year: int, round_num: int) -> List[Dict]:
        """
        Get sprint race results for a specific race.
        Note: Sprints only exist from 2021 onwards.

        Args:
            year: Season year
            round_num: Round number

        Returns:
            List of sprint result dictionaries
        """
        data = self._make_request(f"{year}/{round_num}/sprint")
        races = data.get('RaceTable', {}).get('Races', [])

        if races:
            return races[0].get('SprintResults', [])
        return []

    def get_driver_standings(self, year: int, round_num: Optional[int] = None) -> List[Dict]:
        """
        Get driver standings for a season or after a specific round.

        Args:
            year: Season year
            round_num: Optional round number (if None, gets final standings)

        Returns:
            List of driver standing dictionaries
        """
        endpoint = f"{year}/driverStandings"
        if round_num:
            endpoint = f"{year}/{round_num}/driverStandings"

        data = self._make_request(endpoint)
        standings_lists = data.get('StandingsTable', {}).get('StandingsLists', [])

        if standings_lists:
            return standings_lists[0].get('DriverStandings', [])
        return []

    def get_constructor_standings(self, year: int, round_num: Optional[int] = None) -> List[Dict]:
        """
        Get constructor standings for a season or after a specific round.

        Args:
            year: Season year
            round_num: Optional round number (if None, gets final standings)

        Returns:
            List of constructor standing dictionaries
        """
        endpoint = f"{year}/constructorStandings"
        if round_num:
            endpoint = f"{year}/{round_num}/constructorStandings"

        data = self._make_request(endpoint)
        standings_lists = data.get('StandingsTable', {}).get('StandingsLists', [])

        if standings_lists:
            return standings_lists[0].get('ConstructorStandings', [])
        return []

    def get_lap_times(self, year: int, round_num: int, lap_num: Optional[int] = None) -> List[Dict]:
        """
        Get lap times for a specific race.
        Note: Lap times are only available from 1996 onwards and may be incomplete.

        Args:
            year: Season year
            round_num: Round number
            lap_num: Optional specific lap number

        Returns:
            List of lap time dictionaries
        """
        endpoint = f"{year}/{round_num}/laps"
        if lap_num:
            endpoint = f"{year}/{round_num}/laps/{lap_num}"

        data = self._make_request(endpoint)
        races = data.get('RaceTable', {}).get('Races', [])

        if races:
            return races[0].get('Laps', [])
        return []

    def get_pit_stops(self, year: int, round_num: int) -> List[Dict]:
        """
        Get pit stop data for a specific race.
        Note: Pit stop data is only available from 2012 onwards.

        Args:
            year: Season year
            round_num: Round number

        Returns:
            List of pit stop dictionaries
        """
        data = self._make_request(f"{year}/{round_num}/pitstops")
        races = data.get('RaceTable', {}).get('Races', [])

        if races:
            return races[0].get('PitStops', [])
        return []

    def get_circuits(self) -> List[Dict]:
        """
        Get all circuits.

        Returns:
            List of circuit dictionaries
        """
        data = self._make_request("circuits", params={'limit': 1000})
        return data.get('CircuitTable', {}).get('Circuits', [])

    def get_drivers(self, year: Optional[int] = None) -> List[Dict]:
        """
        Get all drivers, optionally filtered by season.

        Args:
            year: Optional season year to filter drivers

        Returns:
            List of driver dictionaries
        """
        endpoint = "drivers"
        if year:
            endpoint = f"{year}/drivers"

        data = self._make_request(endpoint, params={'limit': 1000})
        return data.get('DriverTable', {}).get('Drivers', [])

    def get_constructors(self, year: Optional[int] = None) -> List[Dict]:
        """
        Get all constructors, optionally filtered by season.

        Args:
            year: Optional season year to filter constructors

        Returns:
            List of constructor dictionaries
        """
        endpoint = "constructors"
        if year:
            endpoint = f"{year}/constructors"

        data = self._make_request(endpoint, params={'limit': 1000})
        return data.get('ConstructorTable', {}).get('Constructors', [])


def parse_time_string(time_str: str) -> Optional[timedelta]:
    """
    Parse time string from API to timedelta.

    Formats supported:
    - "1:23:45.678" (hours:minutes:seconds.milliseconds)
    - "23:45.678" (minutes:seconds.milliseconds)
    - "45.678" (seconds.milliseconds)
    - "+1.234" (gap in seconds)

    Args:
        time_str: Time string from API

    Returns:
        timedelta object or None if parsing fails
    """
    if not time_str:
        return None

    try:
        # Remove '+' prefix if present (indicates gap)
        time_str = time_str.lstrip('+')

        parts = time_str.split(':')

        if len(parts) == 3:
            # Format: H:MM:SS.mmm
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_parts = parts[2].split('.')
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        elif len(parts) == 2:
            # Format: MM:SS.mmm
            hours = 0
            minutes = int(parts[0])
            seconds_parts = parts[1].split('.')
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        else:
            # Format: SS.mmm or just milliseconds
            hours = 0
            minutes = 0
            seconds_parts = time_str.split('.')
            seconds = int(float(seconds_parts[0]))
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

        return timedelta(
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            milliseconds=milliseconds
        )
    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to parse time string '{time_str}': {e}")
        return None


def parse_millis_to_timedelta(millis: Any) -> Optional[timedelta]:
    """
    Convert milliseconds (int or string) to timedelta.

    Args:
        millis: Milliseconds value

    Returns:
        timedelta object or None if conversion fails
    """
    if not millis:
        return None

    try:
        millis_int = int(millis)
        return timedelta(milliseconds=millis_int)
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse milliseconds '{millis}': {e}")
        return None
