import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.views import get_teams_by_name_or_operation
from core.models import TeamOperation

team_name = 'Kick Sauber'
print(f"Testing get_teams_by_name_or_operation('{team_name}')")

teams = get_teams_by_name_or_operation(team_name)
print(f"\nTeams returned: {teams.count()}")
for t in teams:
    print(f"  - ID {t.id}: {t.name}")

# Verificar se pertence a uma operação
if teams.exists():
    first_team = teams.first()
    team_operation = TeamOperation.objects.filter(teams=first_team).first()

    if team_operation:
        print(f"\nTeamOperation found:")
        print(f"  operation_name: {team_operation.operation_name}")
        print(f"  primary_team: {team_operation.primary_team.name if team_operation.primary_team else 'None'}")
    else:
        print("\nNo TeamOperation found for these teams")
