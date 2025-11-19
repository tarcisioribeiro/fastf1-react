import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.views import get_teams_by_name_or_operation
from core.models import TeamOperation

team_name = 'Kick Sauber'
teams = get_teams_by_name_or_operation(team_name)

print(f"Teams: {teams.count()}")

# Simular o código da view
team_operation = None
first_team = teams.first()
if first_team:
    team_operation = TeamOperation.objects.filter(teams=first_team).first()

print(f"TeamOperation found: {team_operation is not None}")

if team_operation:
    canonical_name = team_operation.operation_name
    current_name = team_operation.primary_team.name if team_operation.primary_team else team_operation.operation_name
    color = team_operation.primary_team.color if team_operation.primary_team else (teams.first().color if teams.exists() else '#000000')

    print(f"\nUsing TeamOperation:")
    print(f"  canonical_name: {canonical_name}")
    print(f"  current_name: {current_name}")
    print(f"  color: {color}")
else:
    main_team = teams.filter(display_in_filters=True).first()
    if not main_team:
        main_team = teams.order_by('-id').first()

    canonical_name = main_team.current_name or main_team.name
    current_name = main_team.current_name or main_team.name
    color = main_team.color

    print(f"\nUsing main_team:")
    print(f"  canonical_name: {canonical_name}")
    print(f"  current_name: {current_name}")
    print(f"  color: {color}")
