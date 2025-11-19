import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import TeamOperation, Team

# Buscar operação
op = TeamOperation.objects.filter(operation_name__icontains='Kick').first()
if op:
    print(f"Operation Name: {op.operation_name}")
    print(f"Primary Team: {op.primary_team.name if op.primary_team else 'None'}")
    print(f"Teams in operation:")
    for t in op.teams.all():
        print(f"  - ID {t.id}: {t.name}")
else:
    print("Operation not found")

# Buscar se existe uma equipe chamada "Kick Sauber"
team = Team.objects.filter(name__iexact='Kick Sauber').first()
if team:
    print(f"\nTeam 'Kick Sauber' found: ID {team.id}")
    # Verificar se pertence a alguma operação
    operations = TeamOperation.objects.filter(teams=team)
    print(f"Belongs to {operations.count()} operation(s)")
    for op in operations:
        print(f"  - {op.operation_name}")
