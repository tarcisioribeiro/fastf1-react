# PLANO DE CONSOLIDAÇÃO DE EQUIPES - BANCO DE DADOS F1

**Data:** 10/11/2025
**Total de Equipes no Banco:** 171
**Total de Operações Identificadas:** 146
**Equipes Atuais (2025):** 10

---

## 📋 RESUMO EXECUTIVO

O banco de dados atualmente possui **171 registros de equipes**, mas muitos deles representam a mesma operação com nomes diferentes ao longo do tempo. Este documento mapeia todas as operações e define qual é o **nome mais recente** que deve aparecer nos filtros da interface.

### PROBLEMA IDENTIFICADO
- Múltiplas entradas para a mesma equipe histórica (ex: Alpine tem 6 variações)
- Dificulta agregações e análises históricas
- Filtros mostram nomes duplicados/obsoletos
- Usuários não conseguem ver dados consolidados de uma operação ao longo do tempo

### SOLUÇÃO PROPOSTA
- **Consolidar operações** mantendo o histórico
- **Mostrar apenas o nome mais recente** nos filtros da UI
- **Preservar dados históricos** para análises detalhadas
- **Adicionar campos no modelo Team** para suportar consolidação

---

## ✅ 10 EQUIPES ATUAIS (2025) - NOMES MAIS RECENTES

### 1. **FERRARI** 🔴
- **Nome para Filtros:** Ferrari (ou Scuderia Ferrari)
- **Status:** ATIVA desde 1950
- **Variações no Banco:** 1
  - Ferrari (id: 1)
- **Nota:** Única equipe presente em todas as temporadas desde 1950
- **Consolidação:** Não necessária (sempre foi Ferrari)

---

### 2. **MERCEDES** 🩵
- **Nome para Filtros:** Mercedes
- **Status:** ATIVA (2010-presente)
- **Variações no Banco:** 5
  - Mercedes (id: 2) ✅ NOME ATUAL
  - Tyrrell (id: 127) [1970-1998]
  - BAR (id: 49) [1999-2005]
  - Honda (id: 113) [2006-2008]
  - Brawn (id: 62) [2009]
- **Linha de Sucessão:** Tyrrell → BAR → Honda → Brawn GP → Mercedes
- **Consolidação:** Consolidar 5 registros sob "Mercedes"

---

### 3. **RED BULL RACING** 🔵
- **Nome para Filtros:** Red Bull Racing
- **Status:** ATIVA (2005-presente)
- **Variações no Banco:** 4
  - Red Bull Racing (id: 3) ✅ NOME ATUAL
  - Red Bull (id: 139)
  - Stewart (id: 136) [1997-1999]
  - Jaguar (id: 117) [2000-2004]
- **Linha de Sucessão:** Stewart → Jaguar → Red Bull Racing
- **Consolidação:** Consolidar 4 registros sob "Red Bull Racing"

---

### 4. **McLAREN** 🧡
- **Nome para Filtros:** McLaren
- **Status:** ATIVA desde 1966
- **Variações no Banco:** 1
  - McLaren (id: 9)
- **Nota:** Segunda equipe mais antiga no grid atual
- **Consolidação:** Não necessária (sempre foi McLaren)
- **Observação:** McLaren-Ford (id: 146) é variante de motor, não mudança de nome

---

### 5. **ALPINE** 💙
- **Nome para Filtros:** Alpine F1 Team (ou Alpine)
- **Status:** ATIVA (2021-presente)
- **Variações no Banco:** 6
  - Alpine F1 Team (id: 15) ✅ NOME ATUAL
  - Renault (id: 4) [2002-2011, 2016-2020]
  - Lotus F1 (id: 159) [2012-2015]
  - Lotus (id: 142)
  - Benetton (id: 52) [1986-2001]
  - Toleman (id: 133) [1981-1985]
- **Linha de Sucessão:** Toleman → Benetton → Renault → Lotus F1 Team → Renault → Alpine
- **Consolidação:** Consolidar 6 registros sob "Alpine F1 Team"
- **Nota:** Esta é a linha de sucessão MAIS COMPLEXA (6 identidades)

---

### 6. **ASTON MARTIN** 💚
- **Nome para Filtros:** Aston Martin
- **Status:** ATIVA (2021-presente)
- **Variações no Banco:** 4
  - Aston Martin (id: 12) ✅ NOME ATUAL
  - Racing Point (id: 11) [2019-2020]
  - Force India (id: 5) [2008-2018]
  - Jordan (id: 119) [1991-2005]
- **Linha de Sucessão:** Jordan → Midland → Spyker → Force India → Racing Point → Aston Martin
- **Consolidação:** Consolidar 4 registros sob "Aston Martin"
- **Nota:** Faltam Midland e Spyker no banco (adicionar se houver dados históricos)

---

### 7. **WILLIAMS** 🔵
- **Nome para Filtros:** Williams
- **Status:** ATIVA desde 1977
- **Variações no Banco:** 1
  - Williams (id: 10)
- **Nota:** 9 títulos de construtores, 7 de pilotos
- **Consolidação:** Não necessária (sempre foi Williams)
- **Observação:** Wolf (id: 151) é equipe SEPARADA, NÃO é predecessora

---

### 8. **HAAS** ⚪
- **Nome para Filtros:** Haas F1 Team (ou Haas)
- **Status:** ATIVA desde 2016
- **Variações no Banco:** 2
  - Haas F1 Team (id: 109) ✅ NOME PREFERENCIAL
  - Haas F1 Team (id: 6) (duplicata)
- **Consolidação:** REMOVER duplicata (id: 6) ou marcar como mesmo registro
- **Nota:** Primeira equipe americana desde 1986

---

### 9. **KICK SAUBER** 💚
- **Nome para Filtros:** Kick Sauber (futuramente Audi em 2026)
- **Status:** ATIVA (2024-presente)
- **Variações no Banco:** 6
  - Kick Sauber (id: 13) ✅ NOME ATUAL
  - Alfa Romeo Racing (id: 16) [2019-2023]
  - Alfa Romeo (id: 19) [2018-2023]
  - Alfa Romeo (id: 20) (duplicata)
  - Sauber (id: 8) [1993-2005, 2010-2017]
  - BMW Sauber (id: 54) [2006-2009]
- **Linha de Sucessão:** Sauber → BMW Sauber → Sauber → Alfa Romeo → Kick Sauber → Audi (2026)
- **Consolidação:** Consolidar 6 registros sob "Kick Sauber" (ou "Audi" a partir de 2026)
- **Nota:** Existem duplicatas de Alfa Romeo (ids 19 e 20)

---

### 10. **RACING BULLS** 💙
- **Nome para Filtros:** Racing Bulls
- **Status:** ATIVA (2025-presente)
- **Variações no Banco:** 5
  - Racing Bulls (id: 18) ✅ NOME ATUAL
  - RB (id: 14) [2024]
  - AlphaTauri (id: 17) [2020-2023]
  - Toro Rosso (id: 7) [2006-2019]
  - Minardi (id: 131) [1985-2005]
- **Linha de Sucessão:** Minardi → Toro Rosso → AlphaTauri → RB → Racing Bulls
- **Consolidação:** Consolidar 5 registros sob "Racing Bulls"
- **Nota:** Equipe júnior da Red Bull desde 2006

---

## 📊 ESTATÍSTICAS DAS 10 EQUIPES ATUAIS

| Equipe | Variações | Anos de História | Identidades | Complexidade |
|--------|-----------|------------------|-------------|--------------|
| Ferrari | 1 | 75 anos (1950-) | 1 | ⭐ Simples |
| Mercedes | 5 | 55 anos (1970-) | 5 | ⭐⭐⭐⭐ Alta |
| Red Bull Racing | 4 | 28 anos (1997-) | 3 | ⭐⭐⭐ Média |
| McLaren | 1 | 59 anos (1966-) | 1 | ⭐ Simples |
| Alpine | 6 | 44 anos (1981-) | 6 | ⭐⭐⭐⭐⭐ Muito Alta |
| Aston Martin | 4 | 34 anos (1991-) | 6 | ⭐⭐⭐⭐ Alta |
| Williams | 1 | 48 anos (1977-) | 1 | ⭐ Simples |
| Haas | 2 | 9 anos (2016-) | 1 | ⭐ Simples (duplicata) |
| Kick Sauber | 6 | 32 anos (1993-) | 5 | ⭐⭐⭐⭐ Alta |
| Racing Bulls | 5 | 40 anos (1985-) | 5 | ⭐⭐⭐⭐ Alta |

**TOTAL:** 34 variações para 10 equipes atuais

---

## 🔧 ESTRUTURA DE CONSOLIDAÇÃO RECOMENDADA

### Campos Adicionais no Modelo `Team`

```python
class Team(models.Model):
    # Campos existentes
    team_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200, blank=True)
    canonical_name = models.CharField(max_length=100, blank=True)  # JÁ EXISTE ✅
    color = models.CharField(max_length=7)
    color_secondary = models.CharField(max_length=7, blank=True)

    # NOVOS CAMPOS RECOMENDADOS
    operation_line_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID da linha de operação (ex: 1=Ferrari, 2=Mercedes, etc.)"
    )

    current_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nome mais recente da operação (para exibição nos filtros)"
    )

    display_in_filters = models.BooleanField(
        default=True,
        help_text="Se True, mostra nos filtros da UI. False para nomes históricos."
    )

    is_engine_variant = models.BooleanField(
        default=False,
        help_text="True se for apenas variação de motor (ex: Cooper-Climax)"
    )

    predecessor_id = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='successor',
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
        default='ACTIVE'
    )
```

---

## 📝 PLANO DE IMPLEMENTAÇÃO

### FASE 1: Preparação do Banco de Dados

#### 1.1 Criar Migration
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

#### 1.2 Script de Atualização dos Dados

```python
# backend/core/management/commands/consolidate_teams.py

from django.core.management.base import BaseCommand
from core.models import Team

class Command(BaseCommand):
    help = 'Consolida equipes e define nomes atuais'

    CONSOLIDATION_MAP = {
        # operation_line_id: (current_name, team_ids, display_ids)
        1: ('Ferrari', [1], [1]),  # Ferrari
        2: ('Mercedes', [2, 127, 49, 113, 62], [2]),  # Mercedes
        3: ('Red Bull Racing', [3, 139, 136, 117], [3]),  # Red Bull
        4: ('McLaren', [9], [9]),  # McLaren
        5: ('Alpine F1 Team', [15, 4, 159, 142, 52, 133], [15]),  # Alpine
        6: ('Aston Martin', [12, 11, 5, 119], [12]),  # Aston Martin
        7: ('Williams', [10], [10]),  # Williams
        8: ('Haas F1 Team', [109, 6], [109]),  # Haas (remover duplicata)
        9: ('Kick Sauber', [13, 16, 19, 20, 8, 54], [13]),  # Kick Sauber
        10: ('Racing Bulls', [18, 14, 17, 7, 131], [18]),  # Racing Bulls
    }

    def handle(self, *args, **options):
        for operation_id, (current_name, team_ids, display_ids) in self.CONSOLIDATION_MAP.items():
            self.stdout.write(f"\nConsolidando operação {operation_id}: {current_name}")

            for team_id in team_ids:
                try:
                    team = Team.objects.get(id=team_id)
                    team.operation_line_id = operation_id
                    team.current_name = current_name
                    team.display_in_filters = (team.id in display_ids)
                    team.save()

                    status = "✅ EXIBIR" if team.display_in_filters else "🔇 OCULTAR"
                    self.stdout.write(f"  {status} - {team.name} (id: {team.id})")

                except Team.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  ⚠️  Team id {team_id} não encontrada"))

        self.stdout.write(self.style.SUCCESS("\n✅ Consolidação concluída!"))
```

#### 1.3 Executar Script
```bash
python manage.py consolidate_teams
```

---

### FASE 2: Atualizar API Views

#### 2.1 Modificar Filtros para Mostrar Apenas Nomes Atuais

```python
# backend/api/views.py

class DriverStandingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DriverStanding.objects.all()
    serializer_class = DriverStandingSerializer

    @action(detail=False, methods=['get'])
    def latest(self, request):
        # ... código existente ...

        # FILTRAR POR EQUIPE (apenas nomes atuais)
        team_filter = request.query_params.get('team', None)
        if team_filter:
            # Buscar todas as variações da operação
            team_obj = Team.objects.filter(
                current_name=team_filter,
                display_in_filters=True
            ).first()

            if team_obj and team_obj.operation_line_id:
                # Filtrar por todas as equipes da mesma operação
                operation_teams = Team.objects.filter(
                    operation_line_id=team_obj.operation_line_id
                )
                standings = standings.filter(team__in=operation_teams)

        # ... resto do código ...
```

#### 2.2 Endpoint para Listar Equipes nos Filtros

```python
# backend/api/views.py

class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    @action(detail=False, methods=['get'])
    def for_filters(self, request):
        """
        Retorna apenas equipes que devem aparecer nos filtros
        (nomes mais recentes de cada operação)
        """
        teams = Team.objects.filter(display_in_filters=True).order_by('current_name')

        data = [
            {
                'id': team.id,
                'name': team.current_name or team.name,
                'color': team.color,
                'operation_line_id': team.operation_line_id,
            }
            for team in teams
        ]

        return Response(data)
```

---

### FASE 3: Atualizar Frontend

#### 3.1 Serviço de API
```typescript
// frontend/src/services/api.ts

export const getTeamsForFilters = async () => {
  const response = await api.get('/api/teams/for_filters/');
  return response.data;
};
```

#### 3.2 Componente de Filtro
```typescript
// frontend/src/components/TeamFilter.tsx

import { useState, useEffect } from 'react';
import { getTeamsForFilters } from '../services/api';

interface Team {
  id: number;
  name: string;
  color: string;
  operation_line_id: number;
}

export const TeamFilter = ({ onChange }: { onChange: (team: string) => void }) => {
  const [teams, setTeams] = useState<Team[]>([]);

  useEffect(() => {
    getTeamsForFilters().then(setTeams);
  }, []);

  return (
    <select onChange={(e) => onChange(e.target.value)}>
      <option value="">Todas as equipes</option>
      {teams.map((team) => (
        <option key={team.id} value={team.name}>
          {team.name}
        </option>
      ))}
    </select>
  );
};
```

---

## 🗂️ TRATAMENTO DE CASOS ESPECIAIS

### CASO 1: Haas - Duplicata
**Problema:** Dois registros com mesmo team_id
- Haas F1 Team (id: 109, team_id: haas)
- Haas F1 Team (id: 6, team_id: haas_f1_team)

**Solução:**
1. Verificar qual tem mais dados associados
2. Manter apenas um (provavelmente id: 6)
3. Migrar todos os relacionamentos para o registro mantido
4. Deletar o duplicado

```python
# Verificar qual tem mais dados
haas_109 = Team.objects.get(id=109)
haas_6 = Team.objects.get(id=6)

print(f"ID 109: {haas_109.race_results.count()} race results")
print(f"ID 6: {haas_6.race_results.count()} race results")

# Manter o que tem mais dados
# Migrar relacionamentos se necessário
# Deletar o duplicado
```

---

### CASO 2: Alfa Romeo - Duplicatas
**Problema:** Três registros de Alfa Romeo
- Alfa Romeo (id: 20, team_id: alfa) - canonical: "Kick Sauber"
- Alfa Romeo (id: 19, team_id: alfa_romeo) - canonical: "Kick Sauber"
- Alfa Romeo Racing (id: 16, team_id: alfa_romeo_racing) - canonical: "Kick Sauber"

**Solução:**
1. Verificar qual tem mais dados
2. Consolidar todos em um único registro
3. Atualizar canonical_name para "Kick Sauber"

---

### CASO 3: Equipes com Variações de Motor

Muitas equipes históricas têm variações de motor que NÃO devem ser consolidadas nos filtros modernos, mas devem ser marcadas como `is_engine_variant=True`:

**Exemplos:**
- Brabham: 6 variações (Brabham, Brabham-Alfa Romeo, Brabham-BRM, etc.)
- Cooper: 10 variações (Cooper, Cooper-Climax, Cooper-Ferrari, etc.)
- Lotus: Lotus-BRM, Lotus-Climax

**Ação:**
```python
# Marcar variações de motor
engine_variants = [
    'brabham-alfa_romeo', 'brabham-brm', 'brabham-climax',
    'brabham-ford', 'brabham-repco',
    'cooper-alfa_romeo', 'cooper-ats', 'cooper-borgward',
    'cooper-brm', 'cooper-castellotti', 'cooper-climax',
    'cooper-ferrari', 'cooper-ford', 'cooper-maserati', 'cooper-osca',
    'lotus-brm', 'lotus-climax',
    'eagle-climax', 'eagle-weslake',
    'brm-ford',
    'mclaren-ford',
]

Team.objects.filter(team_id__in=engine_variants).update(
    is_engine_variant=True,
    display_in_filters=False
)
```

---

## 📋 LISTA COMPLETA DE OPERAÇÕES (146)

### OPERAÇÕES ATIVAS (10)

| ID | Operação | Nome Atual | Variações | Anos |
|----|----------|------------|-----------|------|
| 1 | Ferrari | Ferrari | 1 | 1950- |
| 2 | Mercedes | Mercedes | 5 | 1970- |
| 3 | Red Bull Racing | Red Bull Racing | 4 | 1997- |
| 4 | McLaren | McLaren | 1 | 1966- |
| 5 | Alpine | Alpine F1 Team | 6 | 1981- |
| 6 | Aston Martin | Aston Martin | 4 | 1991- |
| 7 | Williams | Williams | 1 | 1977- |
| 8 | Haas | Haas F1 Team | 2 | 2016- |
| 9 | Kick Sauber | Kick Sauber | 6 | 1993- |
| 10 | Racing Bulls | Racing Bulls | 5 | 1985- |

### OPERAÇÕES EXTINTAS PRINCIPAIS (20+)

| ID | Operação | Nome Final | Status | Anos |
|----|----------|------------|--------|------|
| 20 | Team Lotus (original) | Team Lotus | EXTINTA 1994 | 1958-1994 |
| 21 | Brabham | Brabham | EXTINTA 1992 | 1960-1992 |
| 22 | Vanwall | Vanwall | EXTINTA 1960 | 1954-1960 |
| 23 | Cooper | Cooper | EXTINTA 1969 | 1950-1969 |
| 24 | BRM | BRM | EXTINTA 1977 | 1951-1977 |
| 25 | Matra | Matra | EXTINTA 1972 | 1968-1972 |
| 26 | Shadow | Shadow | EXTINTA 1980 | 1973-1980 |
| 27 | Toyota | Toyota | EXTINTA 2009 | 2002-2009 |
| 28 | HRT | HRT | EXTINTA 2012 | 2010-2012 |
| 29 | Super Aguri | Super Aguri | EXTINTA 2008 | 2006-2008 |
| 30 | Eagle | Eagle | EXTINTA 1969 | 1966-1969 |
| 31 | Theodore | Theodore | EXTINTA 1983 | 1978-1983 |

*(... mais 114 operações históricas menores)*

---

## 🎯 RECOMENDAÇÕES FINAIS

### 1. **Interface de Usuário (Filtros)**
- ✅ Mostrar APENAS as 10 equipes atuais com seus nomes mais recentes
- ✅ Adicionar opção "Incluir equipes históricas" (checkbox)
- ✅ Quando histórico ativado, mostrar TODAS as operações

### 2. **Análises e Relatórios**
- ✅ Sempre consolidar por `operation_line_id`
- ✅ Exibir nome atual mas permitir drill-down por período histórico
- ✅ Exemplo: "Mercedes (2010-presente) inclui dados de Tyrrell (1970-1998)"

### 3. **Performance**
- ✅ Criar índice em `operation_line_id`
- ✅ Criar índice em `display_in_filters`
- ✅ Cache dos filtros de equipes

```python
# backend/core/models.py
class Meta:
    indexes = [
        models.Index(fields=['operation_line_id']),
        models.Index(fields=['display_in_filters']),
        models.Index(fields=['current_name']),
    ]
```

### 4. **Validação de Dados**
- ✅ Garantir que cada operação tem EXATAMENTE 1 equipe com `display_in_filters=True`
- ✅ Todas as equipes de uma operação devem ter o mesmo `current_name`
- ✅ Testar queries de agregação por operação

### 5. **Documentação para Usuários**
- ✅ Explicar que "Mercedes" inclui dados históricos de Tyrrell, BAR, Honda, Brawn
- ✅ Tooltip nos filtros com linha de sucessão
- ✅ Link para documentação completa das linhas de sucessão

---

## 📊 CONSULTAS ÚTEIS

### Verificar Consolidação
```python
# Quantas equipes por operação?
from django.db.models import Count
Team.objects.values('operation_line_id', 'current_name').annotate(
    count=Count('id')
).order_by('operation_line_id')
```

### Listar Equipes para Filtros
```python
# Apenas nomes atuais
Team.objects.filter(display_in_filters=True).values('id', 'current_name', 'color')
```

### Buscar Dados Consolidados
```python
# Todas as corridas da operação Mercedes (incluindo Tyrrell, BAR, Honda, Brawn)
mercedes_operation_id = 2
teams_in_operation = Team.objects.filter(operation_line_id=mercedes_operation_id)
race_results = RaceResult.objects.filter(team__in=teams_in_operation)
```

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

- [ ] Criar migration com novos campos
- [ ] Executar migration
- [ ] Criar comando `consolidate_teams`
- [ ] Executar consolidação
- [ ] Verificar dados consolidados
- [ ] Atualizar API views (filtros)
- [ ] Criar endpoint `/api/teams/for_filters/`
- [ ] Atualizar frontend (componentes de filtro)
- [ ] Testar filtros na UI
- [ ] Verificar agregações e relatórios
- [ ] Adicionar índices de performance
- [ ] Atualizar testes unitários
- [ ] Documentar para usuários finais
- [ ] Deploy em produção

---

## 📚 REFERÊNCIAS

- **Documentação Completa:** `RELATORIO_COMPLETO_EQUIPES_F1.md`
- **Diagramas de Sucessão:** `DIAGRAMA_LINHAS_SUCESSAO.md`
- **Mapeamento Técnico:** `MAPEAMENTO_LINHAS_SUCESSAO.md`
- **Dados Estruturados:** `teams_consolidation.csv`
- **Índice:** `INDEX_DOCUMENTACAO_EQUIPES.md`

---

**FIM DO PLANO DE CONSOLIDAÇÃO**

*Documento criado em: 10/11/2025*
*Última atualização: 10/11/2025*
