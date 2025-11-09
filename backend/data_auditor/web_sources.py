"""
Módulo para buscar dados em fontes públicas e gratuitas.
Implementa rate limiting e retry logic para evitar bloqueios.
"""
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class RateLimiter:
    """Controlador de rate limiting para evitar bloqueios."""

    def __init__(self, calls_per_second: float = 1.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0
        self.consecutive_errors = 0
        self.backoff_multiplier = 1.0

    def wait(self):
        """Aguarda o tempo necessário para respeitar o rate limit."""
        now = time.time()
        time_since_last_call = now - self.last_call

        # Aplicar backoff se houve erros consecutivos
        adjusted_interval = self.min_interval * self.backoff_multiplier

        if time_since_last_call < adjusted_interval:
            sleep_time = adjusted_interval - time_since_last_call
            time.sleep(sleep_time)

        self.last_call = time.time()

    def report_error(self):
        """Registra um erro e aumenta o backoff."""
        self.consecutive_errors += 1
        # Aumentar backoff exponencialmente: 1x, 2x, 4x, 8x, até max 16x
        self.backoff_multiplier = min(2 ** self.consecutive_errors, 16.0)
        logger.warning(f"Rate limit error. Backoff aumentado para {self.backoff_multiplier}x")

    def report_success(self):
        """Registra sucesso e reduz o backoff gradualmente."""
        if self.consecutive_errors > 0:
            self.consecutive_errors = max(0, self.consecutive_errors - 1)
            self.backoff_multiplier = max(1.0, 2 ** self.consecutive_errors)
            if self.backoff_multiplier == 1.0:
                logger.info("Rate limit normalizado")


class BaseWebSource:
    """Classe base para fontes de dados web."""

    def __init__(self, calls_per_second: float = 0.5):
        # Configurar session com retry mais conservador
        self.session = requests.Session()
        retry = Retry(
            total=2,  # Reduzido de 3 para 2
            backoff_factor=2,  # Aumentado de 1 para 2
            status_forcelist=[500, 502, 503, 504],  # Removido 429 para tratar manualmente
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # Rate limiter mais conservador (0.5 chamadas/segundo = 1 chamada a cada 2 segundos)
        self.rate_limiter = RateLimiter(calls_per_second=calls_per_second)

    def _make_request(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Optional[Dict]:
        """Faz requisição HTTP com rate limiting e error handling."""
        self.rate_limiter.wait()

        try:
            response = self.session.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()

            # Sucesso - reportar ao rate limiter
            self.rate_limiter.report_success()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:
                # Rate limit excedido - aumentar backoff
                logger.warning(f"Rate limit 429 para {url}")
                self.rate_limiter.report_error()
            else:
                logger.warning(f"HTTP Error para {url}: {e}")
            return None

        except requests.exceptions.RequestException as e:
            logger.warning(f"Erro ao fazer requisição para {url}: {e}")
            return None


class WikipediaSource(BaseWebSource):
    """Busca dados na Wikipedia API (gratuita)."""

    BASE_URL = "https://en.wikipedia.org/w/api.php"

    def search_driver(self, driver_name: str) -> Optional[Dict[str, Any]]:
        """
        Busca informações de um piloto na Wikipedia.
        Retorna dict com: nationality, date_of_birth, bio, url
        """
        self.rate_limiter.wait()

        # Buscar página
        search_params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': f"{driver_name} Formula 1 driver",
            'srlimit': 1
        }

        search_result = self._make_request(self.BASE_URL, params=search_params)
        if not search_result or 'query' not in search_result:
            return None

        searches = search_result.get('query', {}).get('search', [])
        if not searches:
            return None

        page_title = searches[0]['title']

        # Obter conteúdo da página
        content_params = {
            'action': 'query',
            'format': 'json',
            'prop': 'extracts|info',
            'exintro': True,
            'explaintext': True,
            'inprop': 'url',
            'titles': page_title
        }

        content_result = self._make_request(self.BASE_URL, params=content_params)
        if not content_result or 'query' not in content_result:
            return None

        pages = content_result.get('query', {}).get('pages', {})
        if not pages:
            return None

        page = next(iter(pages.values()))

        return {
            'title': page.get('title'),
            'extract': page.get('extract', '')[:500],  # Primeiros 500 chars
            'url': page.get('fullurl'),
            'source': 'Wikipedia',
            'confidence': 0.7
        }

    def search_circuit(self, circuit_name: str) -> Optional[Dict[str, Any]]:
        """Busca informações de um circuito na Wikipedia."""
        self.rate_limiter.wait()

        search_params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': f"{circuit_name} circuit",
            'srlimit': 1
        }

        search_result = self._make_request(self.BASE_URL, params=search_params)
        if not search_result or 'query' not in search_result:
            return None

        searches = search_result.get('query', {}).get('search', [])
        if not searches:
            return None

        page_title = searches[0]['title']

        content_params = {
            'action': 'query',
            'format': 'json',
            'prop': 'extracts|info',
            'exintro': True,
            'explaintext': True,
            'inprop': 'url',
            'titles': page_title
        }

        content_result = self._make_request(self.BASE_URL, params=content_params)
        if not content_result:
            return None

        pages = content_result.get('query', {}).get('pages', {})
        if not pages:
            return None

        page = next(iter(pages.values()))

        return {
            'title': page.get('title'),
            'extract': page.get('extract', '')[:500],
            'url': page.get('fullurl'),
            'source': 'Wikipedia',
            'confidence': 0.7
        }


class WikidataSource(BaseWebSource):
    """Busca dados estruturados no Wikidata (gratuito)."""

    BASE_URL = "https://www.wikidata.org/w/api.php"
    SPARQL_URL = "https://query.wikidata.org/sparql"

    def search_driver_birthdate(self, driver_name: str) -> Optional[Dict[str, Any]]:
        """Busca data de nascimento de um piloto no Wikidata via SPARQL."""
        self.rate_limiter.wait()

        # Query SPARQL para buscar piloto de F1 e sua data de nascimento
        sparql_query = f"""
        SELECT ?driver ?driverLabel ?birthDate ?countryLabel WHERE {{
          ?driver wdt:P106 wd:Q10841764 .  # ocupação: piloto de Fórmula 1
          ?driver rdfs:label ?driverLabel .
          FILTER(CONTAINS(LCASE(?driverLabel), LCASE("{driver_name}")))
          OPTIONAL {{ ?driver wdt:P569 ?birthDate . }}
          OPTIONAL {{ ?driver wdt:P27 ?country . }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 1
        """

        try:
            response = self.session.get(
                self.SPARQL_URL,
                params={'query': sparql_query, 'format': 'json'},
                headers={'User-Agent': 'F1DataAuditor/1.0'},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results = data.get('results', {}).get('bindings', [])
            if not results:
                return None

            result = results[0]

            return {
                'date_of_birth': result.get('birthDate', {}).get('value'),
                'nationality': result.get('countryLabel', {}).get('value'),
                'url': self.SPARQL_URL,
                'source': 'Wikidata',
                'confidence': 0.9
            }
        except Exception as e:
            logger.warning(f"Erro ao buscar no Wikidata: {e}")
            return None


class ErgastAPISource(BaseWebSource):
    """
    Busca dados na API Ergast (gratuita, mas foi desativada em 2024).
    Mantido para compatibilidade, mas pode não funcionar.

    Alternativa: Jolpica API (https://api.jolpi.ca/ergast/)

    IMPORTANTE: Esta API tem rate limiting agressivo.
    Configurado para 0.2 chamadas/segundo (1 chamada a cada 5 segundos).
    """

    BASE_URL = "https://api.jolpi.ca/ergast/f1"

    def __init__(self):
        # Jolpica/Ergast precisa de rate limiting muito conservador
        super().__init__(calls_per_second=0.2)  # 1 chamada a cada 5 segundos

    def get_driver_info(self, driver_id: str) -> Optional[Dict[str, Any]]:
        """Busca informações de um piloto na API Ergast/Jolpica."""
        self.rate_limiter.wait()

        url = f"{self.BASE_URL}/drivers/{driver_id}.json"
        data = self._make_request(url)

        if not data:
            return None

        try:
            driver = data['MRData']['DriverTable']['Drivers'][0]
            return {
                'code': driver.get('code'),
                'number': driver.get('permanentNumber'),
                'nationality': driver.get('nationality'),
                'date_of_birth': driver.get('dateOfBirth'),
                'url': driver.get('url'),
                'source': 'Jolpica/Ergast API',
                'confidence': 0.95
            }
        except (KeyError, IndexError):
            return None

    def get_circuit_info(self, circuit_id: str) -> Optional[Dict[str, Any]]:
        """Busca informações de um circuito na API Ergast/Jolpica."""
        self.rate_limiter.wait()

        url = f"{self.BASE_URL}/circuits/{circuit_id}.json"
        data = self._make_request(url)

        if not data:
            return None

        try:
            circuit = data['MRData']['CircuitTable']['Circuits'][0]
            location = circuit.get('Location', {})

            return {
                'latitude': float(location.get('lat', 0)),
                'longitude': float(location.get('long', 0)),
                'location': location.get('locality'),
                'country': location.get('country'),
                'url': circuit.get('url'),
                'source': 'Jolpica/Ergast API',
                'confidence': 0.95
            }
        except (KeyError, IndexError, ValueError):
            return None


class DataSourceAggregator:
    """
    Agrega múltiplas fontes de dados e retorna o melhor resultado.

    Estratégia de busca:
    1. Prioriza Wikidata (mais confiável e sem rate limiting agressivo)
    2. Usa Ergast/Jolpica apenas como fallback se Wikidata falhar
    3. Implementa circuit breaker: se Ergast falhar muito, para de tentar
    """

    def __init__(self):
        self.wikipedia = WikipediaSource()
        self.wikidata = WikidataSource()
        self.ergast = ErgastAPISource()
        self.ergast_consecutive_failures = 0
        self.ergast_circuit_breaker_threshold = 5

    def _is_ergast_available(self) -> bool:
        """Verifica se Ergast está disponível (circuit breaker)."""
        if self.ergast_consecutive_failures >= self.ergast_circuit_breaker_threshold:
            logger.info(f"Ergast circuit breaker ativo ({self.ergast_consecutive_failures} falhas). Pulando.")
            return False
        return True

    def _report_ergast_result(self, success: bool):
        """Registra resultado de chamada Ergast para circuit breaker."""
        if success:
            self.ergast_consecutive_failures = max(0, self.ergast_consecutive_failures - 1)
            if self.ergast_consecutive_failures == 0:
                logger.info("Ergast circuit breaker resetado")
        else:
            self.ergast_consecutive_failures += 1
            if self.ergast_consecutive_failures == self.ergast_circuit_breaker_threshold:
                logger.warning(f"Ergast circuit breaker ativado após {self.ergast_consecutive_failures} falhas")

    def find_driver_date_of_birth(self, driver_name: str, driver_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Busca data de nascimento de um piloto em múltiplas fontes.
        Retorna o resultado com maior confiança.

        Estratégia:
        1. Wikidata primeiro (mais confiável)
        2. Ergast como fallback (se circuit breaker permitir)
        """
        results = []

        # 1. Tentar Wikidata primeiro (PRIORIDADE)
        if driver_name:
            wikidata_result = self.wikidata.search_driver_birthdate(driver_name)
            if wikidata_result and wikidata_result.get('date_of_birth'):
                results.append(wikidata_result)
                # Se Wikidata tem a resposta, não precisa tentar Ergast
                return wikidata_result

        # 2. Tentar Ergast/Jolpica apenas se Wikidata falhou E circuit breaker permite
        if driver_id and self._is_ergast_available():
            ergast_result = self.ergast.get_driver_info(driver_id)
            if ergast_result and ergast_result.get('date_of_birth'):
                results.append(ergast_result)
                self._report_ergast_result(True)
            else:
                self._report_ergast_result(False)

        # Retornar resultado com maior confiança
        if results:
            return max(results, key=lambda x: x.get('confidence', 0))

        return None

    def find_circuit_coordinates(self, circuit_name: str, circuit_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Busca coordenadas de um circuito.

        Estratégia: Somente Ergast se circuit breaker permitir
        (Wikipedia/Wikidata não têm coordenadas estruturadas facilmente)
        """
        results = []

        # Ergast tem coordenadas precisas, mas apenas se circuit breaker permitir
        if circuit_id and self._is_ergast_available():
            ergast_result = self.ergast.get_circuit_info(circuit_id)
            if ergast_result and ergast_result.get('latitude') and ergast_result.get('longitude'):
                results.append(ergast_result)
                self._report_ergast_result(True)
            else:
                self._report_ergast_result(False)

        if results:
            return max(results, key=lambda x: x.get('confidence', 0))

        return None

    def find_driver_nationality(self, driver_name: str, driver_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Busca nacionalidade de um piloto.

        Estratégia:
        1. Wikidata primeiro (PRIORIDADE)
        2. Ergast como fallback (se circuit breaker permitir)
        """
        results = []

        # 1. Wikidata primeiro
        if driver_name:
            wikidata_result = self.wikidata.search_driver_birthdate(driver_name)
            if wikidata_result and wikidata_result.get('nationality'):
                results.append(wikidata_result)
                # Se Wikidata tem a resposta, não precisa tentar Ergast
                return wikidata_result

        # 2. Ergast como fallback
        if driver_id and self._is_ergast_available():
            ergast_result = self.ergast.get_driver_info(driver_id)
            if ergast_result and ergast_result.get('nationality'):
                results.append(ergast_result)
                self._report_ergast_result(True)
            else:
                self._report_ergast_result(False)

        if results:
            return max(results, key=lambda x: x.get('confidence', 0))

        return None
