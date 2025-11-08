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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Mapeamento de consolidação de equipes
    TEAM_CONSOLIDATION_MAP = {
        "Red Bull Racing": ["Red Bull"],
        "Kick Sauber": ["Alfa Romeo", "Alfa Romeo Racing", "Sauber"],
        "Alpine": ["Alpine F1 Team", "Renault"],
        "Aston Martin": ["Force India", "Racing Point"],
        "Racing Bulls": ["RB", "AlphaTauri", "RB F1 Team", "Toro Rosso"],
    }

    class Meta:
        ordering = ['name']
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'

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


class Driver(models.Model):
    """F1 Driver model."""
    driver_id = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=3, help_text="3-letter driver code (e.g., VER, HAM)")
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
