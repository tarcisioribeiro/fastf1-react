"""
Multi-Source Data Scraper for Historical F1 Data (1950-2017).

This module provides a unified interface to fetch F1 data from multiple reliable sources.
It implements a cascading fallback system: if one source fails, it tries the next one.

Supported Sources (in priority order):
1. Ergast/Jolpica API - Most reliable and structured
2. StatsF1.com - Comprehensive historical data
3. RaceFans.net - Good for recent historical data
4. Wikipedia - Fallback for basic information
5. GrandPrix.com - Additional historical source
6. Formula1.com - Official but limited historical data

Author: Claude Code
Date: 2025
"""
import logging
import time
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger('data_collector')


class BaseDataSource:
    """Base class for all data sources."""

    def __init__(self, name: str, base_url: str, rate_limit: float = 1.0):
        """
        Initialize data source.

        Args:
            name: Source name for logging
            base_url: Base URL for the source
            rate_limit: Minimum seconds between requests
        """
        self.name = name
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.consecutive_failures = 0
        self.max_failures_before_circuit_break = 5

        # Create session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; FastF1DataCollector/1.0; +https://github.com/fastf1)'
        })

    def _wait_rate_limit(self):
        """Apply rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, url: str, params: Optional[Dict] = None, timeout: int = 30) -> Optional[requests.Response]:
        """
        Make HTTP request with rate limiting and error handling.

        Args:
            url: URL to fetch
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            Response object or None if failed
        """
        if self.consecutive_failures >= self.max_failures_before_circuit_break:
            logger.warning(f"{self.name} circuit breaker active - skipping request")
            return None

        self._wait_rate_limit()

        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()

            # Success - reset failure counter
            self.consecutive_failures = 0
            return response

        except requests.exceptions.RequestException as e:
            self.consecutive_failures += 1
            logger.warning(f"{self.name} request failed ({self.consecutive_failures}/{self.max_failures_before_circuit_break}): {e}")

            if self.consecutive_failures >= self.max_failures_before_circuit_break:
                logger.error(f"{self.name} circuit breaker activated after {self.consecutive_failures} failures")

            return None

    def is_available(self) -> bool:
        """Check if source is available (circuit breaker not tripped)."""
        return self.consecutive_failures < self.max_failures_before_circuit_break

    def reset_circuit_breaker(self):
        """Reset circuit breaker after successful operations."""
        if self.consecutive_failures > 0:
            logger.info(f"{self.name} circuit breaker reset")
            self.consecutive_failures = 0


class ErgastJolpicaSource(BaseDataSource):
    """
    Ergast/Jolpica API source.
    Most reliable structured data source for historical F1 data.

    API Docs: https://ergast.com/mrd/
    Jolpica Mirror: http://api.jolpi.ca/ergast/
    """

    def __init__(self):
        super().__init__(
            name="Ergast/Jolpica",
            base_url="http://api.jolpi.ca/ergast/f1",
            rate_limit=0.5  # Conservative rate limit
        )

    def get_season_races(self, year: int) -> Optional[List[Dict]]:
        """Get all races for a season."""
        logger.info(f"{self.name}: Fetching races for {year}")

        response = self._make_request(f"{self.base_url}/{year}.json")
        if not response:
            return None

        try:
            data = response.json()
            races = data['MRData']['RaceTable']['Races']
            logger.info(f"{self.name}: Found {len(races)} races for {year}")
            return races
        except (KeyError, ValueError) as e:
            logger.error(f"{self.name}: Error parsing season races: {e}")
            return None

    def get_race_results(self, year: int, round_num: int) -> Optional[Dict]:
        """Get race results."""
        logger.debug(f"{self.name}: Fetching race results {year} R{round_num}")

        response = self._make_request(f"{self.base_url}/{year}/{round_num}/results.json")
        if not response:
            return None

        try:
            data = response.json()
            races = data['MRData']['RaceTable']['Races']
            if races:
                return races[0]
            return None
        except (KeyError, ValueError, IndexError) as e:
            logger.error(f"{self.name}: Error parsing race results: {e}")
            return None

    def get_qualifying_results(self, year: int, round_num: int) -> Optional[Dict]:
        """Get qualifying results."""
        logger.debug(f"{self.name}: Fetching qualifying results {year} R{round_num}")

        response = self._make_request(f"{self.base_url}/{year}/{round_num}/qualifying.json")
        if not response:
            return None

        try:
            data = response.json()
            races = data['MRData']['RaceTable']['Races']
            if races:
                return races[0]
            return None
        except (KeyError, ValueError, IndexError) as e:
            logger.error(f"{self.name}: Error parsing qualifying results: {e}")
            return None

    def get_driver_standings(self, year: int, round_num: Optional[int] = None) -> Optional[List[Dict]]:
        """Get driver standings."""
        endpoint = f"{year}/driverStandings" if not round_num else f"{year}/{round_num}/driverStandings"
        logger.debug(f"{self.name}: Fetching driver standings {endpoint}")

        response = self._make_request(f"{self.base_url}/{endpoint}.json")
        if not response:
            return None

        try:
            data = response.json()
            standings_lists = data['MRData']['StandingsTable']['StandingsLists']
            if standings_lists:
                return standings_lists[0]['DriverStandings']
            return None
        except (KeyError, ValueError, IndexError) as e:
            logger.error(f"{self.name}: Error parsing driver standings: {e}")
            return None

    def get_constructor_standings(self, year: int, round_num: Optional[int] = None) -> Optional[List[Dict]]:
        """Get constructor standings."""
        endpoint = f"{year}/constructorStandings" if not round_num else f"{year}/{round_num}/constructorStandings"
        logger.debug(f"{self.name}: Fetching constructor standings {endpoint}")

        response = self._make_request(f"{self.base_url}/{endpoint}.json")
        if not response:
            return None

        try:
            data = response.json()
            standings_lists = data['MRData']['StandingsTable']['StandingsLists']
            if standings_lists:
                return standings_lists[0]['ConstructorStandings']
            return None
        except (KeyError, ValueError, IndexError) as e:
            logger.error(f"{self.name}: Error parsing constructor standings: {e}")
            return None


class StatsF1Source(BaseDataSource):
    """
    StatsF1.com source.
    Comprehensive historical F1 database with data from 1950 onwards.

    Website: https://www.statsf1.com/
    """

    def __init__(self):
        super().__init__(
            name="StatsF1",
            base_url="https://www.statsf1.com",
            rate_limit=2.0  # Conservative - 1 request per 2 seconds
        )

    def get_season_races(self, year: int) -> Optional[List[Dict]]:
        """
        Get all races for a season by scraping StatsF1.

        Returns list of races with basic info.
        """
        logger.info(f"{self.name}: Fetching races for {year}")

        # StatsF1 uses language-specific URLs
        # Format: https://www.statsf1.com/en/{year}.aspx
        url = f"{self.base_url}/en/{year}.aspx"
        response = self._make_request(url)

        if not response:
            return None

        try:
            soup = BeautifulSoup(response.content, 'html.parser')

            # StatsF1 has a table with all races
            # Find the main results table
            table = soup.find('table', {'class': 'datatable'})
            if not table:
                logger.warning(f"{self.name}: Could not find races table for {year}")
                return None

            races = []
            rows = table.find_all('tr')[1:]  # Skip header

            for idx, row in enumerate(rows, 1):
                cols = row.find_all('td')
                if len(cols) >= 3:
                    # Extract race name and date
                    race_link = cols[1].find('a')
                    if race_link:
                        race_name = race_link.text.strip()
                        race_url = race_link.get('href', '')

                        # Extract date if available
                        date_text = cols[2].text.strip() if len(cols) > 2 else ''

                        races.append({
                            'round': idx,
                            'raceName': race_name,
                            'url': f"{self.base_url}{race_url}" if race_url.startswith('/') else race_url,
                            'date': date_text,
                            'source': self.name
                        })

            logger.info(f"{self.name}: Found {len(races)} races for {year}")
            return races if races else None

        except Exception as e:
            logger.error(f"{self.name}: Error scraping season races: {e}")
            return None

    def get_race_results(self, year: int, round_num: int) -> Optional[Dict]:
        """
        Get race results by scraping StatsF1.
        Returns results in Ergast-compatible format.
        """
        logger.debug(f"{self.name}: Fetching race results {year} R{round_num}")

        # StatsF1 URL format: /en/{year}/{race-slug}.aspx
        # We need to construct this - for now, return None as it requires more complex scraping
        # TODO: Implement full StatsF1 scraping
        return None


class RaceFansSource(BaseDataSource):
    """
    RaceFans.net (formerly F1Fanatic) source.
    Good for recent historical data and race reports.

    Website: https://www.racefans.net/
    """

    def __init__(self):
        super().__init__(
            name="RaceFans",
            base_url="https://www.racefans.net",
            rate_limit=2.0
        )

    def get_season_races(self, year: int) -> Optional[List[Dict]]:
        """
        Get season races from RaceFans.
        Note: RaceFans has good coverage from ~2007 onwards.
        """
        logger.info(f"{self.name}: Fetching races for {year}")

        # RaceFans season page format
        url = f"{self.base_url}/f1-information/f1-race-schedule/{year}/"
        response = self._make_request(url)

        if not response:
            return None

        try:
            soup = BeautifulSoup(response.content, 'html.parser')

            # RaceFans uses article lists for race schedules
            # Find race articles
            articles = soup.find_all('article', {'class': 'post'})

            races = []
            for idx, article in enumerate(articles, 1):
                title_elem = article.find('h2', {'class': 'entry-title'})
                if title_elem:
                    race_link = title_elem.find('a')
                    if race_link:
                        race_name = race_link.text.strip()
                        race_url = race_link.get('href', '')

                        races.append({
                            'round': idx,
                            'raceName': race_name,
                            'url': race_url,
                            'source': self.name
                        })

            logger.info(f"{self.name}: Found {len(races)} races for {year}")
            return races if races else None

        except Exception as e:
            logger.error(f"{self.name}: Error scraping season races: {e}")
            return None


class WikipediaF1Source(BaseDataSource):
    """
    Wikipedia source for F1 data.
    Reliable for basic information but requires parsing.

    Uses Wikipedia API and scraping.
    """

    def __init__(self):
        super().__init__(
            name="Wikipedia",
            base_url="https://en.wikipedia.org",
            rate_limit=1.0
        )
        self.api_url = "https://en.wikipedia.org/w/api.php"

    def get_season_races(self, year: int) -> Optional[List[Dict]]:
        """
        Get season races from Wikipedia.
        Wikipedia has good F1 season pages.
        """
        logger.info(f"{self.name}: Fetching races for {year}")

        # Wikipedia season page format
        page_title = f"{year}_Formula_One_World_Championship"

        # Use Wikipedia API to get page content
        params = {
            'action': 'parse',
            'page': page_title,
            'format': 'json',
            'prop': 'text'
        }

        response = self._make_request(self.api_url, params=params)
        if not response:
            return None

        try:
            data = response.json()
            html_content = data['parse']['text']['*']

            soup = BeautifulSoup(html_content, 'html.parser')

            # Wikipedia has a "Races" section with a table
            # Find the calendar/races table
            tables = soup.find_all('table', {'class': 'wikitable'})

            races = []
            for table in tables:
                # Look for table headers that indicate it's a race calendar
                headers = table.find_all('th')
                header_text = ' '.join([h.text.strip().lower() for h in headers])

                if 'round' in header_text or 'grand prix' in header_text:
                    rows = table.find_all('tr')[1:]  # Skip header

                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 3:
                            # Extract round, race name, date
                            round_num = cols[0].text.strip()
                            race_name = cols[1].text.strip()

                            # Find race link
                            race_link = cols[1].find('a')
                            race_url = ''
                            if race_link:
                                race_url = f"{self.base_url}{race_link.get('href', '')}"

                            # Extract date
                            date_col = cols[2] if len(cols) > 2 else None
                            date_text = date_col.text.strip() if date_col else ''

                            try:
                                round_int = int(round_num)
                            except ValueError:
                                continue

                            races.append({
                                'round': round_int,
                                'raceName': race_name,
                                'url': race_url,
                                'date': date_text,
                                'source': self.name
                            })

                    if races:
                        break  # Found the races table

            logger.info(f"{self.name}: Found {len(races)} races for {year}")
            return races if races else None

        except Exception as e:
            logger.error(f"{self.name}: Error parsing Wikipedia season page: {e}")
            return None


class GrandPrixSource(BaseDataSource):
    """
    GrandPrix.com source.
    Historical F1 database.

    Website: https://www.grandprix.com/
    """

    def __init__(self):
        super().__init__(
            name="GrandPrix.com",
            base_url="https://www.grandprix.com",
            rate_limit=2.0
        )

    def get_season_races(self, year: int) -> Optional[List[Dict]]:
        """Get season races from GrandPrix.com."""
        logger.info(f"{self.name}: Fetching races for {year}")

        # GrandPrix.com has race archives
        # Format varies - would need to implement specific scraping
        # TODO: Implement GrandPrix.com scraping
        return None


class MultiSourceDataFetcher:
    """
    Unified interface to fetch F1 data from multiple sources.
    Implements cascading fallback: tries sources in priority order.
    """

    def __init__(self):
        """Initialize all data sources in priority order."""
        self.sources = [
            ErgastJolpicaSource(),      # Most reliable
            WikipediaF1Source(),         # Good fallback
            StatsF1Source(),             # Comprehensive but requires scraping
            RaceFansSource(),            # Recent data
            # GrandPrixSource(),         # Additional source (not fully implemented)
        ]

        logger.info(f"MultiSourceDataFetcher initialized with {len(self.sources)} sources")

    def get_season_races(self, year: int) -> Optional[Dict[str, Any]]:
        """
        Get season races from the first available source.

        Args:
            year: Season year

        Returns:
            Dict with 'data' (list of races) and 'source' (source name), or None
        """
        logger.info(f"Fetching season races for {year} from multiple sources")

        for source in self.sources:
            if not source.is_available():
                logger.info(f"Skipping {source.name} (circuit breaker active)")
                continue

            try:
                races = source.get_season_races(year)
                if races:
                    logger.info(f"Successfully fetched {len(races)} races from {source.name}")
                    return {
                        'data': races,
                        'source': source.name,
                        'year': year
                    }
                else:
                    logger.info(f"{source.name} returned no races for {year}")

            except Exception as e:
                logger.error(f"Error fetching from {source.name}: {e}", exc_info=True)
                continue

        logger.warning(f"Failed to fetch season races for {year} from all sources")
        return None

    def get_race_results(self, year: int, round_num: int) -> Optional[Dict[str, Any]]:
        """Get race results from the first available source."""
        logger.info(f"Fetching race results for {year} R{round_num} from multiple sources")

        for source in self.sources:
            if not source.is_available():
                continue

            try:
                # Only try sources that implement race results
                if hasattr(source, 'get_race_results'):
                    results = source.get_race_results(year, round_num)
                    if results:
                        logger.info(f"Successfully fetched race results from {source.name}")
                        return {
                            'data': results,
                            'source': source.name,
                            'year': year,
                            'round': round_num
                        }
            except Exception as e:
                logger.error(f"Error fetching race results from {source.name}: {e}")
                continue

        logger.warning(f"Failed to fetch race results for {year} R{round_num} from all sources")
        return None

    def get_qualifying_results(self, year: int, round_num: int) -> Optional[Dict[str, Any]]:
        """Get qualifying results from the first available source."""
        logger.info(f"Fetching qualifying results for {year} R{round_num} from multiple sources")

        for source in self.sources:
            if not source.is_available():
                continue

            try:
                if hasattr(source, 'get_qualifying_results'):
                    results = source.get_qualifying_results(year, round_num)
                    if results:
                        logger.info(f"Successfully fetched qualifying results from {source.name}")
                        return {
                            'data': results,
                            'source': source.name,
                            'year': year,
                            'round': round_num
                        }
            except Exception as e:
                logger.error(f"Error fetching qualifying results from {source.name}: {e}")
                continue

        logger.warning(f"Failed to fetch qualifying results for {year} R{round_num} from all sources")
        return None

    def get_driver_standings(self, year: int, round_num: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get driver standings from the first available source."""
        logger.info(f"Fetching driver standings for {year}" + (f" R{round_num}" if round_num else ""))

        for source in self.sources:
            if not source.is_available():
                continue

            try:
                if hasattr(source, 'get_driver_standings'):
                    standings = source.get_driver_standings(year, round_num)
                    if standings:
                        logger.info(f"Successfully fetched driver standings from {source.name}")
                        return {
                            'data': standings,
                            'source': source.name,
                            'year': year,
                            'round': round_num
                        }
            except Exception as e:
                logger.error(f"Error fetching driver standings from {source.name}: {e}")
                continue

        logger.warning(f"Failed to fetch driver standings for {year} from all sources")
        return None

    def get_constructor_standings(self, year: int, round_num: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get constructor standings from the first available source."""
        logger.info(f"Fetching constructor standings for {year}" + (f" R{round_num}" if round_num else ""))

        for source in self.sources:
            if not source.is_available():
                continue

            try:
                if hasattr(source, 'get_constructor_standings'):
                    standings = source.get_constructor_standings(year, round_num)
                    if standings:
                        logger.info(f"Successfully fetched constructor standings from {source.name}")
                        return {
                            'data': standings,
                            'source': source.name,
                            'year': year,
                            'round': round_num
                        }
            except Exception as e:
                logger.error(f"Error fetching constructor standings from {source.name}: {e}")
                continue

        logger.warning(f"Failed to fetch constructor standings for {year} from all sources")
        return None


# Global instance
multi_source_fetcher = MultiSourceDataFetcher()
