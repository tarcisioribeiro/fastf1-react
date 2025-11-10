#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Driver, RaceResult, QualifyingResult, DriverStanding
from django.db.models import Count, Min, Max

# Analisar drivers duplicados e suas corridas
print("=" * 80)
print("ANÁLISE DE DRIVERS DUPLICADOS E DADOS HISTÓRICOS")
print("=" * 80)

# Drivers duplicados
duplicates = Driver.objects.values('code').annotate(
    count=Count('id'),
    min_id=Min('id'),
    max_id=Max('id')
).filter(count__gt=1).order_by('-count')

print(f"\n1. DRIVERS COM MÚLTIPLOS REGISTROS: {duplicates.count()}")
print("-" * 80)

for dup in duplicates[:10]:
    code = dup['code']
    drivers = Driver.objects.filter(code=code).order_by('id')

    print(f"\nCódigo: {code} ({dup['count']} registros)")
    for driver in drivers:
        # Contar resultados de corrida
        race_results = RaceResult.objects.filter(driver=driver).count()
        quali_results = QualifyingResult.objects.filter(driver=driver).count()

        # Verificar ano de atividade
        first_race = RaceResult.objects.filter(driver=driver).select_related('session__event__season').order_by('session__event__event_date').first()
        last_race = RaceResult.objects.filter(driver=driver).select_related('session__event__season').order_by('-session__event__event_date').first()

        year_range = "Sem corridas"
        if first_race and last_race:
            year_range = f"{first_race.session.event.season.year}-{last_race.session.event.season.year}"

        print(f"  ID {driver.id}: {driver.full_name} (#{driver.number})")
        print(f"    - Corridas: {race_results}, Quali: {quali_results}")
        print(f"    - Período: {year_range}")
        print(f"    - driver_id: {driver.driver_id}")

# Verificar distribuição de dados por ano
print("\n" + "=" * 80)
print("2. DISTRIBUIÇÃO DE DADOS POR ANO")
print("-" * 80)

from django.db.models import Count
from core.models import Event, Season

years_data = Season.objects.values('year').annotate(
    events_count=Count('events')
).order_by('year')

print("\nEventos por ano:")
for year_data in years_data[:20]:
    year = year_data['year']
    events = year_data['events_count']

    # Contar resultados desse ano
    race_results = RaceResult.objects.filter(session__event__season__year=year).count()
    quali_results = QualifyingResult.objects.filter(session__event__season__year=year).count()

    print(f"  {year}: {events} eventos, {race_results} race results, {quali_results} quali results")

# Verificar se há dados duplicados entre períodos
print("\n" + "=" * 80)
print("3. VERIFICAR SOBREPOSIÇÃO DE DADOS")
print("-" * 80)

# Verificar 2018 (primeiro ano da FastF1)
results_2018 = RaceResult.objects.filter(session__event__season__year=2018).select_related('driver').values('driver__code').distinct()
print(f"\nDrivers com resultados em 2018: {results_2018.count()}")

# Ver alguns exemplos
sample_2018_drivers = list(results_2018[:5])
for driver_data in sample_2018_drivers:
    code = driver_data['driver__code']
    drivers_with_code = Driver.objects.filter(code=code)
    print(f"\n  Código {code}:")
    for driver in drivers_with_code:
        results = RaceResult.objects.filter(driver=driver, session__event__season__year=2018).count()
        print(f"    ID {driver.id} ({driver.full_name}): {results} resultados em 2018")
