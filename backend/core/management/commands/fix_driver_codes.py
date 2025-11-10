"""
Django management command to fix duplicate driver codes.
Generates unique 3-letter codes for drivers who share codes.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from core.models import Driver
import re


class Command(BaseCommand):
    help = 'Fix duplicate driver codes by generating unique 3-letter codes'

    # Mapeamento de driver_ids oficiais que devem manter seus códigos
    # (pilotos atuais e recentes da era FastF1)
    OFFICIAL_CODES = {
        'ver': 'VER',  # Max Verstappen
        'max_verstappen': None,  # Duplicata, será deletado na consolidação
        'ham': 'HAM',  # Lewis Hamilton
        'hamilton': None,
        'per': 'PER',  # Sergio Perez
        'perez': None,
        'bot': 'BOT',  # Valtteri Bottas
        'bottas': None,
        'vet': 'VET',  # Sebastian Vettel
        'vettel': None,
        'rai': 'RAI',  # Kimi Raikkonen
        'raikkonen': None,
        'ric': 'RIC',  # Daniel Ricciardo
        'ricciardo': None,
        'hul': 'HUL',  # Nico Hulkenberg
        'hulkenberg': None,
        'oco': 'OCO',  # Esteban Ocon
        'ocon': None,
        'sai': 'SAI',  # Carlos Sainz
        'sainz': None,
        'lec': 'LEC',  # Charles Leclerc
        'alo': 'ALO',  # Fernando Alonso
        'alonso': None,
        'eri': 'ERI',  # Marcus Ericsson
        'ericsson': None,
        'pia': 'PIA',  # Oscar Piastri
        'gio': 'GIO',  # Antonio Giovinazzi
        'giovinazzi': None,
        'kvy': 'KVY',  # Daniil Kvyat
        'kvyat': None,
        'kub': 'KUB',  # Robert Kubica
        'kubica': None,
        'ant': 'ANT',  # Kimi Antonelli
        'antonelli': None,
        'law': 'LAW',  # Liam Lawson
        'col': 'COL',  # Franco Colapinto
        'ait': 'AIT',  # Jack Aitken
        'aitken': None,
        'msc': 'MSC',  # Mick Schumacher
        'bea': 'BEA',  # Oliver Bearman
        'bearman': None,
        'rus': 'RUS',  # George Russell
        'alb': 'ALB',  # Alex Albon
        'albon': None,
        'bor': 'BOR',  # Gabriel Bortoleto
        'bortoleto': None,
        'fit': 'FIT',  # Pietro Fittipaldi
        'har': 'HAR',  # Brendon Hartley
        'van': 'VAN',  # Stoffel Vandoorne
        'vandoorne': None,
        'str': 'STR',  # Lance Stroll
        'stroll': None,
        'gro': 'GRO',  # Romain Grosjean
        'grosjean': None,
        'mag': 'MAG',  # Kevin Magnussen (atual)
    }

    # Códigos customizados para pilotos famosos/históricos
    CUSTOM_CODES = {
        'barrichello': 'RBA',  # Rubens Barrichello
        'berger': 'GBE',  # Gerhard Berger
        'ralf_schumacher': 'RSC',  # Ralf Schumacher
        'michael_schumacher': 'MSC',  # Michael Schumacher
        'keke_rosberg': 'KRO',  # Keke Rosberg
        'rosberg': 'NRO',  # Nico Rosberg
        'mario_andretti': 'MAN',  # Mario Andretti
        'senna': 'SEN',  # Ayrton Senna
        'piquet': 'PIQ',  # Nelson Piquet
        'mansell': 'NMA',  # Nigel Mansell
        'hill': 'GHI',  # Graham Hill
        'damon_hill': 'DHI',  # Damon Hill
        'clark': 'JCL',  # Jim Clark
        'stewart': 'JST',  # Jackie Stewart
        'villeneuve': 'JVI',  # Jacques Villeneuve
        'gilles_villeneuve': 'GVI',  # Gilles Villeneuve
        'fittipaldi': None,  # Vai usar FIT padrão
        'emerson_fittipaldi': 'EFI',  # Emerson Fittipaldi
        'jack_brabham': 'JBR',  # Jack Brabham
        'hulme': 'DHU',  # Denny Hulme
        'verstappen': 'JVE',  # Jos Verstappen
        'montoya': 'JPM',  # Juan Pablo Montoya
        'webber': 'WEB',  # Mark Webber
        'massa': 'MAS',  # Felipe Massa
        'frentzen': 'HHF',  # Heinz-Harald Frentzen
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually changing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - no data will be changed\n'))

        # Find duplicate codes
        duplicates = (
            Driver.objects.values('code')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
            .order_by('-count')
        )

        if not duplicates.exists():
            self.stdout.write(self.style.SUCCESS('No duplicate driver codes found!'))
            return

        self.stdout.write(f'Found {duplicates.count()} codes with duplicates\n')

        used_codes = set(Driver.objects.values_list('code', flat=True))
        total_fixed = 0

        for dup in duplicates:
            code = dup['code']
            count = dup['count']

            drivers = Driver.objects.filter(code=code).order_by('id')

            self.stdout.write(f'\n{self.style.WARNING(f"Code: {code} ({count} drivers)")}')

            # Identify which driver should keep the original code
            keeper = None
            for driver in drivers:
                if driver.driver_id in self.OFFICIAL_CODES:
                    official_code = self.OFFICIAL_CODES[driver.driver_id]
                    if official_code == code:
                        keeper = driver
                        self.stdout.write(f'  ✓ Keeping: {driver.full_name} (driver_id={driver.driver_id})')
                        break

            # If no official keeper found, keep the most recent driver (highest ID)
            # as they're more likely to be the active/recent driver
            if not keeper:
                keeper = drivers.last()
                self.stdout.write(f'  ✓ Keeping: {keeper.full_name} (most recent, ID={keeper.id})')

            # Generate new codes for the rest
            # We'll track codes we're about to assign in this batch to avoid conflicts
            batch_codes = set()

            for driver in drivers:
                if driver.id == keeper.id:
                    continue

                # Check if there's a custom code for this driver
                if driver.driver_id in self.CUSTOM_CODES and self.CUSTOM_CODES[driver.driver_id]:
                    new_code = self.CUSTOM_CODES[driver.driver_id]
                    # Verify it's not already used
                    if new_code in used_codes or new_code in batch_codes:
                        new_code = self._generate_unique_code(driver, used_codes | batch_codes)
                else:
                    # Generate a new code
                    new_code = self._generate_unique_code(driver, used_codes | batch_codes)

                if new_code:
                    self.stdout.write(
                        f'  → Changing: {driver.full_name} (ID={driver.id}) '
                        f'from "{code}" to "{new_code}"'
                    )

                    if not dry_run:
                        driver.code = new_code
                        driver.save()
                        used_codes.add(new_code)
                        total_fixed += 1
                    else:
                        # In dry-run, track what we would assign
                        batch_codes.add(new_code)
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Could not generate unique code for {driver.full_name}'
                        )
                    )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Fixed {total_fixed} duplicate driver codes')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\nThis was a DRY RUN - no actual data was changed')
            )

    def _generate_unique_code(self, driver, used_codes):
        """
        Generate a unique 3-letter code for a driver.

        Strategy:
        1. Try first letter of first name + first 2 letters of last name (e.g., RBA for Rubens Barrichello)
        2. Try first 3 letters of last name (e.g., BAR for Barrichello)
        3. Try first 2 letters of first + first letter of last (e.g., RUB for Rubens B)
        4. Try variations with middle name if available
        5. As last resort, add numbers (BAR1, BAR2, etc.)
        """
        first_name = self._clean_name(driver.first_name)
        last_name = self._clean_name(driver.last_name)

        # Split first name to handle middle names
        first_parts = first_name.split()
        last_parts = last_name.split()

        # Get main first and last name
        main_first = first_parts[0] if first_parts else first_name
        main_last = last_parts[-1] if last_parts else last_name

        candidates = []

        # Strategy 1: First letter of first name + first 2 of last name
        if len(main_first) >= 1 and len(main_last) >= 2:
            candidates.append((main_first[0] + main_last[:2]).upper())

        # Strategy 2: First 3 letters of last name
        if len(main_last) >= 3:
            candidates.append(main_last[:3].upper())

        # Strategy 3: First 2 of first + first of last
        if len(main_first) >= 2 and len(main_last) >= 1:
            candidates.append((main_first[:2] + main_last[0]).upper())

        # Strategy 4: All 3 from first name
        if len(main_first) >= 3:
            candidates.append(main_first[:3].upper())

        # Strategy 5: Use middle name if available
        if len(first_parts) > 1:
            middle = first_parts[1]
            if len(middle) >= 1 and len(main_last) >= 2:
                candidates.append((middle[0] + main_last[:2]).upper())

        # Strategy 6: Different combinations
        if len(main_first) >= 1 and len(main_last) >= 1:
            # First + last 2 of last name
            if len(main_last) >= 2:
                candidates.append((main_first[0] + main_last[-2:]).upper())

        # Try all candidates
        for code in candidates:
            if code not in used_codes and len(code) == 3:
                return code

        # Last resort: add numbers to the most logical code
        base_code = candidates[0] if candidates else main_last[:3].upper()
        base_code = base_code[:2]  # Make it 2 letters to add a number

        for i in range(1, 10):
            code = f"{base_code}{i}"
            if code not in used_codes:
                return code

        return None

    def _clean_name(self, name):
        """Remove accents and special characters from name."""
        if not name:
            return ''

        # Remove common accents
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n',
            'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
            'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
            'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
            'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
            'Ç': 'C', 'Ñ': 'N',
        }

        for old, new in replacements.items():
            name = name.replace(old, new)

        # Remove any remaining non-alphanumeric characters
        name = re.sub(r'[^a-zA-Z\s]', '', name)

        return name.strip()
