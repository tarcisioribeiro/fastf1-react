# MAPEAMENTO DE LINHAS DE SUCESSÃO - F1 TEAMS
## Guia de Consolidação para Banco de Dados

**Data:** 10/11/2025
**Objetivo:** Mapear todas as operações (linhas de sucessão) identificadas para consolidação do banco de dados

---

## DEFINIÇÕES

### Termos Importantes:

- **OPERAÇÃO:** Uma licença/entidade legal que pode mudar de nome ao longo dos anos
- **IDENTIDADE:** Um nome específico usado pela operação em determinado período
- **LINHA DE SUCESSÃO:** Sequência cronológica de identidades de uma mesma operação
- **EQUIPE ÚNICA:** Operação que manteve o mesmo nome principal (pode ter variações de patrocinador)
- **VARIAÇÃO DE MOTOR:** Mesmo construtor com diferentes fornecedores de motor (ex: Brabham-Ford, Brabham-Repco)

---

## PARTE 1: EQUIPES ATUAIS (2025)

### OPERAÇÃO 1: FERRARI
**Tipo:** EQUIPE ÚNICA
**Anos:** 1950 - presente (75 anos)
**Status:** ATIVA

**Identidades:**
1. Scuderia Ferrari (1950-presente) - principal
2. Ferrari Marlboro (variações com Marlboro até 2011)
3. Scuderia Ferrari HP (2024-presente)

**Consolidação:** SEM NECESSIDADE (equipe única)

---

### OPERAÇÃO 2: MERCEDES (TYRRELL LINEAGE)
**Tipo:** LINHA DE SUCESSÃO
**Anos:** 1970 - presente (55 anos)
**Status:** ATIVA

**Identidades (em ordem cronológica):**
1. **Tyrrell Racing** (1970-1998)
2. **British American Racing (BAR)** (1999-2005)
3. **Honda Racing F1 Team** (2006-2008)
4. **Brawn GP** (2009)
5. **Mercedes GP / Mercedes-AMG Petronas F1** (2010-presente)

**Nome atual:** Mercedes
**Base:** Brackley (desde era BAR)

**Consolidação recomendada:**
- Predecessor de BAR: Tyrrell
- Predecessor de Honda: BAR
- Predecessor de Brawn: Honda
- Predecessor de Mercedes: Brawn
- Nome atual (todas): Mercedes

---

### OPERAÇÃO 3: RED BULL RACING (STEWART LINEAGE)
**Tipo:** LINHA DE SUCESSÃO
**Anos:** 1997 - presente (28 anos)
**Status:** ATIVA

**Identidades (em ordem cronológica):**
1. **Stewart Grand Prix** (1997-1999)
2. **Jaguar Racing** (2000-2004)
3. **Red Bull Racing** (2005-presente)

**Nome atual:** Red Bull Racing
**Base:** Milton Keynes

**Consolidação recomendada:**
- Predecessor de Jaguar: Stewart
- Predecessor de Red Bull: Jaguar
- Nome atual (todas): Red Bull Racing

---

### OPERAÇÃO 4: MCLAREN
**Tipo:** EQUIPE ÚNICA
**Anos:** 1966 - presente (59 anos)
**Status:** ATIVA

**Identidades:**
1. Bruce McLaren Motor Racing (1966-1972)
2. McLaren / Team McLaren (1972-presente)

**Consolidação:** SEM NECESSIDADE (apenas mudança de nome, mesma operação)

---

### OPERAÇÃO 5: ALPINE (TOLEMAN LINEAGE)
**Tipo:** LINHA DE SUCESSÃO (complexa)
**Anos:** 1981 - presente (44 anos)
**Status:** ATIVA

**Identidades (em ordem cronológica):**
1. **Toleman** (1981-1985)
2. **Benetton** (1986-2001)
3. **Renault (primeira era)** (2002-2011)
4. **Lotus F1 Team** (2012-2015) *NÃO é Team Lotus original*
5. **Renault (segunda era)** (2016-2020)
6. **Alpine F1 Team** (2021-presente)

**Nome atual:** Alpine F1 Team
**Base:** Enstone (desde Benetton 1986)
**Apelido:** "Team Enstone"

**Consolidação recomendada:**
- Predecessor de Benetton: Toleman
- Predecessor de Renault (1ª era): Benetton
- Predecessor de Lotus F1: Renault (1ª era)
- Predecessor de Renault (2ª era): Lotus F1
- Predecessor de Alpine: Renault (2ª era)
- Nome atual (todas): Alpine F1 Team

**IMPORTANTE:** Separar do Team Lotus original (1958-1994) e Lotus Racing/Caterham (2010-2014)

---

### OPERAÇÃO 6: ASTON MARTIN (JORDAN LINEAGE)
**Tipo:** LINHA DE SUCESSÃO (muito fragmentada)
**Anos:** 1991 - presente (34 anos)
**Status:** ATIVA

**Identidades (em ordem cronológica):**
1. **Jordan Grand Prix** (1991-2005)
2. **Midland F1 Racing** (2006)
3. **Spyker F1** (2007)
4. **Force India** (2008-2018)
5. **Racing Point** (2019-2020)
6. **Aston Martin F1 Team** (2021-presente)

**Nome atual:** Aston Martin
**Base:** Silverstone

**Consolidação recomendada:**
- Predecessor de Midland: Jordan
- Predecessor de Spyker: Midland
- Predecessor de Force India: Spyker
- Predecessor de Racing Point: Force India
- Predecessor de Aston Martin: Racing Point
- Nome atual (todas): Aston Martin

---

### OPERAÇÃO 7: WILLIAMS
**Tipo:** EQUIPE ÚNICA
**Anos:** 1977 - presente (48 anos)
**Status:** ATIVA

**Identidades:**
1. Williams Grand Prix Engineering (1977-2013)
2. BMW Williams F1 (2000-2005) - apenas nome de competição durante parceria BMW
3. Williams Racing (2014-2024)
4. Atlassian Williams Racing (2025-presente)

**Consolidação:** SEM NECESSIDADE (mesma operação, variações de patrocinador)

**IMPORTANTE:** Wolf-Williams (1976) é operação SEPARADA, NÃO é predecessor!

---

### OPERAÇÃO 8: RACING BULLS (MINARDI LINEAGE)
**Tipo:** LINHA DE SUCESSÃO
**Anos:** 1985 - presente (40 anos)
**Status:** ATIVA

**Identidades (em ordem cronológica):**
1. **Minardi** (1985-2005)
2. **Scuderia Toro Rosso** (2006-2019)
3. **Scuderia AlphaTauri** (2020-2023)
4. **Visa Cash App RB / VCARB** (2024)
5. **Racing Bulls** (2025-presente)

**Nome atual:** Racing Bulls
**Base:** Faenza, Itália

**Consolidação recomendada:**
- Predecessor de Toro Rosso: Minardi
- Predecessor de AlphaTauri: Toro Rosso
- Predecessor de RB: AlphaTauri
- Predecessor de Racing Bulls: RB
- Nome atual (todas): Racing Bulls

---

### OPERAÇÃO 9: KICK SAUBER (SAUBER LINEAGE)
**Tipo:** LINHA DE SUCESSÃO (com retornos)
**Anos:** 1993 - presente (32 anos)
**Status:** ATIVA

**Identidades (em ordem cronológica):**
1. **Sauber (primeira era)** (1993-2005)
2. **BMW Sauber F1 Team** (2006-2009)
3. **Sauber (segunda era)** (2010-2017)
4. **Alfa Romeo Sauber / Alfa Romeo Racing / Alfa Romeo F1 Team** (2018-2023)
5. **Stake F1 Team Kick Sauber** (2024-presente)

**Nome atual:** Stake F1 Team Kick Sauber (usado como "Kick Sauber")
**Base:** Hinwil, Suíça
**Futuro:** Audi (2026)

**Consolidação recomendada:**
- Predecessor de BMW Sauber: Sauber (1ª era)
- Predecessor de Sauber (2ª era): BMW Sauber
- Predecessor de Alfa Romeo: Sauber (2ª era)
- Predecessor de Kick Sauber: Alfa Romeo
- Nome atual (todas): Kick Sauber

**NOTA:** Sauber 1ª e 2ª era são mesma operação (Peter Sauber recomprou após BMW)

---

### OPERAÇÃO 10: HAAS F1 TEAM
**Tipo:** EQUIPE ÚNICA
**Anos:** 2016 - presente (9 anos)
**Status:** ATIVA

**Identidades:**
1. Haas F1 Team (2016-2022)
2. MoneyGram Haas F1 Team (2023-presente)

**Consolidação:** SEM NECESSIDADE (variação de patrocinador apenas)

---

## PARTE 2: LINHAS DE SUCESSÃO EXTINTAS

### OPERAÇÃO 11: MANOR (VIRGIN LINEAGE)
**Tipo:** LINHA DE SUCESSÃO
**Anos:** 2010-2017 (7 anos)
**Status:** EXTINTA (2017)

**Identidades (em ordem cronológica):**
1. **Manor Grand Prix / Virgin Racing** (2010)
2. **Marussia Virgin Racing** (2011)
3. **Marussia F1 Team** (2012-2014)
4. **Manor Marussia F1 Team** (2015)
5. **Manor Racing** (2016)

**Nome final:** Manor Racing
**Fechamento:** Março 2017

**Consolidação recomendada:**
- Todas fazem parte da mesma operação
- Nome final: Manor Racing
- Status: EXTINCT

---

### OPERAÇÃO 12: CATERHAM (LOTUS RACING LINEAGE)
**Tipo:** LINHA DE SUCESSÃO
**Anos:** 2010-2014 (5 anos)
**Status:** EXTINTA (2014)

**Identidades (em ordem cronológica):**
1. **Lotus Racing** (2010) - construtor: 1Malaysia Racing Team
2. **Team Lotus** (2011)
3. **Caterham F1 Team** (2012-2014)

**Nome final:** Caterham F1 Team
**Fechamento:** Final 2014 (administração)

**Consolidação recomendada:**
- Todas fazem parte da mesma operação (Tony Fernandes)
- Nome final: Caterham
- Status: EXTINCT

**IMPORTANTE:** NÃO confundir com Team Lotus original (1958-1994) ou Lotus F1 Team (2012-2015)

---

### OPERAÇÃO 13: MARCH (FRAGMENTADA)
**Tipo:** LINHA DE SUCESSÃO (3 eras)
**Anos:** 1970-1977, 1981-1982, 1987-1992
**Status:** EXTINTA (1992)

**Identidades (em ordem cronológica):**
1. **March Engineering (1ª era)** (1970-1977) → vendida para ATS
2. **March (2ª era)** (1981-1982)
3. **March (3ª era início)** (1987-1989)
4. **Leyton House Racing** (1990-1991)
5. **March (era final)** (1992)

**Nome final:** March
**Fechamento:** 1992

**Consolidação recomendada:**
- Operação complexa com interrupções
- Marcar eras distintas
- Status: EXTINCT

---

### OPERAÇÃO 14: LIGIER-PROST
**Tipo:** LINHA DE SUCESSÃO
**Anos:** 1976-2001 (26 anos)
**Status:** EXTINTA (2002)

**Identidades (em ordem cronológica):**
1. **Ligier / Équipe Ligier** (1976-1996)
2. **Prost Grand Prix** (1997-2001)

**Nome final:** Prost Grand Prix
**Fechamento:** Janeiro 2002 (liquidação compulsória)

**Consolidação recomendada:**
- Predecessor de Prost: Ligier
- Status: EXTINCT

---

### OPERAÇÃO 15: ARROWS (COM FOOTWORK)
**Tipo:** LINHA DE SUCESSÃO
**Anos:** 1978-2002 (25 anos)
**Status:** EXTINTA (2003)

**Identidades (em ordem cronológica):**
1. **Arrows Grand Prix International (1ª era)** (1978-1990)
2. **Footwork / Footwork Arrows** (1991-1995)
3. **Arrows (2ª era / era TWR)** (1996-2002)

**Nome final:** Arrows
**Fechamento:** Início 2003 (liquidação)

**Consolidação recomendada:**
- Mesma operação, 3 fases
- Status: EXTINCT
- Nota: 382 GPs, zero vitórias

---

### OPERAÇÃO 16: OSELLA-FONDMETAL
**Tipo:** LINHA DE SUCESSÃO
**Anos:** 1980-1992
**Status:** EXTINTA (1992)

**Identidades (em ordem cronológica):**
1. **Osella** (1980-1990)
2. **Fondmetal** (1991-1992)

**Nome final:** Fondmetal
**Fechamento:** 1992

**Consolidação recomendada:**
- Predecessor de Fondmetal: Osella
- Status: EXTINCT

---

### OPERAÇÃO 17: ENSIGN-THEODORE
**Tipo:** LINHA DE SUCESSÃO (fusão)
**Anos:** 1973-1982+ (Ensign)
**Status:** FUNDIDA (Theodore)

**Identidades:**
1. **Ensign Racing** (1973-1982)
2. **Fusão com Theodore** (1983)

**Nome final:** Theodore (absorveu Ensign)
**Fechamento:** Fundida em Theodore

**Consolidação recomendada:**
- Ensign fundida em Theodore (1983)
- Status: MERGED

---

### OPERAÇÃO 18: FITTIPALDI (VÁRIAS DENOMINAÇÕES)
**Tipo:** LINHA DE SUCESSÃO (variações)
**Anos:** 1975-1982 (8 anos)
**Status:** EXTINTA (1982)

**Identidades (em ordem cronológica):**
1. **Copersucar-Fittipaldi** (1975)
2. **Fittipaldi Automotive** (1976-1979)
3. **Skol Team Fittipaldi** (1980)
4. **Fittipaldi Automotive** (1981-1982)

**Nome final:** Fittipaldi Automotive
**Fechamento:** 1982

**Consolidação recomendada:**
- Todas são mesma operação, variações de patrocinador
- Status: EXTINCT

---

### OPERAÇÃO 19: WOLF (FRAGMENTADA)
**Tipo:** LINHA DE SUCESSÃO (parcial)
**Anos:** 1976-1979
**Status:** EXTINTA (fundida)

**Identidades (em ordem cronológica):**
1. **Wolf-Williams** (1976)
2. **Walter Wolf Racing** (1977-1979) → fundida em Fittipaldi

**Nome final:** Walter Wolf Racing
**Fechamento:** Fundida em Fittipaldi Automotive (1979)

**Consolidação recomendada:**
- Status: MERGED (em Fittipaldi)

**IMPORTANTE:** Wolf-Williams (1976) NÃO é predecessor de Williams GP Engineering (1977)

---

## PARTE 3: EQUIPES ÚNICAS EXTINTAS (SEM SUCESSÃO)

### Grandes Equipes Históricas:

| Equipe | Anos | Títulos | Status |
|--------|------|---------|--------|
| Team Lotus (original) | 1958-1994 | 7 Const, 6 Pilots | EXTINCT - Sem sucessor |
| Brabham | 1960-1992 | 2 Const, 4 Pilots | EXTINCT - Sem sucessor |
| Vanwall | 1954-1960 | 1 Const | EXTINCT - Sem sucessor |
| Cooper | 1950-1969 | 2 Const, 2 Pilots | EXTINCT - Sem sucessor |
| BRM | 1951-1977 | 1 Const, 1 Pilot | EXTINCT - Sem sucessor |
| Matra | 1968-1972 | 1 Const, 1 Pilot | EXTINCT - Sem sucessor |
| Shadow | 1973-1980 | 0 Const | EXTINCT - Sem sucessor |
| Toyota | 2002-2009 | 0 Const | EXTINCT - Sem sucessor |
| HRT | 2010-2012 | 0 Const | EXTINCT - Sem sucessor |
| Super Aguri | 2006-2008 | 0 Const | EXTINCT - Sem sucessor |

**Consolidação:** Marcar como equipes únicas sem predecessores/sucessores

---

## PARTE 4: VARIAÇÕES DE MOTOR (MESMO CONSTRUTOR)

### Principais casos identificados no banco (171 equipes):

#### BRABHAM (6 variações):
- Brabham (base)
- Brabham-Alfa Romeo
- Brabham-BRM
- Brabham-Climax
- Brabham-Ford
- Brabham-Repco

**Consolidação:** Todas são **MESMA OPERAÇÃO** (Brabham)

#### COOPER (11 variações):
- Cooper (base)
- Cooper-Alfa Romeo
- Cooper-ATS
- Cooper-Borgward
- Cooper-BRM
- Cooper-Castellotti
- Cooper-Climax
- Cooper-Ferrari
- Cooper-Ford
- Cooper-Maserati
- Cooper-OSCA

**Consolidação:** Todas são **MESMA OPERAÇÃO** (Cooper)

#### LOTUS (3 variações):
- Lotus (base)
- Lotus-BRM
- Lotus-Climax

**Consolidação:** Todas são **MESMA OPERAÇÃO** (Team Lotus original)

#### EAGLE (2 variações):
- Eagle
- Eagle-Climax
- Eagle-Weslake

**Consolidação:** Mesma operação

#### OUTROS:
- BRM, BRM-Ford
- McLaren, McLaren-Ford
- De Tomaso (várias variações)
- Muitos outros...

**Recomendação:** Adicionar campo `is_engine_variant` e `base_team` no banco

---

## PARTE 5: CASOS ESPECIAIS E CONFUSÕES

### 1. TRÊS "LOTUS" DIFERENTES:

#### A) Team Lotus (ORIGINAL) - 1958-1994
- Colin Chapman
- 7 títulos de construtores
- **SEM SUCESSOR** (encerrou 1994)
- Variações: Lotus, Lotus-BRM, Lotus-Climax

#### B) Lotus Racing / Team Lotus / Caterham - 2010-2014
- Tony Fernandes
- Operação completamente separada
- Sucessão: Lotus Racing → Team Lotus → Caterham
- **EXTINTA 2014**

#### C) Lotus F1 Team - 2012-2015
- Renault/Genii Capital (operação Enstone)
- Parte da linha Alpine
- Sucessão: ... → Renault → **Lotus F1** → Renault → Alpine
- **ATIVA** (como Alpine)

**Consolidação:** São 3 operações COMPLETAMENTE DIFERENTES!

---

### 2. WILLIAMS: WOLF-WILLIAMS ≠ WILLIAMS GP

#### Wolf-Williams (1976):
- Walter Wolf comprou 60% de Frank Williams Racing Cars
- Frank Williams era gerente
- Final 1976: Frank foi removido
- Esta operação → Walter Wolf Racing → fundida em Fittipaldi

#### Williams Grand Prix Engineering (1977-presente):
- Frank Williams recomeçou do ZERO
- Operação nova, sem relação com Wolf-Williams
- Esta é a Williams atual

**Consolidação:** Wolf-Williams NÃO é predecessor de Williams atual!

---

### 3. ALFA ROMEO - MÚLTIPLAS ERAS:

#### Alfa Romeo (equipe própria antiga):
- Anos 1950
- Equipe de fábrica original
- **SEM RELAÇÃO** com eras modernas

#### Alfa Romeo Racing (2018-2023):
- Patrocínio título na operação Sauber
- Parte da linha Kick Sauber
- Não é equipe própria, é Sauber com nome Alfa Romeo

**Consolidação:** Separar eras antigas de era moderna (Sauber)

---

### 4. RENAULT - DUAS ERAS NA MESMA OPERAÇÃO:

#### Renault (primeira era) - 2002-2011
- Parte da linha Toleman → Benetton → **Renault**
- Depois virou Lotus F1 Team

#### Renault (segunda era) - 2016-2020
- Mesma operação, mas recomprou de Genii
- **Lotus F1** → **Renault** → Alpine

**Consolidação:** Mesma linha de sucessão, apenas retornou ao nome Renault

---

## PARTE 6: ESTRUTURA RECOMENDADA PARA BANCO DE DADOS

### Novos campos sugeridos:

```sql
ALTER TABLE teams ADD COLUMN operation_line_id INT;
ALTER TABLE teams ADD COLUMN operation_name VARCHAR(100);
ALTER TABLE teams ADD COLUMN is_engine_variant BOOLEAN DEFAULT FALSE;
ALTER TABLE teams ADD COLUMN base_team_name VARCHAR(100);
ALTER TABLE teams ADD COLUMN predecessor_id INT;
ALTER TABLE teams ADD COLUMN successor_id INT;
ALTER TABLE teams ADD COLUMN current_name VARCHAR(100);
ALTER TABLE teams ADD COLUMN final_name VARCHAR(100);
ALTER TABLE teams ADD COLUMN team_status ENUM('ACTIVE', 'EXTINCT', 'RENAMED', 'MERGED');
ALTER TABLE teams ADD COLUMN years_active VARCHAR(50);
```

### Exemplo de registro:

```json
{
  "id": 1,
  "name": "Tyrrell",
  "operation_line_id": 2,
  "operation_name": "Mercedes (Tyrrell lineage)",
  "is_engine_variant": false,
  "base_team_name": null,
  "predecessor_id": null,
  "successor_id": 2,  // BAR
  "current_name": "Mercedes",
  "final_name": "BAR",
  "team_status": "RENAMED",
  "years_active": "1970-1998"
}
```

```json
{
  "id": 50,
  "name": "Brabham-Ford",
  "operation_line_id": 25,
  "operation_name": "Brabham",
  "is_engine_variant": true,
  "base_team_name": "Brabham",
  "predecessor_id": null,
  "successor_id": null,
  "current_name": null,
  "final_name": null,
  "team_status": "EXTINCT",
  "years_active": "1960s"
}
```

---

## PARTE 7: TABELA DE REFERÊNCIA RÁPIDA

### RESUMO DAS OPERAÇÕES:

| ID | Operação | Identidades | Anos | Status |
|----|----------|-------------|------|--------|
| 1 | Ferrari | 1 | 1950-presente | ACTIVE |
| 2 | Mercedes (Tyrrell) | 5 | 1970-presente | ACTIVE |
| 3 | Red Bull (Stewart) | 3 | 1997-presente | ACTIVE |
| 4 | McLaren | 1 | 1966-presente | ACTIVE |
| 5 | Alpine (Toleman) | 6 | 1981-presente | ACTIVE |
| 6 | Aston Martin (Jordan) | 6 | 1991-presente | ACTIVE |
| 7 | Williams | 1 | 1977-presente | ACTIVE |
| 8 | Racing Bulls (Minardi) | 5 | 1985-presente | ACTIVE |
| 9 | Kick Sauber (Sauber) | 5 | 1993-presente | ACTIVE |
| 10 | Haas | 1 | 2016-presente | ACTIVE |
| 11 | Manor (Virgin) | 5 | 2010-2017 | EXTINCT |
| 12 | Caterham (Lotus Racing) | 3 | 2010-2014 | EXTINCT |
| 13 | March | 5 | 1970-1992 | EXTINCT |
| 14 | Ligier-Prost | 2 | 1976-2001 | EXTINCT |
| 15 | Arrows | 3 | 1978-2002 | EXTINCT |
| 16 | Osella-Fondmetal | 2 | 1980-1992 | EXTINCT |
| 17 | Ensign | 1 | 1973-1982 | MERGED |
| 18 | Fittipaldi | 4 | 1975-1982 | EXTINCT |
| 19 | Wolf | 2 | 1976-1979 | MERGED |
| 20+ | Várias equipes únicas | 1 cada | Variados | EXTINCT |

**Total de operações principais identificadas:** ~30-40
**Total de identidades (incluindo variações de motor):** 171

---

## CONCLUSÃO

Este mapeamento identifica:
- ✅ 10 operações ativas (equipes atuais 2025)
- ✅ ~10 linhas de sucessão extintas
- ✅ ~60-70 equipes únicas extintas
- ✅ ~50-60 variações de motor (mesmo construtor)
- ✅ Total: 171 entradas no banco de dados

**Próximo passo:** Implementar estrutura de banco de dados com campos de sucessão e consolidar estatísticas por operação.

---

**FIM DO DOCUMENTO**
