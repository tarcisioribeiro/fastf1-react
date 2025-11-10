#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Team, RaceResult, QualifyingResult
from django.db.models import Count, Min, Max

print("=" * 80)
print("ANÁLISE DE EQUIPES DUPLICADAS")
print("=" * 80)

# Verificar equipes com nomes similares ou duplicados
teams = Team.objects.all().order_by('name')
print(f"\nTotal de equipes: {teams.count()}")

# Agrupar por canonical_name ou nome similar
print("\nEquipes ordenadas por nome:")
for team in teams[:30]:
    race_results = RaceResult.objects.filter(team=team).count()
    quali_results = QualifyingResult.objects.filter(team=team).count()

    # Verificar período de atividade
    first_race = RaceResult.objects.filter(team=team).select_related('session__event__season').order_by('session__event__event_date').first()
    last_race = RaceResult.objects.filter(team=team).select_related('session__event__season').order_by('-session__event__event_date').first()

    year_range = "Sem corridas"
    if first_race and last_race:
        year_range = f"{first_race.session.event.season.year}-{last_race.session.event.season.year}"

    canonical = team.canonical_name or "-"
    print(f"  {team.name:40} | Canonical: {canonical:20} | {race_results:4} resultados | {year_range}")

# Verificar equipes que deveriam ser consolidadas
print("\n" + "=" * 80)
print("EQUIPES QUE PODEM SER CONSOLIDADAS")
print("-" * 80)

# Exemplos conhecidos de consolidação
consolidation_groups = {
    "Red Bull": ["Red Bull", "Red Bull Racing"],
    "Alpine": ["Alpine", "Alpine F1 Team", "Renault"],
    "Aston Martin": ["Aston Martin", "Force India", "Racing Point"],
    "Kick Sauber": ["Kick Sauber", "Alfa Romeo", "Alfa Romeo Racing", "Sauber"],
    "Racing Bulls": ["Racing Bulls", "RB", "AlphaTauri", "RB F1 Team", "Toro Rosso"],
}

for canonical, names in consolidation_groups.items():
    print(f"\n{canonical}:")
    for name in names:
        teams_found = Team.objects.filter(name__icontains=name)
        for team in teams_found:
            race_results = RaceResult.objects.filter(team=team).count()
            print(f"  - {team.name} (ID {team.id}): {race_results} resultados")
