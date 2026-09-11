"""
Django management command para baixar os previews (SVGs de traçado) dos circuitos.

Passos executados:

1. Busca ``circuits.json`` do repositório f1-circuits-svg e resolve o
   ``layoutId`` mais recente de cada circuito do banco (a menos que
   ``--no-layout-sync`` seja informado).
2. Baixa os arquivos SVG para ``MEDIA_ROOT/circuits/<estilo>/<layout_id>.svg``.

O endpoint ``/api/circuits/track-svg/<layout_id>/<estilo>/`` serve a cópia local
quando ela existe e redireciona para o repositório remoto enquanto não existe.

Uso:
    python manage.py download_circuit_previews
    python manage.py download_circuit_previews --force
    python manage.py download_circuit_previews --circuit 12
    python manage.py download_circuit_previews --style black --style white
"""
import os
import re
import time
import unicodedata

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import Circuit

CIRCUITS_JSON_URL = (
    "https://raw.githubusercontent.com/julesr0y/f1-circuits-svg/main/circuits.json"
)


def _slug(value):
    """Normaliza um nome para comparação (sem acento, minúsculo, só a-z0-9)."""
    if not value:
        return ""
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '', value.lower())


class Command(BaseCommand):
    help = 'Baixa os previews (SVGs de traçado) dos circuitos para o armazenamento local'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Rebaixa os arquivos mesmo que já existam localmente',
        )
        parser.add_argument(
            '--circuit',
            type=int,
            dest='circuit_id',
            help='Baixa apenas o circuito com este ID',
        )
        parser.add_argument(
            '--style',
            action='append',
            dest='styles',
            choices=list(Circuit.SVG_STYLES),
            help='Estilo(s) a baixar (padrão: todos). Pode ser repetido.',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=15,
            help='Timeout (segundos) por requisição HTTP (padrão: 15)',
        )
        parser.add_argument(
            '--no-layout-sync',
            action='store_true',
            help='Não resolve/atualiza layout_id a partir do circuits.json',
        )

    def handle(self, *args, **options):
        force = options['force']
        styles = options['styles'] or list(Circuit.SVG_STYLES)
        timeout = options['timeout']
        session = requests.Session()

        if not options['no_layout_sync']:
            self._sync_layout_ids(session, timeout)

        circuits = Circuit.objects.exclude(layout_id='').exclude(layout_id__isnull=True)
        if options['circuit_id']:
            circuits = circuits.filter(id=options['circuit_id'])

        total = circuits.count()
        if not total:
            self.stdout.write(self.style.WARNING(
                'Nenhum circuito com layout_id encontrado. Rode a coleta de '
                'circuitos primeiro ou verifique o circuits.json.'
            ))
            return

        base_dir = os.path.join(settings.MEDIA_ROOT, 'circuits')
        self.stdout.write(
            f'Baixando previews de {total} circuito(s) | '
            f'variante: {Circuit.SVG_VARIANT} | estilos: {", ".join(styles)}'
        )

        downloaded = skipped = failed = 0

        for circuit in circuits.iterator():
            for style in styles:
                dest_dir = os.path.join(base_dir, style)
                os.makedirs(dest_dir, exist_ok=True)
                dest_path = os.path.join(dest_dir, f'{circuit.layout_id}.svg')

                if os.path.exists(dest_path) and not force:
                    skipped += 1
                    continue

                url = circuit.remote_svg_url(style)
                try:
                    resp = session.get(url, timeout=timeout)
                    resp.raise_for_status()
                    content = resp.content
                    if b'<svg' not in content[:512].lower():
                        raise ValueError('resposta não parece ser um SVG')
                    with open(dest_path, 'wb') as fh:
                        fh.write(content)
                    downloaded += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'  OK   {circuit.name} [{style}] -> {circuit.layout_id}.svg'
                    ))
                except Exception as exc:
                    failed += 1
                    self.stdout.write(self.style.ERROR(
                        f'  ERRO {circuit.name} [{style}] ({url}): {exc}'
                    ))
                time.sleep(0.1)  # evita martelar o raw.githubusercontent

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Concluído: {downloaded} baixado(s), {skipped} já existente(s), {failed} falha(s).'
        ))

    def _sync_layout_ids(self, session, timeout):
        """Resolve o layoutId mais recente de cada circuito via circuits.json."""
        try:
            resp = session.get(CIRCUITS_JSON_URL, timeout=timeout)
            resp.raise_for_status()
            repo_circuits = resp.json()
        except Exception as exc:
            self.stdout.write(self.style.WARNING(
                f'Não foi possível buscar circuits.json ({exc}). '
                f'Usando os layout_id já existentes.'
            ))
            return

        # Índices de busca do repositório
        by_id = {}
        by_name = {}
        for rc in repo_circuits:
            layouts = rc.get('layouts') or []
            if not layouts:
                continue
            latest = layouts[-1].get('layoutId')
            if not latest:
                continue
            by_id[_slug(rc.get('id'))] = latest
            by_name[_slug(rc.get('name'))] = latest

        # Mapeamento auxiliar Ergast -> base do layout (ex.: 'monza-6' -> 'monza')
        try:
            from data_collector.circuit_tasks import ERGAST_TO_LAYOUT_MAPPING
        except Exception:
            ERGAST_TO_LAYOUT_MAPPING = {}

        updated = unresolved = 0
        for circuit in Circuit.objects.all():
            candidates = [
                _slug(circuit.circuit_id),
                _slug(circuit.name),
                _slug(circuit.location),
            ]
            mapped = ERGAST_TO_LAYOUT_MAPPING.get(circuit.circuit_id)
            if mapped:
                candidates.append(_slug(re.sub(r'-\d+$', '', mapped)))

            layout_id = next(
                (by_id.get(c) or by_name.get(c) for c in candidates
                 if by_id.get(c) or by_name.get(c)),
                None,
            )

            if not layout_id:
                unresolved += 1
                continue

            if circuit.layout_id != layout_id or not circuit.svg_url:
                circuit.layout_id = layout_id
                circuit.svg_url = circuit.remote_svg_url('black')
                circuit.save(update_fields=['layout_id', 'svg_url', 'updated_at'])
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'layout_id resolvido: {updated} atualizado(s), {unresolved} sem correspondência.'
        ))
