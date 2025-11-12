# Guia de Uso: TeamFilterDropdown

## 📋 Visão Geral

O componente `TeamFilterDropdown` é um dropdown avançado para filtrar equipes de F1, com recursos de:
- **Tooltip interativo** mostrando linha de sucessão histórica
- **Dados consolidados** (10 equipes atuais)
- **Animações** e design responsivo
- **Opção de equipes históricas** (preparada para expansão futura)

---

## 🚀 Uso Básico

### Importação

```typescript
import TeamFilterDropdown from '../components/TeamFilterDropdown';
```

### Exemplo Simples

```typescript
import { useState } from 'react';
import TeamFilterDropdown from '../components/TeamFilterDropdown';

function MyPage() {
  const [selectedTeam, setSelectedTeam] = useState('');

  return (
    <TeamFilterDropdown
      value={selectedTeam}
      onChange={setSelectedTeam}
    />
  );
}
```

---

## ⚙️ Props

| Prop | Tipo | Padrão | Descrição |
|------|------|--------|-----------|
| `value` | `string` | - | **Obrigatório**. Valor selecionado |
| `onChange` | `(value: string) => void` | - | **Obrigatório**. Callback ao mudar |
| `label` | `string` | `'Equipe'` | Label do filtro |
| `icon` | `string` | `'🏎️'` | Ícone ao lado do label |
| `placeholder` | `string` | `'Selecione uma equipe'` | Texto quando vazio |
| `disabled` | `boolean` | `false` | Desabilita o dropdown |
| `showHistoricalToggle` | `boolean` | `false` | Mostra opção "Incluir históricas" |

---

## 📝 Exemplos de Uso

### 1. Uso em Página de Histórico (já integrado)

```typescript
// frontend/src/components/HistoryFilters.tsx

<TeamFilterDropdown
  label="4️⃣ Equipe"
  value={teamFilter}
  onChange={setTeamFilter}
  placeholder="Todas as equipes"
  icon="🏎️"
  disabled={loadingOptions}
  showHistoricalToggle={false}
/>
```

**Páginas que usam:**
- `/history/races` - Histórico de corridas
- `/history/qualifying` - Histórico de qualifyings
- `/history/sprints` - Histórico de sprints

---

### 2. Uso Standalone (página customizada)

```typescript
import { useState, useEffect } from 'react';
import TeamFilterDropdown from '../components/TeamFilterDropdown';
import { f1Api } from '../services/api';

function TeamAnalysis() {
  const [selectedTeam, setSelectedTeam] = useState('');
  const [teamData, setTeamData] = useState(null);

  useEffect(() => {
    if (selectedTeam) {
      loadTeamData(selectedTeam);
    }
  }, [selectedTeam]);

  const loadTeamData = async (teamName: string) => {
    const data = await f1Api.getRaceHistory({ team: teamName });
    setTeamData(data);
  };

  return (
    <div>
      <h1>Análise de Equipes</h1>

      <TeamFilterDropdown
        label="Selecione uma Equipe"
        value={selectedTeam}
        onChange={setSelectedTeam}
        icon="🏆"
        placeholder="Escolha uma equipe para analisar"
        showHistoricalToggle={true}
      />

      {teamData && (
        <div>
          {/* Renderizar dados da equipe */}
        </div>
      )}
    </div>
  );
}
```

---

### 3. Com Estado de Loading

```typescript
function TeamComparison() {
  const [team1, setTeam1] = useState('');
  const [team2, setTeam2] = useState('');
  const [loading, setLoading] = useState(false);

  return (
    <div className="comparison-grid">
      <TeamFilterDropdown
        label="Equipe 1"
        value={team1}
        onChange={setTeam1}
        disabled={loading}
        icon="🏎️"
      />

      <TeamFilterDropdown
        label="Equipe 2"
        value={team2}
        onChange={setTeam2}
        disabled={loading}
        icon="🏎️"
      />
    </div>
  );
}
```

---

### 4. Com Validação

```typescript
function TeamForm() {
  const [selectedTeam, setSelectedTeam] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = () => {
    if (!selectedTeam) {
      setError('Por favor, selecione uma equipe');
      return;
    }
    // Processar...
  };

  return (
    <form>
      <TeamFilterDropdown
        value={selectedTeam}
        onChange={(value) => {
          setSelectedTeam(value);
          setError(''); // Limpar erro ao selecionar
        }}
        label="Equipe Favorita"
      />
      {error && <span className="error">{error}</span>}

      <button onClick={handleSubmit}>Enviar</button>
    </form>
  );
}
```

---

## 🎨 Tooltip - Linha de Sucessão

### Como Funciona

Ao passar o mouse sobre uma equipe no dropdown, o tooltip aparece automaticamente mostrando:

1. **Nome atual** (destacado)
2. **Linha de sucessão** completa em ordem cronológica
3. **Anos ativos** de cada identidade
4. **Setas animadas** (→) indicando sucessão
5. **Contador** de identidades históricas

### Exemplo Visual

```
┌─────────────────────────────────┐
│  Mercedes                       │
│  Linha de Sucessão              │
├─────────────────────────────────┤
│  Tyrrell       1970-1998        │
│         ↓                        │
│  BAR           1999-2005        │
│         ↓                        │
│  Honda         2006-2008        │
│         ↓                        │
│  Brawn         2009             │
│         ↓                        │
│  ✓ Mercedes    2010-present     │
├─────────────────────────────────┤
│  5 identidade(s) histórica(s)   │
└─────────────────────────────────┘
```

### Dados Retornados pela API

```typescript
{
  id: 2,
  current_name: "Mercedes",
  color: "#00D2BE",
  operation_line_id: 2,
  succession_line: [
    {
      name: "Tyrrell",
      years_active: "1970-1998",
      is_current: false,
      status: "RENAMED"
    },
    // ... mais 4 entradas
  ]
}
```

---

## 🔧 Integração com Backend

### Endpoint Usado

```
GET /api/teams/for_filters/
```

### Resposta

```json
[
  {
    "id": 1,
    "current_name": "Ferrari",
    "color": "#DC0000",
    "operation_line_id": 1,
    "succession_line": [...]
  },
  // ... mais 9 equipes
]
```

### Filtragem com Operações Consolidadas

Quando você filtra por uma equipe, o backend automaticamente inclui todas as variações históricas:

```typescript
// Frontend envia:
fetch('/api/races/history/?team=Mercedes')

// Backend retorna dados de:
// - Mercedes (2010-presente)
// - Brawn (2009)
// - Honda (2006-2008)
// - BAR (1999-2005)
// - Tyrrell (1970-1998)
```

Isso é feito automaticamente pela função helper `get_teams_by_name_or_operation()` no backend.

---

## 🎯 Equipes Disponíveis (2025)

As 10 equipes atuais que aparecem no filtro:

| Equipe | Variações Históricas | Anos de História |
|--------|---------------------|------------------|
| Alpine F1 Team | 6 | 1981-presente (44 anos) |
| Aston Martin | 4 | 1991-presente (34 anos) |
| Ferrari | 1 | 1950-presente (75 anos) |
| Haas F1 Team | 2 | 2016-presente (9 anos) |
| Kick Sauber | 6 | 1993-presente (32 anos) |
| McLaren | 1 | 1966-presente (59 anos) |
| Mercedes | 5 | 1970-presente (55 anos) |
| Racing Bulls | 5 | 1985-presente (40 anos) |
| Red Bull Racing | 4 | 1997-presente (28 anos) |
| Williams | 1 | 1977-presente (48 anos) |

---

## 🎨 Customização de Estilos

### Variáveis CSS Disponíveis

O componente usa variáveis CSS do tema global. Para customizar:

```css
/* globals.css ou seu arquivo de tema */

:root {
  --primary-color: #3671C6;
  --primary-color-alpha: rgba(54, 113, 198, 0.1);
  --surface-color: #ffffff;
  --border-color: #e0e0e0;
  --text-primary: #1a1a1a;
  --text-secondary: #666666;
}

[data-theme='dark'] {
  --surface-color: #1e1e1e;
  --border-color: #333333;
  --text-primary: #f5f5f5;
  --text-secondary: #b0b0b0;
}
```

### Classes CSS Customizáveis

```css
/* Customizar o dropdown */
.team-filter-dropdown .filter-select {
  /* Seus estilos */
}

/* Customizar o tooltip */
.team-tooltip {
  /* Seus estilos */
}

/* Customizar linha de sucessão */
.succession-item {
  /* Seus estilos */
}

/* Customizar equipe atual */
.succession-item.current {
  /* Seus estilos */
}
```

---

## 📱 Responsividade

O componente é totalmente responsivo:

### Desktop (> 768px)
- Tooltip com largura máxima de 400px
- Font-size padrão
- Hover effects completos

### Mobile (≤ 768px)
- Tooltip com largura de 90% da viewport
- Font-size reduzido (0.875rem)
- Select nativo do mobile
- Touch-friendly

---

## ♿ Acessibilidade

### Recursos de Acessibilidade

- ✅ **Navegação por teclado** (Tab, Enter, Arrows)
- ✅ **ARIA labels** para screen readers
- ✅ **Alto contraste** entre texto e fundo
- ✅ **Focus visible** em todos os elementos interativos
- ✅ **Estados disabled** claramente indicados

### Exemplo de Uso Acessível

```typescript
<TeamFilterDropdown
  value={team}
  onChange={setTeam}
  label="Equipe"
  aria-label="Selecione uma equipe de Fórmula 1"
  aria-required="true"
/>
```

---

## 🐛 Troubleshooting

### Problema: Tooltip não aparece

**Possíveis causas:**
1. Equipe tem apenas 1 identidade (sem linha de sucessão)
2. CSS não foi importado
3. z-index conflitando com outros elementos

**Solução:**
```typescript
// Importar CSS no componente pai ou em _app.tsx
import '../components/TeamFilterDropdown.css';

// Verificar z-index
.team-tooltip {
  z-index: 9999 !important;
}
```

### Problema: Dados não carregam

**Possíveis causas:**
1. Backend não está rodando
2. Endpoint `/api/teams/for_filters/` não acessível
3. CORS bloqueando

**Solução:**
```bash
# Verificar se backend está rodando
docker ps | grep django

# Testar endpoint manualmente
curl http://localhost:8000/api/teams/for_filters/

# Ver logs
docker logs f1-django-api --tail 50
```

### Problema: Filtros não funcionam corretamente

**Causa:** Backend não está usando `get_teams_by_name_or_operation()`

**Solução:**
```python
# backend/api/views.py
# Certifique-se de que usa a função helper:

if team:
    teams_in_operation = get_teams_by_name_or_operation(team)
    results_query = results_query.filter(team__in=teams_in_operation)
```

---

## 📚 Referências

- **Documentação Completa:** `PLANO_CONSOLIDACAO_EQUIPES.md`
- **Histórico de Equipes:** `RELATORIO_COMPLETO_EQUIPES_F1.md`
- **Diagramas:** `DIAGRAMA_LINHAS_SUCESSAO.md`
- **Modelo de Dados:** `backend/core/models.py`
- **API Views:** `backend/api/views.py`

---

## 🎯 Próximas Melhorias Sugeridas

1. **Modo "Incluir Históricas"**
   - Implementar toggle para mostrar todas as 171 equipes
   - Filtrar por década/era

2. **Busca por Texto**
   - Adicionar campo de busca no dropdown
   - Suporte a autocomplete

3. **Multi-seleção**
   - Permitir selecionar múltiplas equipes
   - Comparação lado a lado

4. **Favoritos**
   - Salvar equipes favoritas no localStorage
   - Quick access aos favoritos

5. **Estatísticas no Tooltip**
   - Mostrar títulos conquistados por cada identidade
   - Vitórias, poles, pódios

---

**Documento criado em:** 10/11/2025
**Última atualização:** 10/11/2025
**Versão:** 1.0
