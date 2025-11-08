#!/usr/bin/env python
"""
Script para testar a coleta de pit stops com o código corrigido.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from data_collector.tasks import collect_session_data
from core.models import PitStop, Session

print("=" * 80)
print("TESTE DE COLETA DE PIT STOPS")
print("=" * 80)
print()

# Testar com Bahrain 2024 Round 1
year = 2024
round_num = 1
session_type = 'R'

print(f"Limpando pit stops existentes para {year} Round {round_num}...")
session_id = f"{year}_{round_num}_R"
try:
    session_obj = Session.objects.get(session_id=session_id)
    deleted_count = PitStop.objects.filter(session=session_obj).delete()[0]
    print(f"✓ Removidos {deleted_count} pit stops antigos")
except Session.DoesNotExist:
    print(f"⚠ Sessão {session_id} não existe ainda")

print()
print(f"Coletando dados para {year} Round {round_num} {session_type}...")
print()

# Executar a coleta
result = collect_session_data(year, round_num, session_type)

print()
print("=" * 80)
print("RESULTADO DA COLETA")
print("=" * 80)
print()

# Verificar resultados
try:
    session_obj = Session.objects.get(session_id=session_id)
    pit_stops = PitStop.objects.filter(session=session_obj)

    print(f"Total de pit stops: {pit_stops.count()}")
    print()

    # Estatísticas
    with_duration = pit_stops.filter(duration__isnull=False).count()
    without_duration = pit_stops.filter(duration__isnull=True).count()

    print(f"Pit stops COM duração: {with_duration}")
    print(f"Pit stops SEM duração: {without_duration}")
    print()

    if with_duration > 0:
        # Mostrar exemplos
        print("Exemplos de pit stops com duração:")
        print("-" * 80)
        samples = pit_stops.filter(duration__isnull=False)[:5]
        for ps in samples:
            print(f"  {ps.driver.code:4s} | Lap {ps.lap:2d} | Stop #{ps.stop_number} | "
                  f"Duration: {ps.duration.total_seconds():.3f}s | Team: {ps.team.name}")

        print()
        print("✅ SUCESSO! Pit stops estão sendo coletados com duração!")
    else:
        print("❌ ERRO! Nenhum pit stop foi coletado com duração.")

    print()
    print("=" * 80)

except Session.DoesNotExist:
    print(f"❌ Sessão {session_id} não foi criada")
except Exception as e:
    print(f"❌ Erro ao verificar resultados: {e}")
