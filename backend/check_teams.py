from core.models import Team, ConstructorStanding

teams = Team.objects.filter(id__in=[7, 12, 16, 19])

for t in teams:
    count = ConstructorStanding.objects.filter(team=t).count()
    years = ConstructorStanding.objects.filter(team=t).values_list('season__year', flat=True).distinct().order_by('season__year')
    print(f'{t.name}: {count} standings, years: {list(years)}')
