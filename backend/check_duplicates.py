#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Driver, Circuit
from django.db.models import Count

# Check for duplicate drivers
print("Verificando drivers duplicados...")
driver_duplicates = Driver.objects.values('code').annotate(count=Count('code')).filter(count__gt=1)
print(f"Total de códigos de drivers duplicados: {driver_duplicates.count()}")
for d in driver_duplicates[:20]:
    print(f"  Código: {d['code']}, Count: {d['count']}")

print("\nVerificando circuitos duplicados...")
circuit_duplicates = Circuit.objects.values('name').annotate(count=Count('name')).filter(count__gt=1)
print(f"Total de nomes de circuitos duplicados: {circuit_duplicates.count()}")
for c in circuit_duplicates[:20]:
    print(f"  Nome: {c['name']}, Count: {c['count']}")
