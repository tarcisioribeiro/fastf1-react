"""
Script de teste para verificar a ingestão de dados históricos.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from data_collector.jolpica_client import JolpicaF1Client, parse_time_string
from data_collector.historical_processor import HistoricalDataProcessor

def test_api_client():
    """Testa cliente da API Jolpica."""
    print("=== Testando Cliente API Jolpica ===\n")

    client = JolpicaF1Client(rate_limit_delay=0.1)

    # Teste 1: Buscar temporadas
    print("1. Buscando temporadas disponíveis...")
    try:
        seasons = client.get_seasons()
        print(f"   ✓ {len(seasons)} temporadas encontradas")
        print(f"   Primeira: {seasons[0].get('season')}, Última: {seasons[-1].get('season')}\n")
    except Exception as e:
        print(f"   ✗ Erro: {e}\n")
        return False

    # Teste 2: Buscar corridas de 2010
    print("2. Buscando corridas de 2010...")
    try:
        races = client.get_races(2010)
        print(f"   ✓ {len(races)} corridas encontradas")
        if races:
            first_race = races[0]
            print(f"   Primeira corrida: {first_race.get('raceName')} em {first_race.get('Circuit', {}).get('circuitName')}\n")
    except Exception as e:
        print(f"   ✗ Erro: {e}\n")
        return False

    # Teste 3: Buscar resultados de uma corrida
    print("3. Buscando resultados da primeira corrida de 2010...")
    try:
        results = client.get_race_results(2010, 1)
        print(f"   ✓ {len(results)} resultados encontrados")
        if results:
            winner = results[0]
            driver = winner.get('Driver', {})
            print(f"   Vencedor: {driver.get('givenName')} {driver.get('familyName')}\n")
    except Exception as e:
        print(f"   ✗ Erro: {e}\n")
        return False

    # Teste 4: Buscar pilotos
    print("4. Buscando pilotos de 2010...")
    try:
        drivers = client.get_drivers(2010)
        print(f"   ✓ {len(drivers)} pilotos encontrados\n")
    except Exception as e:
        print(f"   ✗ Erro: {e}\n")
        return False

    # Teste 5: Buscar construtores
    print("5. Buscando construtores de 2010...")
    try:
        constructors = client.get_constructors(2010)
        print(f"   ✓ {len(constructors)} construtores encontrados\n")
    except Exception as e:
        print(f"   ✗ Erro: {e}\n")
        return False

    print("✓ Todos os testes de API passaram!\n")
    return True


def test_time_parsing():
    """Testa parsing de strings de tempo."""
    print("=== Testando Parsing de Tempo ===\n")

    test_cases = [
        ("1:23:45.678", "1h 23m 45.678s"),
        ("23:45.678", "23m 45.678s"),
        ("45.678", "45.678s"),
        ("+1.234", "+1.234s (gap)"),
    ]

    for time_str, description in test_cases:
        result = parse_time_string(time_str)
        if result:
            print(f"   ✓ '{time_str}' → {result.total_seconds()}s ({description})")
        else:
            print(f"   ✗ '{time_str}' falhou")

    print()


def test_processor():
    """Testa processador de dados históricos."""
    print("=== Testando Processador de Dados ===\n")

    processor = HistoricalDataProcessor()

    # Teste: Processar um piloto
    print("1. Processando piloto de teste...")
    test_driver = {
        'driverId': 'alonso',
        'givenName': 'Fernando',
        'familyName': 'Alonso',
        'dateOfBirth': '1981-07-29',
        'nationality': 'Spanish',
        'code': 'ALO',
    }

    try:
        driver = processor.process_driver(test_driver)
        print(f"   ✓ Piloto criado: {driver.full_name} ({driver.code})")
        print(f"   ID: {driver.driver_id}, Número: {driver.number}\n")
    except Exception as e:
        print(f"   ✗ Erro: {e}\n")
        return False

    # Teste: Processar uma equipe
    print("2. Processando equipe de teste...")
    test_constructor = {
        'constructorId': 'ferrari',
        'name': 'Ferrari',
        'nationality': 'Italian',
    }

    try:
        team = processor.process_team(test_constructor)
        print(f"   ✓ Equipe criada: {team.name}")
        print(f"   ID: {team.team_id}, Cor: {team.color}\n")
    except Exception as e:
        print(f"   ✗ Erro: {e}\n")
        return False

    # Teste: Processar um circuito
    print("3. Processando circuito de teste...")
    test_circuit = {
        'circuitId': 'monza',
        'circuitName': 'Autodromo Nazionale di Monza',
        'Location': {
            'locality': 'Monza',
            'country': 'Italy',
            'lat': '45.6156',
            'long': '9.28111',
        }
    }

    try:
        circuit = processor.process_circuit(test_circuit)
        print(f"   ✓ Circuito criado: {circuit.name}")
        print(f"   ID: {circuit.circuit_id}, Local: {circuit.location}, {circuit.country}\n")
    except Exception as e:
        print(f"   ✗ Erro: {e}\n")
        return False

    print("✓ Todos os testes de processamento passaram!\n")
    return True


def main():
    """Executa todos os testes."""
    print("\n" + "="*60)
    print("TESTE DE INGESTÃO DE DADOS HISTÓRICOS F1")
    print("="*60 + "\n")

    # Teste 1: API Client
    api_ok = test_api_client()

    # Teste 2: Time Parsing
    test_time_parsing()

    # Teste 3: Processor
    processor_ok = test_processor()

    # Resultado final
    print("="*60)
    if api_ok and processor_ok:
        print("✓ TODOS OS TESTES PASSARAM!")
        print("\nSistema pronto para ingestão de dados históricos.")
        print("\nPróximos passos:")
        print("1. Execute: python manage.py ingest_historical_data --mode metadata")
        print("2. Execute: python manage.py ingest_historical_data --mode season --year 2010")
        print("3. Ou execute ingestão completa: python manage.py ingest_historical_data --mode complete")
    else:
        print("✗ ALGUNS TESTES FALHARAM")
        print("\nVerifique os erros acima antes de prosseguir.")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
