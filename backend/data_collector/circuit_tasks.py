"""
Celery tasks for collecting circuit data from multiple sources.
"""
import logging
import time
import requests
from celery import shared_task
from django.utils import timezone
from core.models import Circuit

logger = logging.getLogger('data_collector')

# ergast.com foi descontinuado (só retorna 404); jolpica-f1 é o sucessor
# comunitário com o mesmo schema de resposta.
ERGAST_BASE_URL = "https://api.jolpi.ca/ergast/f1"

# circuit_id do FastF1/Ergast que diverge do id usado hoje pela Ergast/Jolpica
# e pelo repositório f1-circuits-svg (circuitos renomeados/substituídos).
CIRCUIT_ID_ALIASES = {
    'madrid': 'madring',       # GP da Espanha migra para o Madring em 2026
    'kuala_lumpur': 'sepang',  # GP da Malásia (Sepang) retorna em 2026
}

# circuit.name (herdado do FastF1) é o nome da cidade, não do circuito/pista -
# buscar esse nome na Wikipedia traria o artigo da cidade, não do autódromo.
CIRCUIT_WIKIPEDIA_TITLE_OVERRIDES = {
    'madrid': 'Circuito de Madring',
    'kuala_lumpur': 'Sepang International Circuit',
}


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

        # Wikipedia bloqueia (403) requisições sem User-Agent identificável
        headers = {'User-Agent': 'fastf1-react/1.0 (https://github.com/tarcisioribeiro/fastf1-react)'}
        response = requests.get(wiki_url, params=params, headers=headers, timeout=10)
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
        lookup_id = CIRCUIT_ID_ALIASES.get(circuit_id, circuit_id)
        url = f"{ERGAST_BASE_URL}/circuits/{lookup_id}.json"
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
        lookup_id = CIRCUIT_ID_ALIASES.get(circuit_id, circuit_id)
        url = f"{ERGAST_BASE_URL}/circuits/{lookup_id}/races.json?limit=1000"
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

                # Definir SVG URL (path atual do repo: <variant>/<style>/<layoutId>.svg)
                if layout_id:
                    circuit.svg_url = circuit.remote_svg_url('black')

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


# Mapeamento de circuit_id (Ergast) para layout_id (f1-circuits-svg)
ERGAST_TO_LAYOUT_MAPPING = {
    # Circuitos novos/renomeados (id do FastF1 diverge do id no f1-circuits-svg)
    'madrid': 'madring-1',
    'kuala_lumpur': 'sepang-1',
    # Circuitos atuais do calendário
    'albert_park': 'melbourne-2',
    'rodriguez': 'mexico-city-3',
    'galvez': 'buenos-aires-4',
    'barcelona': 'catalunya-6',
    'brands_hatch': 'brands-hatch-2',
    'budapest': 'hungaroring-3',
    'charade': 'clermont-ferrand-1',
    'magny_cours': 'magny-cours-3',
    'spa': 'spa-francorchamps-4',
    'villeneuve': 'montreal-6',
    'tremblant': 'mont-tremblant-1',
    'americas': 'austin-1',
    'ricard': 'paul-ricard-3',
    'hockenheim': 'hockenheimring-4',
    'las_vegas': 'las-vegas-1',
    'le_castellet': 'paul-ricard-3',
    'lemans': 'bugatti-1',
    'long_beach': 'long-beach-3',
    'marina_bay': 'marina-bay-4',
    'mexico_city': 'mexico-city-3',
    'miami_gardens': 'miami-1',
    'miami': 'miami-1',
    'monte_carlo': 'monaco-5',
    'monaco': 'monaco-5',
    'okayama': 'aida-1',
    'george': 'east-london-1',
    'red_bull_ring': 'spielberg-3',
    'essarts': 'rouen-2',
    'sakhir': 'bahrain-3',
    'bahrain': 'bahrain-3',
    'interlagos': 'interlagos-2',
    'são_paulo': 'interlagos-2',
    'sao_paulo': 'interlagos-2',
    'singapore': 'marina-bay-4',
    'watkins_glen': 'watkins-glen-3',
    'yas_island': 'yas-marina-2',
    'yas_marina': 'yas-marina-2',
    'jeddah': 'jeddah-1',
    'losail': 'lusail-1',
    'lusail': 'lusail-1',
    'zandvoort': 'zandvoort-4',
    'baku': 'baku-1',
    'imola': 'imola-3',
    'monza': 'monza-6',
    'suzuka': 'suzuka-2',
    'silverstone': 'silverstone-8',
    'shanghai': 'shanghai-1',
    'hungaroring': 'hungaroring-3',
    'spielberg': 'spielberg-3',
    'nurburgring': 'nurburgring-4',
    'sepang': 'sepang-1',
    'yeongam': 'yeongam-1',
    'buddh': 'buddh-1',
    'istanbul': 'istanbul-1',
    'sochi': 'sochi-1',
    'portimao': 'portimao-1',
    'mugello': 'mugello-1',
    'valencia': 'valencia-1',
    'fuji': 'fuji-2',
    'indianapolis': 'indianapolis-2',
    'kyalami': 'kyalami-2',
    'jacarepagua': 'jacarepagua-1',
    'detroit': 'detroit-2',
    'phoenix': 'phoenix-2',
    'adelaide': 'adelaide-1',
    'dallas': 'dallas-1',
    'caesars_palace': 'caesars-palace-1',
    'riverside': 'riverside-1',
    'sebring': 'sebring-1',
    'mosport': 'mosport-1',
    'dijon': 'dijon-2',
    'zolder': 'zolder-2',
    'nivelles': 'nivelles-1',
    'jarama': 'jarama-2',
    'jerez': 'jerez-2',
    'estoril': 'estoril-2',
    'montjuic': 'montjuic-1',
    'pedralbes': 'pedralbes-1',
    'boavista': 'porto-1',
    'monsanto': 'monsanto-1',
    'pescara': 'pescara-1',
    'reims': 'reims-2',
    'aintree': 'aintree-1',
    'anderstorp': 'anderstorp-1',
    'avus': 'avus-1',
    'bremgarten': 'bremgarten-1',
    'donington': 'donington-1',
    'ain_diab': 'ain-diab-1',
    'zeltweg': 'zeltweg-1',
}


@shared_task
def update_missing_circuit_layouts():
    """
    Atualiza os layout_id dos circuitos que estão faltando,
    usando o mapeamento entre IDs do Ergast e IDs do f1-circuits-svg.
    """
    logger.info("Starting update of missing circuit layouts")

    updated = 0
    not_found = []

    circuits = Circuit.objects.filter(layout_id='') | Circuit.objects.filter(layout_id__isnull=True)

    for circuit in circuits:
        circuit_id = circuit.circuit_id

        # Tentar encontrar no mapeamento
        layout_id = ERGAST_TO_LAYOUT_MAPPING.get(circuit_id)

        if layout_id:
            circuit.layout_id = layout_id
            circuit.svg_url = circuit.remote_svg_url('black')
            circuit.save()
            updated += 1
            logger.info(f"Updated layout for {circuit.name}: {layout_id}")
        else:
            not_found.append(circuit_id)
            logger.warning(f"No layout mapping found for circuit: {circuit.name} (ID: {circuit_id})")

    result = {
        'status': 'success',
        'updated': updated,
        'not_found': not_found,
        'timestamp': timezone.now().isoformat()
    }

    logger.info(f"Circuit layout update completed: {result}")
    return result


@shared_task
def consolidate_duplicate_circuits():
    """
    Consolida circuitos duplicados no banco de dados.
    Mantém o circuito com mais dados e remove duplicatas.
    """
    logger.info("Starting circuit consolidation")

    # Mapeamento de circuitos duplicados: (manter, remover)
    # Preferência: manter o ID do f1-circuits-svg (mais padronizado)
    duplicates = [
        # (circuit_id_to_keep, circuit_id_to_remove)
        # Marina Bay (3 duplicatas)
        ('marina-bay', 'marina_bay'),
        ('marina-bay', 'singapore'),
        # Mexico City (3 duplicatas)
        ('mexico-city', 'rodriguez'),
        ('mexico-city', 'mexico_city'),
        # Yas Marina (3 duplicatas)
        ('yas-marina', 'yas_island'),
        ('yas-marina', 'yas_marina'),
        # Paul Ricard (3 duplicatas)
        ('paul-ricard', 'ricard'),
        ('paul-ricard', 'le_castellet'),
        # East London
        ('east-london', 'george'),
        # Bahrain
        ('bahrain', 'sakhir'),
        # Bugatti/Le Mans
        ('bugatti', 'lemans'),
        # Mont Tremblant
        ('mont-tremblant', 'tremblant'),
        # Rouen
        ('rouen', 'essarts'),
        # Clermont-Ferrand
        ('clermont-ferrand', 'charade'),
        # Watkins Glen
        ('watkins-glen', 'watkins_glen'),
        # Long Beach
        ('long-beach', 'long_beach'),
        # Brands Hatch
        ('brands-hatch', 'brands_hatch'),
        # Aida/Okayama
        ('aida', 'okayama'),
        # Buenos Aires
        ('buenos-aires', 'galvez'),
        # Magny Cours
        ('magny-cours', 'magny_cours'),
        # Hockenheimring
        ('hockenheimring', 'hockenheim'),
        # Las Vegas
        ('las-vegas', 'las_vegas'),
        # Interlagos
        ('interlagos', 'são_paulo'),
        # Austin
        ('austin', 'americas'),
        # Spa-Francorchamps
        ('spa-francorchamps', 'spa'),
        # Hungaroring
        ('hungaroring', 'budapest'),
        # Spielberg
        ('spielberg', 'red_bull_ring'),
        # Montreal
        ('montréal', 'villeneuve'),
        # Catalunya
        ('catalunya', 'barcelona'),
        # Monaco
        ('monaco', 'monte_carlo'),
        # Miami
        ('miami', 'miami_gardens'),
        # Melbourne
        ('melbourne', 'albert_park'),
    ]

    merged = 0
    deleted = 0

    for keep_id, remove_id in duplicates:
        try:
            keep_circuit = Circuit.objects.filter(circuit_id=keep_id).first()
            remove_circuit = Circuit.objects.filter(circuit_id=remove_id).first()

            if not remove_circuit:
                continue

            if keep_circuit:
                # Mesclar dados - manter os dados mais completos
                if remove_circuit.first_grand_prix and not keep_circuit.first_grand_prix:
                    keep_circuit.first_grand_prix = remove_circuit.first_grand_prix
                if remove_circuit.total_races_held and not keep_circuit.total_races_held:
                    keep_circuit.total_races_held = remove_circuit.total_races_held
                if remove_circuit.description and not keep_circuit.description:
                    keep_circuit.description = remove_circuit.description
                if remove_circuit.history and not keep_circuit.history:
                    keep_circuit.history = remove_circuit.history
                if remove_circuit.length_km and not keep_circuit.length_km:
                    keep_circuit.length_km = remove_circuit.length_km
                if remove_circuit.number_of_corners and not keep_circuit.number_of_corners:
                    keep_circuit.number_of_corners = remove_circuit.number_of_corners
                if remove_circuit.lap_record and not keep_circuit.lap_record:
                    keep_circuit.lap_record = remove_circuit.lap_record
                    keep_circuit.lap_record_driver = remove_circuit.lap_record_driver
                    keep_circuit.lap_record_year = remove_circuit.lap_record_year

                keep_circuit.save()
                merged += 1
                logger.info(f"Merged data from {remove_id} into {keep_id}")

            # Remover circuito duplicado
            remove_circuit.delete()
            deleted += 1
            logger.info(f"Deleted duplicate circuit: {remove_id}")

        except Exception as e:
            logger.error(f"Error consolidating {keep_id}/{remove_id}: {e}")

    # Deletar circuitos órfãos sem layout (duplicatas que podem ser recriadas)
    orphan_ids = [
        'barcelona', 'budapest', 'le_castellet', 'monte_carlo', 'sakhir',
        'yas_island', 'mexico_city', 'são_paulo', 'sao_paulo'
    ]
    orphans = Circuit.objects.filter(circuit_id__in=orphan_ids)
    orphan_count = orphans.count()
    if orphan_count > 0:
        orphans.delete()
        deleted += orphan_count
        logger.info(f"Deleted {orphan_count} orphan circuits")

    result = {
        'status': 'success',
        'merged': merged,
        'deleted': deleted,
        'timestamp': timezone.now().isoformat()
    }

    logger.info(f"Circuit consolidation completed: {result}")
    return result


@shared_task(bind=True, max_retries=2)
def enrich_incomplete_circuits_data(self):
    """
    Preenche dados técnicos/históricos e o layout dos circuitos que foram
    criados apenas com nome/local/país pela coleta de sessões do FastF1
    (ex.: circuitos novos como o Madring, que entram no calendário antes de
    aparecerem enriquecidos no banco).

    Não cria circuitos novos - isso já é feito por
    ``data_collector.tasks.get_or_create_circuit`` durante a coleta de sessões.
    """
    from django.core.management import call_command
    from django.db.models import Q

    logger.info("Starting enrichment of incomplete circuits")

    incomplete = Circuit.objects.filter(
        Q(length_km__isnull=True) | Q(description='') | Q(layout_id='') | Q(layout_id__isnull=True)
    )

    enriched = []
    for circuit in incomplete:
        if not circuit.total_races_held:
            history_data = fetch_circuit_race_history(circuit.circuit_id)
            if history_data:
                circuit.first_grand_prix = history_data.get('first_grand_prix', circuit.first_grand_prix)
                circuit.total_races_held = history_data.get('total_races_held', circuit.total_races_held)

        if not circuit.description or not circuit.history:
            wiki_title = CIRCUIT_WIKIPEDIA_TITLE_OVERRIDES.get(circuit.circuit_id, circuit.name)
            wiki_data = fetch_circuit_info_wikipedia(wiki_title)
            if wiki_data:
                circuit.description = circuit.description or wiki_data.get('description', '')
                circuit.history = circuit.history or wiki_data.get('history', '')

        circuit.save()
        enriched.append(circuit.circuit_id)
        logger.info(f"Enriched circuit data: {circuit.name}")
        time.sleep(0.5)  # evita 429 (rate limit) na jolpica/Wikipedia

    # Resolve layout_id via circuits.json e baixa os SVGs que ainda faltam
    try:
        call_command('download_circuit_previews')
    except Exception as e:
        logger.error(f"Error downloading circuit previews: {e}")

    result = {
        'status': 'success',
        'enriched': enriched,
        'total_enriched': len(enriched),
        'timestamp': timezone.now().isoformat(),
    }

    logger.info(f"Circuit enrichment completed: {result}")
    return result
