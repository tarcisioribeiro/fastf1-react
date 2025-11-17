"""
Scraper da Ergast API para coleta de dados históricos de F1 (1950-2024).
API oficial: http://ergast.com/mrd/
Documentação: https://ergast.com/mrd/
"""
import logging
import time
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger('data_collector')


class ErgastAPIClient:
    """
    Cliente para a Ergast API com retry logic e rate limiting.
    """

    BASE_URL = "http://ergast.com/api/f1"
    RATE_LIMIT_DELAY = 0.5  # Segundos entre requests (respeitar API)

    def __init__(self):
        self.session = self._create_session()
        self.last_request_time = 0

    def _create_session(self) -> requests.Session:
        """Criar sessão com retry logic."""
        session = requests.Session()

        # Configurar retry strategy
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _rate_limit(self):
        """Aplicar rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Fazer request à API com rate limiting.

        Args:
            endpoint: Endpoint da API (ex: "2020/1/results")
            params: Parâmetros query string

        Returns:
            Dict com resposta JSON ou None em caso de erro
        """
        self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}.json"

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao acessar Ergast API: {url} - {e}")
            return None

    def get_season_schedule(self, year: int) -> Optional[List[Dict]]:
        """Obter calendário de uma temporada."""
        logger.info(f"Buscando calendário de {year} na Ergast API...")

        data = self._make_request(f"{year}")

        if not data:
            return None

        try:
            races = data['MRData']['RaceTable']['Races']
            logger.info(f"Encontradas {len(races)} corridas em {year}")
            return races
        except (KeyError, TypeError) as e:
            logger.error(f"Erro ao processar calendário de {year}: {e}")
            return None

    def get_race_results(self, year: int, round_number: int) -> Optional[Dict]:
        """Obter resultados de uma corrida."""
        logger.debug(f"Buscando resultados de corrida: {year} R{round_number}")

        data = self._make_request(f"{year}/{round_number}/results")

        if not data:
            return None

        try:
            races = data['MRData']['RaceTable']['Races']
            if races:
                return races[0]
            return None
        except (KeyError, TypeError) as e:
            logger.error(f"Erro ao processar resultados de corrida {year} R{round_number}: {e}")
            return None

    def get_qualifying_results(self, year: int, round_number: int) -> Optional[Dict]:
        """Obter resultados de qualificação."""
        logger.debug(f"Buscando resultados de qualificação: {year} R{round_number}")

        data = self._make_request(f"{year}/{round_number}/qualifying")

        if not data:
            return None

        try:
            races = data['MRData']['RaceTable']['Races']
            if races:
                return races[0]
            return None
        except (KeyError, TypeError) as e:
            logger.error(f"Erro ao processar resultados de qualificação {year} R{round_number}: {e}")
            return None

    def get_sprint_results(self, year: int, round_number: int) -> Optional[Dict]:
        """Obter resultados de sprint."""
        logger.debug(f"Buscando resultados de sprint: {year} R{round_number}")

        data = self._make_request(f"{year}/{round_number}/sprint")

        if not data:
            return None

        try:
            races = data['MRData']['RaceTable']['Races']
            if races:
                return races[0]
            return None
        except (KeyError, TypeError) as e:
            logger.debug(f"Sem resultados de sprint para {year} R{round_number}: {e}")
            return None

    def get_driver_standings(self, year: int, round_number: int = None) -> Optional[List[Dict]]:
        """
        Obter classificação de pilotos.

        Args:
            year: Ano da temporada
            round_number: Round específico (None = final da temporada)
        """
        endpoint = f"{year}/driverStandings"
        if round_number:
            endpoint = f"{year}/{round_number}/driverStandings"

        logger.debug(f"Buscando classificação de pilotos: {endpoint}")

        data = self._make_request(endpoint)

        if not data:
            return None

        try:
            standings_lists = data['MRData']['StandingsTable']['StandingsLists']
            if standings_lists:
                return standings_lists[0]['DriverStandings']
            return None
        except (KeyError, TypeError) as e:
            logger.error(f"Erro ao processar classificação de pilotos {year} R{round_number}: {e}")
            return None

    def get_constructor_standings(self, year: int, round_number: int = None) -> Optional[List[Dict]]:
        """
        Obter classificação de construtores.

        Args:
            year: Ano da temporada
            round_number: Round específico (None = final da temporada)
        """
        endpoint = f"{year}/constructorStandings"
        if round_number:
            endpoint = f"{year}/{round_number}/constructorStandings"

        logger.debug(f"Buscando classificação de construtores: {endpoint}")

        data = self._make_request(endpoint)

        if not data:
            return None

        try:
            standings_lists = data['MRData']['StandingsTable']['StandingsLists']
            if standings_lists:
                return standings_lists[0]['ConstructorStandings']
            return None
        except (KeyError, TypeError) as e:
            logger.error(f"Erro ao processar classificação de construtores {year} R{round_number}: {e}")
            return None

    def get_drivers(self, year: int = None) -> Optional[List[Dict]]:
        """Obter lista de pilotos (de um ano específico ou todos)."""
        endpoint = "drivers"
        if year:
            endpoint = f"{year}/drivers"

        logger.debug(f"Buscando pilotos: {endpoint}")

        data = self._make_request(endpoint, params={'limit': 1000})

        if not data:
            return None

        try:
            drivers = data['MRData']['DriverTable']['Drivers']
            logger.info(f"Encontrados {len(drivers)} pilotos")
            return drivers
        except (KeyError, TypeError) as e:
            logger.error(f"Erro ao processar lista de pilotos: {e}")
            return None

    def get_constructors(self, year: int = None) -> Optional[List[Dict]]:
        """Obter lista de construtores (de um ano específico ou todos)."""
        endpoint = "constructors"
        if year:
            endpoint = f"{year}/constructors"

        logger.debug(f"Buscando construtores: {endpoint}")

        data = self._make_request(endpoint, params={'limit': 1000})

        if not data:
            return None

        try:
            constructors = data['MRData']['ConstructorTable']['Constructors']
            logger.info(f"Encontrados {len(constructors)} construtores")
            return constructors
        except (KeyError, TypeError) as e:
            logger.error(f"Erro ao processar lista de construtores: {e}")
            return None

    def get_circuits(self, year: int = None) -> Optional[List[Dict]]:
        """Obter lista de circuitos (de um ano específico ou todos)."""
        endpoint = "circuits"
        if year:
            endpoint = f"{year}/circuits"

        logger.debug(f"Buscando circuitos: {endpoint}")

        data = self._make_request(endpoint, params={'limit': 1000})

        if not data:
            return None

        try:
            circuits = data['MRData']['CircuitTable']['Circuits']
            logger.info(f"Encontrados {len(circuits)} circuitos")
            return circuits
        except (KeyError, TypeError) as e:
            logger.error(f"Erro ao processar lista de circuitos: {e}")
            return None

    def get_lap_times(self, year: int, round_number: int, lap_number: int = None) -> Optional[List[Dict]]:
        """
        Obter tempos de volta.

        Args:
            year: Ano
            round_number: Número do round
            lap_number: Número da volta específica (None = todas)
        """
        endpoint = f"{year}/{round_number}/laps"
        if lap_number:
            endpoint = f"{year}/{round_number}/laps/{lap_number}"

        logger.debug(f"Buscando tempos de volta: {endpoint}")

        data = self._make_request(endpoint)

        if not data:
            return None

        try:
            races = data['MRData']['RaceTable']['Races']
            if races and 'Laps' in races[0]:
                return races[0]['Laps']
            return None
        except (KeyError, TypeError) as e:
            logger.error(f"Erro ao processar tempos de volta {year} R{round_number}: {e}")
            return None

    def get_pit_stops(self, year: int, round_number: int) -> Optional[List[Dict]]:
        """Obter pit stops de uma corrida."""
        logger.debug(f"Buscando pit stops: {year} R{round_number}")

        data = self._make_request(f"{year}/{round_number}/pitstops")

        if not data:
            return None

        try:
            races = data['MRData']['RaceTable']['Races']
            if races and 'PitStops' in races[0]:
                return races[0]['PitStops']
            return None
        except (KeyError, TypeError) as e:
            logger.debug(f"Sem pit stops para {year} R{round_number}: {e}")
            return None


class ErgastDataMapper:
    """
    Mapeia dados da Ergast API para o formato do banco de dados.
    """

    @staticmethod
    def map_circuit(circuit_data: Dict) -> Dict:
        """Mapear dados de circuito."""
        return {
            'circuit_id': circuit_data['circuitId'],
            'name': circuit_data['circuitName'],
            'location': circuit_data['Location']['locality'],
            'country': circuit_data['Location']['country'],
            'latitude': float(circuit_data['Location']['lat']) if 'lat' in circuit_data['Location'] else None,
            'longitude': float(circuit_data['Location']['long']) if 'long' in circuit_data['Location'] else None,
        }

    @staticmethod
    def map_driver(driver_data: Dict) -> Dict:
        """Mapear dados de piloto."""
        # Gerar código de 3 letras se não existir
        code = driver_data.get('code', '')
        if not code:
            # Fallback: usar primeiras 3 letras do sobrenome em uppercase
            code = driver_data['familyName'][:3].upper()

        # Gerar número se não existir
        number = driver_data.get('permanentNumber', '')
        if not number or number == '':
            # Usar ID como fallback
            number = hash(driver_data['driverId']) % 99 + 1

        date_of_birth = None
        if 'dateOfBirth' in driver_data:
            try:
                date_of_birth = datetime.strptime(driver_data['dateOfBirth'], '%Y-%m-%d').date()
            except:
                pass

        return {
            'driver_id': driver_data['driverId'],
            'code': code,
            'number': int(number),
            'first_name': driver_data['givenName'],
            'last_name': driver_data['familyName'],
            'nationality': driver_data.get('nationality', ''),
            'date_of_birth': date_of_birth,
        }

    @staticmethod
    def map_constructor(constructor_data: Dict) -> Dict:
        """Mapear dados de construtor/equipe."""
        return {
            'team_id': constructor_data['constructorId'],
            'name': constructor_data['name'],
            'full_name': constructor_data.get('name', ''),
            'color': '#FFFFFF',  # Cor padrão - pode ser sobrescrita depois
        }

    @staticmethod
    def parse_time(time_str: str) -> Optional[timedelta]:
        """
        Parsear string de tempo para timedelta.

        Formats supported:
            - "1:23.456" (min:sec.ms)
            - "23.456" (sec.ms)
            - "+1.234" (gap)
        """
        if not time_str or time_str == '' or time_str == 'None':
            return None

        try:
            # Remover '+' se for gap
            time_str = time_str.replace('+', '')

            # Se tem ':', é min:sec.ms
            if ':' in time_str:
                parts = time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                total_seconds = minutes * 60 + seconds
            else:
                # É apenas sec.ms
                total_seconds = float(time_str)

            return timedelta(seconds=total_seconds)

        except (ValueError, IndexError) as e:
            logger.warning(f"Erro ao parsear tempo '{time_str}': {e}")
            return None

    @staticmethod
    def parse_duration_to_seconds(duration_str: str) -> Optional[float]:
        """
        Parsear duração (ex: pit stop) para segundos.

        Format: "23.456"
        """
        if not duration_str or duration_str == '' or duration_str == 'None':
            return None

        try:
            return float(duration_str)
        except ValueError:
            logger.warning(f"Erro ao parsear duração '{duration_str}'")
            return None


# Instância global do cliente
ergast_client = ErgastAPIClient()
ergast_mapper = ErgastDataMapper()
