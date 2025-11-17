"""
Django models for F1 data.
Covers historical data from 1950 onwards (via Jolpica API for 1950-2017, FastF1 for 2018+).
Tyre strategies available from 2025 onwards.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Team(models.Model):
    """F1 Team/Constructor model."""
    team_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200, blank=True)
    canonical_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nome consolidado da equipe para análises históricas. Ex: 'Alpine' para Renault/Alpine F1 Team"
    )
    color = models.CharField(max_length=7, help_text="Hex color code (e.g., #FF0000)")
    color_secondary = models.CharField(max_length=7, blank=True, help_text="Secondary hex color")

    # Campos de consolidação de equipes
    operation_line_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="ID da linha de operação (ex: 1=Ferrari, 2=Mercedes, etc.)"
    )

    current_name = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Nome mais recente da operação (para exibição nos filtros)"
    )

    display_in_filters = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Se True, mostra nos filtros da UI. False para nomes históricos."
    )

    is_engine_variant = models.BooleanField(
        default=False,
        help_text="True se for apenas variação de motor (ex: Cooper-Climax)"
    )

    predecessor = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='successors',
        help_text="Equipe predecessora na linha de sucessão"
    )

    years_active = models.CharField(
        max_length=50,
        blank=True,
        help_text="Anos em que este nome foi usado (ex: '1997-1999')"
    )

    team_status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Ativa'),
            ('RENAMED', 'Renomeada'),
            ('EXTINCT', 'Extinta'),
            ('MERGED', 'Fundida'),
        ],
        default='ACTIVE',
        help_text="Status atual da equipe"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Mapeamento de consolidação de equipes (histórico completo 1950-2025)
    # Formato: "Nome Atual/Canônico": ["Lista", "de", "nomes", "históricos"]
    TEAM_CONSOLIDATION_MAP = {
        # Red Bull Racing: Stewart (1997-1999) → Jaguar (2000-2004) → Red Bull (2005-presente)
        "Red Bull Racing": [
            "Red Bull",
            "Jaguar",
            "Jaguar Racing",
            "Stewart",
            "Stewart Grand Prix",
            "Stewart-Ford",
        ],

        # Mercedes: Tyrrell (1970-1998) → BAR (1999-2005) → Honda (2006-2008) → Brawn (2009) → Mercedes (2010-presente)
        "Mercedes": [
            "Mercedes-AMG Petronas",
            "Mercedes GP",
            "Mercedes-Benz",
            "Brawn GP",
            "Brawn",
            "Honda",
            "Honda Racing",
            "Honda Racing F1",
            "BAR",
            "British American Racing",
            "BAR-Honda",
            "Lucky Strike BAR",
            "Tyrrell",
            "Tyrrell Racing",
        ],

        # Alpine: Toleman (1981-1985) → Benetton (1986-2001) → Renault (2002-2011) → Lotus (2012-2015) → Renault (2016-2020) → Alpine (2021-presente)
        "Alpine": [
            "Alpine F1 Team",
            "Renault",
            "Renault F1",
            "Renault F1 Team",
            "ING Renault F1",
            "Mild Seven Renault F1",
            "Lotus F1",
            "Lotus F1 Team",
            "Lotus",
            "Benetton",
            "Benetton Formula",
            "Mild Seven Benetton",
            "Toleman",
            "Toleman Group Motorsport",
        ],

        # Aston Martin: Jordan (1991-2005) → Midland (2006) → Spyker (2007) → Force India (2008-2018) → Racing Point (2019-2020) → Aston Martin (2021-presente)
        "Aston Martin": [
            "Aston Martin Aramco",
            "Racing Point",
            "Racing Point F1",
            "SportPesa Racing Point",
            "BWT Racing Point",
            "Force India",
            "Sahara Force India",
            "Kingfisher Force India",
            "Spyker",
            "Spyker F1",
            "Midland",
            "Midland F1",
            "Jordan",
            "Jordan Grand Prix",
            "Benson & Hedges Jordan",
        ],

        # Racing Bulls: Minardi (1985-2005) → Toro Rosso (2006-2019) → AlphaTauri (2020-2023) → RB (2024) → Racing Bulls (2025-presente)
        "Racing Bulls": [
            "RB",
            "RB F1 Team",
            "AlphaTauri",
            "Scuderia AlphaTauri",
            "Toro Rosso",
            "Scuderia Toro Rosso",
            "STR",
            "Minardi",
            "Minardi F1",
            "European Minardi",
        ],

        # Kick Sauber: Sauber (1993-2005) → BMW Sauber (2006-2010) → Sauber (2011-2018) → Alfa Romeo (2019-2023) → Kick Sauber (2024-presente)
        "Kick Sauber": [
            "Stake F1 Team",
            "Alfa Romeo",
            "Alfa Romeo Racing",
            "Alfa Romeo Racing ORLEN",
            "Sauber",
            "Sauber F1",
            "BMW Sauber",
            "BMW Sauber F1",
        ],

        # Ferrari: contínuo desde 1950
        "Ferrari": [
            "Scuderia Ferrari",
            "Scuderia Ferrari HP",
            "Scuderia Ferrari Mission Winnow",
            "Ferrari Marlboro",
        ],

        # McLaren: contínuo desde 1966
        "McLaren": [
            "McLaren F1",
            "McLaren F1 Team",
            "McLaren Mercedes",
            "McLaren Racing",
            "Vodafone McLaren Mercedes",
            "West McLaren Mercedes",
            "Marlboro McLaren",
        ],

        # Williams: contínuo desde 1975 (1978 em F1)
        "Williams": [
            "Williams F1",
            "Williams Racing",
            "Williams Grand Prix Engineering",
            "AT&T Williams",
            "Rothmans Williams",
            "Canon Williams",
        ],

        # Haas: estreia em 2016
        "Haas": [
            "Haas F1 Team",
            "MoneyGram Haas F1",
            "Uralkali Haas F1",
            "Rich Energy Haas F1",
        ],

        # Equipes históricas extintas (não têm sucessoras atuais)

        # Brabham: 1962-1992 (extinta)
        "Brabham": [
            "Motor Racing Developments",
            "MRD",
            "Brabham Racing",
            "Brabham-Repco",
            "Brabham-Ford",
            "Brabham-Alfa Romeo",
            "Brabham-BMW",
        ],

        # Cooper: 1950-1969 (extinta)
        "Cooper": [
            "Cooper Car Company",
            "Cooper-Climax",
            "Cooper-Maserati",
            "Cooper-BRM",
        ],

        # Lotus (Team Lotus original): 1958-1994 (extinta)
        # Nota: Lotus F1 Team (2012-2015) já está mapeada para Alpine
        "Team Lotus": [
            "Team Lotus",
            "Lotus-Climax",
            "Lotus-Ford",
            "Lotus-Renault",
            "Team Lotus-Honda",
            "Team Lotus-Judd",
            "Team Lotus-Mugen",
        ],

        # BRM: 1951-1977 (extinta)
        "BRM": [
            "British Racing Motors",
            "Owen Racing Organisation",
            "Stanley-BRM",
        ],

        # Outras equipes históricas importantes
        "Matra": [
            "Matra Sports",
            "Matra International",
            "Equipe Matra",
        ],

        "March": [
            "March Engineering",
            "March-Ford",
            "March-Cosworth",
        ],

        "Arrows": [
            "Arrows Grand Prix International",
            "Arrows Racing",
            "Footwork",
            "Footwork Arrows",
        ],

        "Ligier": [
            "Equipe Ligier",
            "Ligier-Renault",
            "Ligier-Mugen",
        ],

        "Prost": [
            "Prost Grand Prix",
            "Prost-Peugeot",
            "Prost-Acer",
        ],
    }

    class Meta:
        ordering = ['name']
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'
        indexes = [
            models.Index(fields=['operation_line_id']),
            models.Index(fields=['display_in_filters']),
            models.Index(fields=['current_name']),
        ]

    def __str__(self):
        return self.name

    @classmethod
    def get_canonical_name(cls, team_name):
        """
        Retorna o nome canônico (consolidado) de uma equipe.
        Se a equipe não está no mapeamento, retorna o próprio nome.
        """
        if not team_name:
            return team_name

        # Verifica se o nome já é um nome canônico
        for canonical, aliases in cls.TEAM_CONSOLIDATION_MAP.items():
            if team_name == canonical:
                return canonical
            # Verifica se é um alias
            if team_name in aliases:
                return canonical

        # Se não encontrou, retorna o próprio nome
        return team_name

    def get_consolidated_name(self):
        """
        Retorna o nome consolidado desta equipe.
        Se canonical_name está definido, usa ele. Senão, usa o mapeamento.
        """
        if self.canonical_name:
            return self.canonical_name
        return self.get_canonical_name(self.name)

    def get_succession_line(self):
        """
        Retorna a linha completa de sucessão desta equipe.
        Retorna lista de dicionários com: name, years_active, is_current
        """
        if not self.operation_line_id:
            return [{'name': self.name, 'years_active': self.years_active or '', 'is_current': True}]

        # Buscar todas as equipes da mesma operação
        teams_in_operation = Team.objects.filter(
            operation_line_id=self.operation_line_id
        ).order_by('id')  # Ordenar por ID geralmente mantém ordem cronológica

        succession = []
        for team in teams_in_operation:
            succession.append({
                'name': team.name,
                'years_active': team.years_active or '',
                'is_current': team.display_in_filters,
                'status': team.team_status
            })

        return succession


class Driver(models.Model):
    """F1 Driver model."""
    driver_id = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=3, unique=True, help_text="3-letter driver code (e.g., VER, HAM)")
    number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)])
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Driver'
        verbose_name_plural = 'Drivers'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.code})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Circuit(models.Model):
    """F1 Circuit model."""
    circuit_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    length_km = models.FloatField(null=True, blank=True, help_text="Circuit length in kilometers")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Circuit'
        verbose_name_plural = 'Circuits'

    def __str__(self):
        return f"{self.name} ({self.country})"


class Season(models.Model):
    """F1 Season model."""
    year = models.IntegerField(unique=True, validators=[MinValueValidator(1950)])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year']
        verbose_name = 'Season'
        verbose_name_plural = 'Seasons'

    def __str__(self):
        return str(self.year)


class Event(models.Model):
    """F1 Event/Grand Prix model."""
    EVENT_TYPE_CHOICES = [
        ('race', 'Race Weekend'),
        ('sprint', 'Sprint Weekend'),
        ('testing', 'Testing'),
    ]

    event_id = models.CharField(max_length=50, unique=True)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='events')
    round_number = models.IntegerField(validators=[MinValueValidator(1)])
    circuit = models.ForeignKey(Circuit, on_delete=models.CASCADE, related_name='events')
    event_name = models.CharField(max_length=200, help_text="Official event name")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='race')
    event_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['season', 'round_number']
        unique_together = ['season', 'round_number']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        indexes = [
            models.Index(fields=['season', 'round_number']),
            models.Index(fields=['event_date']),
        ]

    def __str__(self):
        return f"{self.season.year} - Round {self.round_number}: {self.event_name}"


class Session(models.Model):
    """F1 Session model (Practice, Qualifying, Sprint, Race)."""
    SESSION_TYPE_CHOICES = [
        ('FP1', 'Free Practice 1'),
        ('FP2', 'Free Practice 2'),
        ('FP3', 'Free Practice 3'),
        ('Q', 'Qualifying'),
        ('S', 'Sprint'),
        ('SQ', 'Sprint Qualifying'),
        ('R', 'Race'),
    ]

    session_id = models.CharField(max_length=100, unique=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sessions')
    session_type = models.CharField(max_length=3, choices=SESSION_TYPE_CHOICES)
    session_date = models.DateTimeField()

    # Metadata
    is_complete = models.BooleanField(default=False)
    data_collected = models.BooleanField(default=False)
    collection_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['event', 'session_date']
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'
        indexes = [
            models.Index(fields=['event', 'session_type']),
            models.Index(fields=['session_date']),
        ]

    def __str__(self):
        return f"{self.event.event_name} - {self.get_session_type_display()}"


class RaceResult(models.Model):
    """Race result for each driver."""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='race_results')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='race_results')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='race_results')

    position = models.IntegerField(validators=[MinValueValidator(1)])
    grid_position = models.IntegerField(null=True, blank=True)
    points = models.FloatField(default=0.0)
    laps_completed = models.IntegerField(default=0)

    # Time data
    total_race_time = models.DurationField(null=True, blank=True)
    fastest_lap_time = models.DurationField(null=True, blank=True)
    fastest_lap_number = models.IntegerField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=50, default='Finished')
    dnf = models.BooleanField(default=False, help_text="Did Not Finish")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['session', 'position']
        unique_together = ['session', 'driver']
        verbose_name = 'Race Result'
        verbose_name_plural = 'Race Results'
        indexes = [
            models.Index(fields=['session', 'position']),
        ]

    def __str__(self):
        return f"P{self.position} - {self.driver.full_name} ({self.session})"


class QualifyingResult(models.Model):
    """Qualifying result for each driver."""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='qualifying_results')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='qualifying_results')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='qualifying_results')

    position = models.IntegerField(validators=[MinValueValidator(1)])

    # Session times
    q1_time = models.DurationField(null=True, blank=True)
    q2_time = models.DurationField(null=True, blank=True)
    q3_time = models.DurationField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['session', 'position']
        unique_together = ['session', 'driver']
        verbose_name = 'Qualifying Result'
        verbose_name_plural = 'Qualifying Results'
        indexes = [
            models.Index(fields=['session', 'position']),
        ]

    def __str__(self):
        return f"Q: P{self.position} - {self.driver.full_name} ({self.session})"


class SprintResult(models.Model):
    """Sprint race result for each driver."""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='sprint_results')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='sprint_results')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='sprint_results')

    position = models.IntegerField(validators=[MinValueValidator(1)])
    grid_position = models.IntegerField(null=True, blank=True)
    points = models.FloatField(default=0.0)
    laps_completed = models.IntegerField(default=0)

    # Time data
    total_sprint_time = models.DurationField(null=True, blank=True)
    fastest_lap_time = models.DurationField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=50, default='Finished')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['session', 'position']
        unique_together = ['session', 'driver']
        verbose_name = 'Sprint Result'
        verbose_name_plural = 'Sprint Results'
        indexes = [
            models.Index(fields=['session', 'position']),
        ]

    def __str__(self):
        return f"Sprint: P{self.position} - {self.driver.full_name} ({self.session})"


class DriverStanding(models.Model):
    """Driver championship standings after each event."""
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='driver_standings')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='driver_standings')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='standings')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='driver_standings')

    position = models.IntegerField(validators=[MinValueValidator(1)])
    points = models.FloatField(default=0.0)
    wins = models.IntegerField(default=0)
    podiums = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['season', 'event', 'position']
        unique_together = ['season', 'event', 'driver']
        verbose_name = 'Driver Standing'
        verbose_name_plural = 'Driver Standings'
        indexes = [
            models.Index(fields=['season', 'event', 'position']),
        ]

    def __str__(self):
        return f"{self.season.year} Round {self.event.round_number} - P{self.position}: {self.driver.full_name} ({self.points} pts)"


class ConstructorStanding(models.Model):
    """Constructor championship standings after each event."""
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='constructor_standings')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='constructor_standings')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='standings')

    position = models.IntegerField(validators=[MinValueValidator(1)])
    points = models.FloatField(default=0.0)
    wins = models.IntegerField(default=0)
    podiums = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['season', 'event', 'position']
        unique_together = ['season', 'event', 'team']
        verbose_name = 'Constructor Standing'
        verbose_name_plural = 'Constructor Standings'
        indexes = [
            models.Index(fields=['season', 'event', 'position']),
        ]

    def __str__(self):
        return f"{self.season.year} Round {self.event.round_number} - P{self.position}: {self.team.name} ({self.points} pts)"


class LapTime(models.Model):
    """Individual lap times for each driver in a session."""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='lap_times')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='lap_times')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='lap_times')

    lap_number = models.IntegerField(validators=[MinValueValidator(1)])
    lap_time = models.DurationField()
    sector1_time = models.DurationField(null=True, blank=True)
    sector2_time = models.DurationField(null=True, blank=True)
    sector3_time = models.DurationField(null=True, blank=True)

    # Lap characteristics
    is_personal_best = models.BooleanField(default=False)
    is_accurate = models.BooleanField(default=True, help_text="Whether the lap time is accurate")

    # Tyre info
    compound = models.CharField(max_length=20, blank=True, help_text="Tyre compound used")
    tyre_life = models.IntegerField(null=True, blank=True, help_text="Age of tyres in laps")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['session', 'lap_number', 'driver']
        unique_together = ['session', 'driver', 'lap_number']
        verbose_name = 'Lap Time'
        verbose_name_plural = 'Lap Times'
        indexes = [
            models.Index(fields=['session', 'driver']),
            models.Index(fields=['session', 'lap_number']),
        ]

    def __str__(self):
        return f"Lap {self.lap_number} - {self.driver.code}: {self.lap_time}"


class TyreStrategy(models.Model):
    """Tyre strategy and stint data for each driver (2025 onwards)."""
    COMPOUND_CHOICES = [
        ('SOFT', 'Soft'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
        ('INTERMEDIATE', 'Intermediate'),
        ('WET', 'Wet'),
    ]

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='tyre_strategies')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='tyre_strategies')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='tyre_strategies')

    stint_number = models.IntegerField(validators=[MinValueValidator(1)])
    compound = models.CharField(max_length=15, choices=COMPOUND_CHOICES)

    # Stint data
    start_lap = models.IntegerField(validators=[MinValueValidator(1)])
    end_lap = models.IntegerField(validators=[MinValueValidator(1)])
    stint_length = models.IntegerField(validators=[MinValueValidator(1)])

    # Performance
    avg_lap_time = models.DurationField(null=True, blank=True)
    fastest_lap_time = models.DurationField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['session', 'driver', 'stint_number']
        unique_together = ['session', 'driver', 'stint_number']
        verbose_name = 'Tyre Strategy'
        verbose_name_plural = 'Tyre Strategies'
        indexes = [
            models.Index(fields=['session', 'driver']),
        ]

    def __str__(self):
        return f"{self.driver.code} - Stint {self.stint_number}: {self.compound} (Laps {self.start_lap}-{self.end_lap})"


class PitStop(models.Model):
    """Pit stop data for each driver."""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='pit_stops')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='pit_stops')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='pit_stops')

    stop_number = models.IntegerField(validators=[MinValueValidator(1)])
    lap = models.IntegerField(validators=[MinValueValidator(1)])
    duration = models.DurationField(null=True, blank=True, help_text="Pit stop duration (can be null if not available)")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['session', 'lap']
        unique_together = ['session', 'driver', 'stop_number']
        verbose_name = 'Pit Stop'
        verbose_name_plural = 'Pit Stops'
        indexes = [
            models.Index(fields=['session', 'driver']),
        ]

    def __str__(self):
        return f"{self.driver.code} - Stop {self.stop_number} on Lap {self.lap}"


class WeatherData(models.Model):
    """Weather conditions during a session."""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='weather_data')

    timestamp = models.DateTimeField()
    air_temp = models.FloatField(help_text="Air temperature in Celsius")
    track_temp = models.FloatField(help_text="Track temperature in Celsius")
    humidity = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Humidity percentage")
    pressure = models.FloatField(help_text="Atmospheric pressure in mbar")
    rainfall = models.BooleanField(default=False)
    wind_speed = models.FloatField(null=True, blank=True, help_text="Wind speed in m/s")
    wind_direction = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(360)], help_text="Wind direction in degrees")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['session', 'timestamp']
        verbose_name = 'Weather Data'
        verbose_name_plural = 'Weather Data'
        indexes = [
            models.Index(fields=['session', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.session} - {self.timestamp}"


class TelemetryData(models.Model):
    """Telemetry data for driver laps (sampled data)."""
    lap_time = models.ForeignKey(LapTime, on_delete=models.CASCADE, related_name='telemetry')

    # Position on track
    distance = models.FloatField(help_text="Distance along track in meters")

    # Speed and performance
    speed = models.FloatField(help_text="Speed in km/h")
    throttle = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Throttle percentage")
    brake = models.BooleanField(default=False)
    drs = models.IntegerField(help_text="DRS status")
    gear = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(8)])

    # Engine data
    rpm = models.IntegerField(null=True, blank=True, help_text="Engine RPM")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['lap_time', 'distance']
        verbose_name = 'Telemetry Data'
        verbose_name_plural = 'Telemetry Data'
        indexes = [
            models.Index(fields=['lap_time', 'distance']),
        ]

    def __str__(self):
        return f"Telemetry - {self.lap_time} @ {self.distance}m"


class DataCollectionLog(models.Model):
    """
    Log de erros e warnings durante coleta de dados.
    Facilita rastreamento e correção de problemas.
    """
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]

    SOURCE_CHOICES = [
        ('FASTF1', 'FastF1 API'),
        ('JOLPICA', 'Jolpica/Ergast API'),
        ('ML', 'Machine Learning'),
        ('SYSTEM', 'System'),
    ]

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, db_index=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, db_index=True)
    task_name = models.CharField(max_length=200, help_text="Nome da tarefa Celery")
    message = models.TextField(help_text="Mensagem de log")
    exception_type = models.CharField(max_length=200, blank=True, help_text="Tipo da exceção (se houver)")
    traceback = models.TextField(blank=True, help_text="Stack trace completo")

    # Contexto adicional
    year = models.IntegerField(null=True, blank=True, help_text="Ano relacionado")
    round_number = models.IntegerField(null=True, blank=True, help_text="Número da rodada")
    session_type = models.CharField(max_length=50, blank=True, help_text="Tipo de sessão (R, Q, S, etc.)")

    # Metadata
    task_id = models.CharField(max_length=255, blank=True, help_text="ID da tarefa Celery")
    resolved = models.BooleanField(default=False, help_text="Problema resolvido?")
    resolution_notes = models.TextField(blank=True, help_text="Notas sobre a resolução")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Data Collection Log'
        verbose_name_plural = 'Data Collection Logs'
        indexes = [
            models.Index(fields=['-created_at', 'level']),
            models.Index(fields=['source', 'level']),
            models.Index(fields=['resolved', 'level']),
        ]

    def __str__(self):
        context = f"{self.year} R{self.round_number}" if self.year and self.round_number else "N/A"
        return f"[{self.level}] {self.source} - {self.task_name} ({context})"

    @classmethod
    def log_error(cls, source, task_name, message, exc=None, **context):
        """Registra um erro no banco."""
        return cls.objects.create(
            level='ERROR',
            source=source,
            task_name=task_name,
            message=message,
            exception_type=exc.__class__.__name__ if exc else '',
            traceback=str(exc) if exc else '',
            **context
        )

    @classmethod
    def log_warning(cls, source, task_name, message, **context):
        """Registra um warning no banco."""
        return cls.objects.create(
            level='WARNING',
            source=source,
            task_name=task_name,
            message=message,
            **context
        )

    @classmethod
    def log_info(cls, source, task_name, message, **context):
        """Registra uma informação no banco."""
        return cls.objects.create(
            level='INFO',
            source=source,
            task_name=task_name,
            message=message,
            **context
        )


class DataAuditReport(models.Model):
    """
    Relatório de auditoria de dados - identifica campos vazios/nulos
    e sugere preenchimentos com base em fontes públicas.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]

    # Metadata do relatório
    execution_date = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    execution_time_seconds = models.FloatField(null=True, blank=True, help_text="Tempo de execução em segundos")

    # Estatísticas da auditoria
    total_tables_scanned = models.IntegerField(default=0)
    total_fields_scanned = models.IntegerField(default=0)
    total_empty_fields_found = models.IntegerField(default=0)
    total_suggestions_found = models.IntegerField(default=0)

    # Resultados (JSON)
    audit_results = models.JSONField(
        default=dict,
        help_text="Resultados completos da auditoria em formato JSON"
    )

    # Logs e erros
    error_message = models.TextField(blank=True, help_text="Mensagem de erro se a execução falhou")

    class Meta:
        ordering = ['-execution_date']
        verbose_name = 'Data Audit Report'
        verbose_name_plural = 'Data Audit Reports'
        indexes = [
            models.Index(fields=['-execution_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Audit Report - {self.execution_date.strftime('%d/%m/%Y %H:%M')} ({self.status})"


class DataAuditSuggestion(models.Model):
    """
    Sugestão individual de preenchimento de dados encontrada pela auditoria.
    """
    report = models.ForeignKey(
        DataAuditReport,
        on_delete=models.CASCADE,
        related_name='suggestions'
    )

    # Localização do campo vazio
    table_name = models.CharField(max_length=100, db_index=True)
    field_name = models.CharField(max_length=100)
    record_id = models.IntegerField(help_text="ID do registro com campo vazio")
    record_identifier = models.CharField(
        max_length=200,
        help_text="Identificador legível do registro (ex: 'Max Verstappen', 'Monaco GP')"
    )

    # Valor atual (vazio/nulo)
    current_value = models.TextField(blank=True, null=True, help_text="Valor atual (geralmente vazio ou NULL)")

    # Sugestão encontrada
    suggested_value = models.TextField(help_text="Valor sugerido encontrado na web")
    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confiança da sugestão (0.0 a 1.0)"
    )

    # Fonte da informação
    source_name = models.CharField(max_length=100, help_text="Nome da fonte (Wikipedia, Wikidata, etc.)")
    source_url = models.URLField(help_text="URL da fonte da informação")
    source_timestamp = models.DateTimeField(auto_now_add=True, help_text="Quando a informação foi obtida")

    # Status da sugestão
    applied = models.BooleanField(default=False, help_text="Sugestão foi aplicada?")
    applied_at = models.DateTimeField(null=True, blank=True)
    rejected = models.BooleanField(default=False, help_text="Sugestão foi rejeitada?")
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Data Audit Suggestion'
        verbose_name_plural = 'Data Audit Suggestions'
        indexes = [
            models.Index(fields=['report', 'table_name']),
            models.Index(fields=['applied', 'rejected']),
        ]

    def __str__(self):
        return f"{self.table_name}.{self.field_name} - {self.record_identifier}: {self.suggested_value}"


class HistoricalDataCollectionConfig(models.Model):
    """
    Configuração para controle de workers e coleta de dados históricos.
    Permite ajustar paralelismo e prioridades dinamicamente via Django Admin.
    """
    # Controle de workers e paralelismo
    max_workers = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Número máximo de workers Celery para coleta histórica (1-50)"
    )

    tasks_per_batch = models.IntegerField(
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Número de tarefas executadas em paralelo por lote (1-100)"
    )

    # Controle de execução
    enabled = models.BooleanField(
        default=True,
        help_text="Ativar/desativar coleta automática de dados históricos"
    )

    scan_interval_minutes = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Intervalo de varredura em minutos (1-60)"
    )

    # Prioridades de coleta (ordem decrescente de ano)
    start_year = models.IntegerField(
        default=2024,
        validators=[MinValueValidator(1950), MaxValueValidator(2050)],
        help_text="Ano inicial para coleta (mais recente para mais antigo)"
    )

    end_year = models.IntegerField(
        default=1950,
        validators=[MinValueValidator(1950), MaxValueValidator(2050)],
        help_text="Ano final para coleta (não incluso)"
    )

    # Tipos de dados a coletar
    collect_races = models.BooleanField(default=True, help_text="Coletar resultados de corridas")
    collect_qualifying = models.BooleanField(default=True, help_text="Coletar resultados de qualificação")
    collect_sprints = models.BooleanField(default=True, help_text="Coletar resultados de sprints")
    collect_standings = models.BooleanField(default=True, help_text="Coletar classificações")
    collect_drivers = models.BooleanField(default=True, help_text="Coletar dados de pilotos")
    collect_teams = models.BooleanField(default=True, help_text="Coletar dados de equipes")
    collect_circuits = models.BooleanField(default=True, help_text="Coletar dados de circuitos")

    # Controle de fonte de dados
    use_wikipedia = models.BooleanField(
        default=True,
        help_text="Usar Wikipedia como fonte para dados históricos (pré-2018)"
    )

    use_ergast_api = models.BooleanField(
        default=True,
        help_text="Usar Ergast API como fonte para dados históricos"
    )

    # Estatísticas
    last_scan_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última execução da varredura"
    )

    last_year_processed = models.IntegerField(
        null=True,
        blank=True,
        help_text="Último ano processado com sucesso"
    )

    total_records_collected = models.IntegerField(
        default=0,
        help_text="Total de registros coletados desde o início"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Historical Data Collection Config'
        verbose_name_plural = 'Historical Data Collection Configs'

    def __str__(self):
        status = "Ativo" if self.enabled else "Inativo"
        return f"Config de Coleta Histórica ({status}) - {self.max_workers} workers"

    def save(self, *args, **kwargs):
        """Garantir que existe apenas uma configuração."""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        """Obter ou criar a configuração singleton."""
        config, created = cls.objects.get_or_create(pk=1)
        return config


class HistoricalDataGap(models.Model):
    """
    Registra gaps/lacunas de dados históricos identificados pela varredura.
    Usado para priorizar coleta de dados faltantes.
    """
    GAP_TYPE_CHOICES = [
        ('season', 'Temporada Completa'),
        ('event', 'Evento/GP'),
        ('session', 'Sessão'),
        ('result', 'Resultado'),
        ('standing', 'Classificação'),
        ('driver', 'Piloto'),
        ('team', 'Equipe'),
        ('circuit', 'Circuito'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('collecting', 'Coletando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
        ('skipped', 'Ignorado'),
    ]

    gap_type = models.CharField(max_length=20, choices=GAP_TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)

    # Identificação do gap
    year = models.IntegerField(validators=[MinValueValidator(1950)])
    round_number = models.IntegerField(null=True, blank=True)
    session_type = models.CharField(max_length=10, blank=True)

    # Descrição
    description = models.TextField(help_text="Descrição do gap identificado")

    # Prioridade (maior = mais prioritário)
    priority = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        help_text="Prioridade de coleta (0-1000, maior = mais prioritário)"
    )

    # Tentativas de coleta
    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    last_attempt_at = models.DateTimeField(null=True, blank=True)

    # Resultado da coleta
    collected_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-year', 'round_number']
        verbose_name = 'Historical Data Gap'
        verbose_name_plural = 'Historical Data Gaps'
        indexes = [
            models.Index(fields=['status', '-priority']),
            models.Index(fields=['year', 'round_number']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        if self.round_number:
            return f"{self.gap_type} - {self.year} R{self.round_number} ({self.status})"
        return f"{self.gap_type} - {self.year} ({self.status})"
