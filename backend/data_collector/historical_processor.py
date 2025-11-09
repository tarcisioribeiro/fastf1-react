"""
Historical F1 data processor.
Ingests historical F1 data from Jolpica API (1950-2017) into Django models.
"""
import logging
from datetime import datetime, date
from typing import Optional, Dict, List, Tuple
from django.utils import timezone
from django.db import transaction

from core.models import (
    Season, Event, Session, Driver, Team, Circuit,
    RaceResult, QualifyingResult, SprintResult,
    DriverStanding, ConstructorStanding,
    LapTime, PitStop
)
from .jolpica_client import (
    JolpicaF1Client,
    parse_time_string,
    parse_millis_to_timedelta
)

logger = logging.getLogger('data_collector')


class HistoricalDataProcessor:
    """Processes historical F1 data from Jolpica API into Django models."""

    def __init__(self):
        """Initialize processor with Jolpica API client."""
        self.client = JolpicaF1Client(rate_limit_delay=0.5)

    def _safe_int(self, value, default=None):
        """Safely convert value to int."""
        try:
            return int(value) if value else default
        except (ValueError, TypeError):
            return default

    def _safe_float(self, value, default=None):
        """Safely convert value to float."""
        try:
            return float(value) if value else default
        except (ValueError, TypeError):
            return default

    def _safe_date(self, date_str: str) -> Optional[date]:
        """Safely parse date string to date object."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            logger.warning(f"Failed to parse date: {date_str}")
            return None

    def _safe_datetime(self, date_str: str, time_str: str = None) -> Optional[datetime]:
        """Safely parse date and time strings to datetime object."""
        if not date_str:
            return None

        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')

            if time_str:
                # Try to parse time
                try:
                    time_obj = datetime.strptime(time_str, '%H:%M:%SZ').time()
                    dt = datetime.combine(dt.date(), time_obj)
                except ValueError:
                    pass  # Use date only

            # Make timezone-aware
            return timezone.make_aware(dt, timezone.get_current_timezone())
        except ValueError as e:
            logger.warning(f"Failed to parse datetime: {date_str} {time_str}: {e}")
            return None

    def process_driver(self, driver_data: Dict) -> Driver:
        """
        Process and create/update Driver from API data.

        Args:
            driver_data: Driver dictionary from API

        Returns:
            Driver model instance
        """
        driver_id = driver_data.get('driverId', '').lower()

        # Extract driver code (3-letter abbreviation)
        # API doesn't provide this, so we'll generate from last name
        last_name = driver_data.get('familyName', '')
        code = driver_data.get('code', last_name[:3].upper() if last_name else 'UNK')

        # Get driver number - not available in historical data, use 0 as placeholder
        number = self._safe_int(driver_data.get('permanentNumber'), 0)
        if number == 0:
            # Generate a placeholder number based on driver_id hash
            number = abs(hash(driver_id)) % 99 + 1

        driver, created = Driver.objects.update_or_create(
            driver_id=driver_id,
            defaults={
                'code': code[:3],  # Ensure 3 characters max
                'number': number,
                'first_name': driver_data.get('givenName', ''),
                'last_name': driver_data.get('familyName', ''),
                'nationality': driver_data.get('nationality', ''),
                'date_of_birth': self._safe_date(driver_data.get('dateOfBirth')),
            }
        )

        if created:
            logger.info(f"Created driver: {driver.full_name}")

        return driver

    def process_team(self, constructor_data: Dict) -> Team:
        """
        Process and create/update Team from API constructor data.

        Args:
            constructor_data: Constructor dictionary from API

        Returns:
            Team model instance
        """
        team_id = constructor_data.get('constructorId', '').lower()
        team_name = constructor_data.get('name', '')

        # Default colors for known teams (historical)
        historical_colors = {
            'ferrari': '#DC0000',
            'mclaren': '#FF8700',
            'williams': '#0082FA',
            'mercedes': '#00D2BE',
            'red_bull': '#0600EF',
            'renault': '#FFF500',
            'lotus': '#FFB800',
            'tyrrell': '#0000FF',
            'brabham': '#FFFFFF',
            'benetton': '#00A000',
            'jordan': '#EFE71B',
            'sauber': '#006EFF',
            'minardi': '#000000',
            'jaguar': '#00A800',
            'toyota': '#EF1E21',
            'bar': '#F0F0F0',
            'force_india': '#FF80C7',
            'toro_rosso': '#0032FA',
        }

        color = historical_colors.get(team_id, '#808080')

        team, created = Team.objects.update_or_create(
            team_id=team_id,
            defaults={
                'name': team_name,
                'full_name': team_name,
                'color': color,
                'canonical_name': Team.get_canonical_name(team_name),
            }
        )

        if created:
            logger.info(f"Created team: {team.name}")

        return team

    def process_circuit(self, circuit_data: Dict) -> Circuit:
        """
        Process and create/update Circuit from API data.

        Args:
            circuit_data: Circuit dictionary from API (nested in race data)

        Returns:
            Circuit model instance
        """
        circuit_id = circuit_data.get('circuitId', '').lower()

        location_data = circuit_data.get('Location', {})

        circuit, created = Circuit.objects.update_or_create(
            circuit_id=circuit_id,
            defaults={
                'name': circuit_data.get('circuitName', ''),
                'location': location_data.get('locality', ''),
                'country': location_data.get('country', ''),
                'latitude': self._safe_float(location_data.get('lat')),
                'longitude': self._safe_float(location_data.get('long')),
            }
        )

        if created:
            logger.info(f"Created circuit: {circuit.name}")

        return circuit

    def process_race_event(self, race_data: Dict, year: int) -> Tuple[Event, Session]:
        """
        Process and create/update Event and Race Session from API data.

        Args:
            race_data: Race dictionary from API
            year: Season year

        Returns:
            Tuple of (Event, Session) instances
        """
        # Get or create season
        season, _ = Season.objects.get_or_create(year=year)

        # Process circuit
        circuit = self.process_circuit(race_data.get('Circuit', {}))

        # Create event
        round_num = self._safe_int(race_data.get('round'), 1)
        event_id = f"{year}_{round_num}"

        race_date = self._safe_date(race_data.get('date'))
        race_time = race_data.get('time', '14:00:00Z')  # Default to 2pm if not available

        event, created = Event.objects.update_or_create(
            event_id=event_id,
            defaults={
                'season': season,
                'round_number': round_num,
                'circuit': circuit,
                'event_name': race_data.get('raceName', ''),
                'event_type': 'race',  # Historical races don't have sprints
                'event_date': race_date,
            }
        )

        # Create race session
        session_id = f"{event_id}_R"
        session_datetime = self._safe_datetime(race_data.get('date'), race_time)

        session, _ = Session.objects.update_or_create(
            session_id=session_id,
            defaults={
                'event': event,
                'session_type': 'R',
                'session_date': session_datetime or timezone.now(),
                'is_complete': True,
                'data_collected': True,
                'collection_date': timezone.now(),
            }
        )

        return event, session

    def process_qualifying_session(self, race_data: Dict, event: Event) -> Session:
        """
        Process and create/update Qualifying Session.

        Args:
            race_data: Race dictionary from API
            event: Event instance

        Returns:
            Session instance
        """
        session_id = f"{event.event_id}_Q"

        # Qualifying typically happens 1 day before race
        qualifying_date = event.event_date
        if qualifying_date:
            qualifying_datetime = timezone.make_aware(
                datetime.combine(qualifying_date, datetime.min.time()),
                timezone.get_current_timezone()
            )
        else:
            qualifying_datetime = timezone.now()

        session, _ = Session.objects.update_or_create(
            session_id=session_id,
            defaults={
                'event': event,
                'session_type': 'Q',
                'session_date': qualifying_datetime,
                'is_complete': True,
                'data_collected': True,
                'collection_date': timezone.now(),
            }
        )

        return session

    
    def process_race_results(self, session: Session, results: List[Dict]) -> int:
        """
        Process and save race results.

        Args:
            session: Session instance
            results: List of result dictionaries from API

        Returns:
            Number of results processed
        """
        count = 0

        # Get winner's time for gap calculation
        winner_time = None
        for result in results:
            if self._safe_int(result.get('position')) == 1:
                time_data = result.get('Time', {})
                millis = time_data.get('millis')
                if millis:
                    winner_time = parse_millis_to_timedelta(millis)
                break

        for result in results:
            try:
                # Process driver and team
                driver = self.process_driver(result.get('Driver', {}))
                team = self.process_team(result.get('Constructor', {}))

                position = self._safe_int(result.get('position'))
                grid_position = self._safe_int(result.get('grid'))
                points = self._safe_float(result.get('points'), 0.0)
                laps = self._safe_int(result.get('laps'), 0)
                status = result.get('status', 'Finished')

                # Parse race time
                time_data = result.get('Time', {})
                total_race_time = None

                if position == 1:
                    # Winner - use absolute time
                    millis = time_data.get('millis')
                    if millis:
                        total_race_time = parse_millis_to_timedelta(millis)
                elif winner_time:
                    # Other drivers - calculate from gap
                    time_str = time_data.get('time', '')
                    if time_str and time_str.startswith('+'):
                        gap = parse_time_string(time_str)
                        if gap:
                            total_race_time = winner_time + gap

                # Parse fastest lap
                fastest_lap_data = result.get('FastestLap', {})
                fastest_lap_time = None
                fastest_lap_number = None

                if fastest_lap_data:
                    fastest_lap_number = self._safe_int(fastest_lap_data.get('lap'))
                    time_data = fastest_lap_data.get('Time', {})
                    time_str = time_data.get('time', '')
                    if time_str:
                        fastest_lap_time = parse_time_string(time_str)

                # Determine if DNF
                dnf = status != 'Finished'

                # Create or update result
                RaceResult.objects.update_or_create(
                    session=session,
                    driver=driver,
                    defaults={
                        'team': team,
                        'position': position or 99,  # Use 99 for disqualified/unclassified
                        'grid_position': grid_position,
                        'points': points,
                        'laps_completed': laps,
                        'total_race_time': total_race_time,
                        'fastest_lap_time': fastest_lap_time,
                        'fastest_lap_number': fastest_lap_number,
                        'status': status,
                        'dnf': dnf,
                    }
                )

                count += 1

            except Exception as e:
                logger.error(f"Error processing race result: {e}", exc_info=True)
                continue

        logger.info(f"Processed {count} race results for {session}")
        return count

    
    def process_qualifying_results(self, session: Session, results: List[Dict]) -> int:
        """
        Process and save qualifying results.

        Args:
            session: Session instance
            results: List of qualifying result dictionaries from API

        Returns:
            Number of results processed
        """
        count = 0

        for result in results:
            try:
                # Process driver and team
                driver = self.process_driver(result.get('Driver', {}))
                team = self.process_team(result.get('Constructor', {}))

                position = self._safe_int(result.get('position'))

                # Parse Q1, Q2, Q3 times
                q1_str = result.get('Q1', '')
                q2_str = result.get('Q2', '')
                q3_str = result.get('Q3', '')

                q1_time = parse_time_string(q1_str) if q1_str else None
                q2_time = parse_time_string(q2_str) if q2_str else None
                q3_time = parse_time_string(q3_str) if q3_str else None

                # Create or update result
                QualifyingResult.objects.update_or_create(
                    session=session,
                    driver=driver,
                    defaults={
                        'team': team,
                        'position': position or 99,
                        'q1_time': q1_time,
                        'q2_time': q2_time,
                        'q3_time': q3_time,
                    }
                )

                count += 1

            except Exception as e:
                logger.error(f"Error processing qualifying result: {e}", exc_info=True)
                continue

        logger.info(f"Processed {count} qualifying results for {session}")
        return count

    
    def process_driver_standings(self, season: Season, event: Event, standings: List[Dict]) -> int:
        """
        Process and save driver standings.

        Args:
            season: Season instance
            event: Event instance (standings are calculated after each event)
            standings: List of standing dictionaries from API

        Returns:
            Number of standings processed
        """
        count = 0

        for standing in standings:
            try:
                # Process driver
                driver = self.process_driver(standing.get('Driver', {}))

                # Get constructor info
                constructors = standing.get('Constructors', [])
                team = None
                if constructors:
                    team = self.process_team(constructors[0])

                if not team:
                    logger.warning(f"No team found for driver {driver.full_name} in standings")
                    continue

                position = self._safe_int(standing.get('position'))
                points = self._safe_float(standing.get('points'), 0.0)
                wins = self._safe_int(standing.get('wins'), 0)

                # Podiums not directly provided in API, will be calculated later
                # For now, use wins as minimum podiums
                podiums = wins

                # Create or update standing
                DriverStanding.objects.update_or_create(
                    season=season,
                    event=event,
                    driver=driver,
                    defaults={
                        'team': team,
                        'position': position or 99,
                        'points': points,
                        'wins': wins,
                        'podiums': podiums,
                    }
                )

                count += 1

            except Exception as e:
                logger.error(f"Error processing driver standing: {e}", exc_info=True)
                continue

        logger.info(f"Processed {count} driver standings for {season.year} Round {event.round_number}")
        return count

    
    def process_constructor_standings(self, season: Season, event: Event, standings: List[Dict]) -> int:
        """
        Process and save constructor standings.

        Args:
            season: Season instance
            event: Event instance
            standings: List of standing dictionaries from API

        Returns:
            Number of standings processed
        """
        count = 0

        for standing in standings:
            try:
                # Process team
                team = self.process_team(standing.get('Constructor', {}))

                position = self._safe_int(standing.get('position'))
                points = self._safe_float(standing.get('points'), 0.0)
                wins = self._safe_int(standing.get('wins'), 0)

                # Podiums not directly provided, use wins as minimum
                podiums = wins

                # Create or update standing
                ConstructorStanding.objects.update_or_create(
                    season=season,
                    event=event,
                    team=team,
                    defaults={
                        'position': position or 99,
                        'points': points,
                        'wins': wins,
                        'podiums': podiums,
                    }
                )

                count += 1

            except Exception as e:
                logger.error(f"Error processing constructor standing: {e}", exc_info=True)
                continue

        logger.info(f"Processed {count} constructor standings for {season.year} Round {event.round_number}")
        return count

    
    def process_pit_stops(self, session: Session, pit_stops: List[Dict]) -> int:
        """
        Process and save pit stop data.
        Note: Pit stop data only available from 2012 onwards.

        Args:
            session: Session instance
            pit_stops: List of pit stop dictionaries from API

        Returns:
            Number of pit stops processed
        """
        count = 0

        for pit_stop in pit_stops:
            try:
                # Get driver by ID
                driver_id = pit_stop.get('driverId', '').lower()
                try:
                    driver = Driver.objects.get(driver_id=driver_id)
                except Driver.DoesNotExist:
                    logger.warning(f"Driver {driver_id} not found for pit stop")
                    continue

                # Get team from race results
                try:
                    race_result = RaceResult.objects.get(session=session, driver=driver)
                    team = race_result.team
                except RaceResult.DoesNotExist:
                    logger.warning(f"No race result found for {driver.full_name} in {session}")
                    continue

                stop_number = self._safe_int(pit_stop.get('stop'))
                lap = self._safe_int(pit_stop.get('lap'))
                duration_str = pit_stop.get('duration', '')

                # Parse duration (in seconds)
                duration = None
                if duration_str:
                    try:
                        duration_seconds = float(duration_str)
                        from datetime import timedelta
                        duration = timedelta(seconds=duration_seconds)
                    except ValueError:
                        pass

                # Create or update pit stop
                PitStop.objects.update_or_create(
                    session=session,
                    driver=driver,
                    stop_number=stop_number,
                    defaults={
                        'team': team,
                        'lap': lap,
                        'duration': duration,
                    }
                )

                count += 1

            except Exception as e:
                logger.error(f"Error processing pit stop: {e}", exc_info=True)
                continue

        logger.info(f"Processed {count} pit stops for {session}")
        return count
