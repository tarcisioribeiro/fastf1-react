"""
Celery tasks for collecting circuit data from multiple sources.
"""
import logging
import requests
from celery import shared_task
from django.utils import timezone
from core.models import Circuit

logger = logging.getLogger('data_collector')


def fetch_circuits_json():
    """
    Busca o arquivo circuits.json do repositório f1-circuits-svg.
    Retorna dict com dados dos circuitos.
    """
    url = "https://raw.githubusercontent.com/julesr0y/f1-circuits-svg/main/circuits.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching circuits.json: {e}")
        return None


def fetch_circuit_info_wikipedia(circuit_name: str) -> dict:
    """
    Busca informações do circuito na Wikipedia.
    Retorna dict com história e informações adicionais.
    """
    try:
        # Usar Wikipedia API para buscar resumo do circuito
        wiki_url = "https://en.wikipedia.org/w/api.php"
        params = {
            'action': 'query',
            'format': 'json',
            'prop': 'extracts|pageimages',
            'exintro': True,
            'explaintext': True,
            'titles': circuit_name,
            'redirects': 1
        }

        response = requests.get(wiki_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        pages = data.get('query', {}).get('pages', {})
        if pages:
            page = next(iter(pages.values()))
            extract = page.get('extract', '')

            return {
                'description': extract[:500] if extract else '',  # Primeiros 500 caracteres
                'history': extract if extract else '',
            }
    except Exception as e:
        logger.error(f"Error fetching Wikipedia info for {circuit_name}: {e}")

    return {}


def fetch_circuit_details_ergast(circuit_id: str) -> dict:
    """
    Busca detalhes do circuito na Ergast API.
    Retorna informações técnicas do circuito.
    """
    try:
        url = f"https://ergast.com/api/f1/circuits/{circuit_id}.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        circuits = data.get('MRData', {}).get('CircuitTable', {}).get('Circuits', [])
        if circuits:
            circuit = circuits[0]
            location = circuit.get('Location', {})

            return {
                'name': circuit.get('circuitName', ''),
                'location': location.get('locality', ''),
                'country': location.get('country', ''),
                'latitude': float(location.get('lat', 0)) if location.get('lat') else None,
                'longitude': float(location.get('long', 0)) if location.get('long') else None,
            }
    except Exception as e:
        logger.error(f"Error fetching Ergast data for {circuit_id}: {e}")

    return {}


def fetch_circuit_race_history(circuit_id: str) -> dict:
    """
    Busca histórico de corridas do circuito via Ergast API.
    Retorna informações sobre primeira corrida e total de corridas.
    """
    try:
        # Buscar todas as corridas neste circuito
        url = f"https://ergast.com/api/f1/circuits/{circuit_id}/races.json?limit=1000"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        races = data.get('MRData', {}).get('RaceTable', {}).get('Races', [])
        if races:
            first_race = min(races, key=lambda x: int(x['season']))
            return {
                'first_grand_prix': int(first_race['season']),
                'total_races_held': len(races),
            }
    except Exception as e:
        logger.error(f"Error fetching race history for {circuit_id}: {e}")

    return {}


@shared_task(bind=True, max_retries=3)
def collect_all_circuits_data(self):
    """
    Tarefa principal para coletar dados de todos os circuitos.
    Busca dados do circuits.json, Wikipedia e Ergast API.
    """
    logger.info("Starting circuit data collection")

    try:
        # 1. Buscar circuits.json
        circuits_data = fetch_circuits_json()
        if not circuits_data:
            logger.error("Failed to fetch circuits.json")
            return {'status': 'error', 'message': 'Failed to fetch circuits.json'}

        circuits_updated = 0
        circuits_created = 0

        # 2. Processar cada circuito
        for circuit_data in circuits_data:
            circuit_id = circuit_data.get('id')
            if not circuit_id:
                continue

            # Buscar ou criar circuito
            circuit, created = Circuit.objects.get_or_create(
                circuit_id=circuit_id,
                defaults={
                    'name': circuit_data.get('name', ''),
                    'country': circuit_data.get('countryId', '').title(),
                    'latitude': circuit_data.get('latitude'),
                    'longitude': circuit_data.get('longitude'),
                }
            )

            if created:
                circuits_created += 1
                logger.info(f"Created new circuit: {circuit.name}")
            else:
                circuits_updated += 1

            # 3. Atualizar informações básicas do circuits.json
            circuit.name = circuit_data.get('name', circuit.name)
            circuit.country = circuit_data.get('countryId', circuit.country).title()
            circuit.latitude = circuit_data.get('latitude', circuit.latitude)
            circuit.longitude = circuit_data.get('longitude', circuit.longitude)

            # 4. Definir layout_id (usar o layout mais recente)
            layouts = circuit_data.get('layouts', [])
            if layouts:
                # Pegar o último layout (mais recente)
                latest_layout = layouts[-1]
                layout_id = latest_layout.get('layoutId')
                circuit.layout_id = layout_id

                # Definir SVG URL
                if layout_id:
                    circuit.svg_url = f"https://raw.githubusercontent.com/julesr0y/f1-circuits-svg/main/circuits/black/{layout_id}.svg"

            # 5. Buscar informações adicionais da Ergast API
            ergast_data = fetch_circuit_details_ergast(circuit_id)
            if ergast_data:
                circuit.location = ergast_data.get('location', circuit.location)
                if ergast_data.get('latitude'):
                    circuit.latitude = ergast_data['latitude']
                if ergast_data.get('longitude'):
                    circuit.longitude = ergast_data['longitude']

            # 6. Buscar histórico de corridas
            history_data = fetch_circuit_race_history(circuit_id)
            if history_data:
                circuit.first_grand_prix = history_data.get('first_grand_prix')
                circuit.total_races_held = history_data.get('total_races_held')

            # 7. Buscar informações da Wikipedia (apenas se não existir)
            if not circuit.history or not circuit.description:
                wiki_data = fetch_circuit_info_wikipedia(circuit.name)
                if wiki_data:
                    if not circuit.description:
                        circuit.description = wiki_data.get('description', '')
                    if not circuit.history:
                        circuit.history = wiki_data.get('history', '')

            circuit.save()
            logger.info(f"Updated circuit: {circuit.name} (ID: {circuit_id})")

        result = {
            'status': 'success',
            'circuits_created': circuits_created,
            'circuits_updated': circuits_updated,
            'total_processed': circuits_created + circuits_updated,
            'timestamp': timezone.now().isoformat()
        }

        logger.info(f"Circuit data collection completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in collect_all_circuits_data: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@shared_task
def update_circuit_technical_data(circuit_id: str, **technical_data):
    """
    Atualiza dados técnicos de um circuito específico.

    Args:
        circuit_id: ID do circuito
        technical_data: Dict com dados técnicos (length_km, number_of_corners, etc.)
    """
    try:
        circuit = Circuit.objects.get(circuit_id=circuit_id)

        # Atualizar campos técnicos se fornecidos
        if 'length_km' in technical_data:
            circuit.length_km = technical_data['length_km']
        if 'number_of_corners' in technical_data:
            circuit.number_of_corners = technical_data['number_of_corners']
        if 'number_of_laps' in technical_data:
            circuit.number_of_laps = technical_data['number_of_laps']
        if 'race_distance_km' in technical_data:
            circuit.race_distance_km = technical_data['race_distance_km']
        if 'circuit_type' in technical_data:
            circuit.circuit_type = technical_data['circuit_type']
        if 'direction' in technical_data:
            circuit.direction = technical_data['direction']

        circuit.save()
        logger.info(f"Updated technical data for circuit: {circuit.name}")

        return {'status': 'success', 'circuit': circuit.name}

    except Circuit.DoesNotExist:
        logger.error(f"Circuit not found: {circuit_id}")
        return {'status': 'error', 'message': 'Circuit not found'}
    except Exception as e:
        logger.error(f"Error updating circuit technical data: {e}")
        return {'status': 'error', 'message': str(e)}
