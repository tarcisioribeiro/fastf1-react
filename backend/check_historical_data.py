import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Season, Event, RaceResult, HistoricalDataCollectionConfig, HistoricalDataGap

print("=" * 80)
print("VERIFICAÇÃO DE DADOS HISTÓRICOS")
print("=" * 80)

# 1. Verificar temporadas
seasons = Season.objects.all().order_by('year')
print(f"\n1. TEMPORADAS NO BANCO:")
print(f"   Total: {seasons.count()}")
if seasons.exists():
    years = list(seasons.values_list('year', flat=True))
    print(f"   Período: {min(years)} - {max(years)}")
    print(f"   Anos: {years}")

    # Temporadas antes de 2018
    old_seasons = Season.objects.filter(year__lt=2018).order_by('year')
    print(f"\n   Temporadas < 2018: {old_seasons.count()}")
    if old_seasons.exists():
        old_years = list(old_seasons.values_list('year', flat=True))
        print(f"   Anos: {old_years}")

# 2. Verificar eventos
events = Event.objects.all()
print(f"\n2. EVENTOS/GPs NO BANCO:")
print(f"   Total: {events.count()}")
old_events = Event.objects.filter(season__year__lt=2018)
print(f"   Eventos < 2018: {old_events.count()}")

# 3. Verificar resultados de corrida
races = RaceResult.objects.all()
print(f"\n3. RESULTADOS DE CORRIDA:")
print(f"   Total: {races.count()}")
old_races = RaceResult.objects.filter(session__event__season__year__lt=2018)
print(f"   Resultados < 2018: {old_races.count()}")

# 4. Verificar configuração
print(f"\n4. CONFIGURAÇÃO DE COLETA HISTÓRICA:")
try:
    config = HistoricalDataCollectionConfig.get_config()
    print(f"   Habilitado: {config.enabled}")
    print(f"   Período: {config.start_year} → {config.end_year}")
    print(f"   Max workers: {config.max_workers}")
    print(f"   Tasks per batch: {config.tasks_per_batch}")
    print(f"   Última varredura: {config.last_scan_at}")
    print(f"   Total registros coletados: {config.total_records_collected}")
    print(f"\n   Tipos de dados habilitados:")
    print(f"     - Corridas: {config.collect_races}")
    print(f"     - Qualifying: {config.collect_qualifying}")
    print(f"     - Sprints: {config.collect_sprints}")
    print(f"     - Standings: {config.collect_standings}")
    print(f"     - Drivers: {config.collect_drivers}")
    print(f"     - Teams: {config.collect_teams}")
    print(f"     - Circuits: {config.collect_circuits}")
except Exception as e:
    print(f"   ERRO: {e}")

# 5. Verificar gaps
print(f"\n5. GAPS IDENTIFICADOS:")
total_gaps = HistoricalDataGap.objects.count()
print(f"   Total de gaps: {total_gaps}")

if total_gaps > 0:
    pending = HistoricalDataGap.objects.filter(status='pending').count()
    collecting = HistoricalDataGap.objects.filter(status='collecting').count()
    completed = HistoricalDataGap.objects.filter(status='completed').count()
    failed = HistoricalDataGap.objects.filter(status='failed').count()
    skipped = HistoricalDataGap.objects.filter(status='skipped').count()

    print(f"\n   Por status:")
    print(f"     - Pendente: {pending}")
    print(f"     - Coletando: {collecting}")
    print(f"     - Completo: {completed}")
    print(f"     - Falhou: {failed}")
    print(f"     - Ignorado: {skipped}")

    # Por tipo
    from django.db.models import Count
    by_type = HistoricalDataGap.objects.values('gap_type').annotate(count=Count('id')).order_by('-count')
    print(f"\n   Por tipo:")
    for item in by_type:
        print(f"     - {item['gap_type']}: {item['count']}")

    # Alguns exemplos
    print(f"\n   Exemplos de gaps pendentes:")
    examples = HistoricalDataGap.objects.filter(status='pending').order_by('-priority')[:5]
    for gap in examples:
        print(f"     - [{gap.priority}] {gap.description}")

print("\n" + "=" * 80)
