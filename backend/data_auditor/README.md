# 🔍 Data Auditor MCP - Documentação Técnica

## 📋 Visão Geral

O **Data Auditor MCP (Model Context Protocol)** é um sistema automatizado de auditoria de banco de dados que:

1. ✅ Identifica campos vazios/nulos no banco de dados
2. 🔎 Busca dados em fontes públicas gratuitas (Wikipedia, Wikidata)
3. 💡 Sugere valores para preenchimento com score de confiança
4. 📊 Gera relatórios detalhados
5. ⏰ Executa automaticamente 1x por dia

**IMPORTANTE:** O sistema **NÃO altera dados automaticamente**. Ele apenas **sugere** valores que podem ser revisados e aplicados manualmente.

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    CELERY BEAT (Agendador)                      │
│                  Executa diariamente às 01:00                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DATABASE AUDITOR (auditor.py)                   │
│  • Escaneia tabelas configuradas (Driver, Circuit)              │
│  • Identifica campos vazios (NULL, '', 0)                       │
│  • Limita busca a 10 registros por campo (performance)          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│            DATA SOURCE AGGREGATOR (web_sources.py)               │
│  • Prioriza fontes por confiabilidade                           │
│  • Implementa rate limiting inteligente                         │
│  • Circuit breaker para APIs problemáticas                      │
└───────┬─────────────────┬─────────────────┬─────────────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
   Wikipedia         Wikidata          Jolpica/Ergast
   (0.5 req/s)       (1 req/s)         (0.2 req/s)
   Confiança: 0.7    Confiança: 0.9    Confiança: 0.95
```

---

## 🔍 Como Funciona a Auditoria (Passo a Passo)

### **Passo 1: Escaneamento do Banco de Dados**

O sistema lê a configuração em `auditor.py`:

```python
AUDIT_CONFIG = {
    'Driver': {
        'fields': ['date_of_birth', 'nationality'],
        'identifier_field': 'full_name',
        'search_methods': {
            'date_of_birth': 'find_driver_date_of_birth',
            'nationality': 'find_driver_nationality',
        }
    },
    'Circuit': {
        'fields': ['latitude', 'longitude', 'length_km'],
        'identifier_field': 'name',
        'search_methods': {
            'latitude': 'find_circuit_coordinates',
            'longitude': 'find_circuit_coordinates',
        }
    },
}
```

**O que é verificado:**
- **NULL**: Valores explicitamente nulos
- **String vazia ('')**: Para campos de texto
- **Zero (0)**: Para coordenadas (latitude/longitude)

**Exemplo de query:**
```python
# Para date_of_birth
empty_records = Driver.objects.filter(
    Q(date_of_birth__isnull=True) | Q(date_of_birth="")
)
```

### **Passo 2: Busca de Dados em Fontes Públicas**

Para cada campo vazio encontrado, o sistema busca dados seguindo uma **estratégia de prioridade**:

#### 🥇 **Prioridade 1: Wikidata (SPARQL Query)**

Wikidata é a fonte mais confiável e não tem rate limiting agressivo.

**Exemplo de busca para data de nascimento:**

```sparql
SELECT ?driver ?driverLabel ?birthDate ?countryLabel WHERE {
  ?driver wdt:P106 wd:Q10841764 .  # ocupação: piloto de Fórmula 1
  ?driver rdfs:label ?driverLabel .
  FILTER(CONTAINS(LCASE(?driverLabel), LCASE("Fernando Alonso")))
  OPTIONAL { ?driver wdt:P569 ?birthDate . }
  OPTIONAL { ?driver wdt:P27 ?country . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

**Retorna:**
```json
{
  "date_of_birth": "1981-07-29T00:00:00Z",
  "nationality": "Spain",
  "url": "https://query.wikidata.org/sparql",
  "source": "Wikidata",
  "confidence": 0.9
}
```

#### 🥈 **Prioridade 2: Wikipedia API**

Usado para informações textuais e contexto adicional.

**Exemplo de busca:**
```python
params = {
    'action': 'query',
    'format': 'json',
    'list': 'search',
    'srsearch': 'Fernando Alonso Formula 1 driver',
    'srlimit': 1
}
```

**Retorna:**
```json
{
  "title": "Fernando Alonso",
  "extract": "Fernando Alonso Díaz is a Spanish racing driver...",
  "url": "https://en.wikipedia.org/wiki/Fernando_Alonso",
  "source": "Wikipedia",
  "confidence": 0.7
}
```

#### 🥉 **Prioridade 3: Jolpica/Ergast API (Fallback)**

⚠️ **Usado APENAS se Wikidata falhar** devido ao rate limiting agressivo.

**Exemplo de busca:**
```
GET https://api.jolpi.ca/ergast/f1/drivers/alonso.json
```

**Retorna:**
```json
{
  "code": "ALO",
  "number": "14",
  "nationality": "Spanish",
  "date_of_birth": "1981-07-29",
  "url": "http://en.wikipedia.org/wiki/Fernando_Alonso",
  "source": "Jolpica/Ergast API",
  "confidence": 0.95
}
```

### **Passo 3: Rate Limiting Inteligente**

O sistema implementa **3 mecanismos** para evitar bloqueios:

#### 🔒 **1. Rate Limiter com Backoff Exponencial**

```python
class RateLimiter:
    def __init__(self, calls_per_second=0.5):
        self.min_interval = 2.0 segundos  # 0.5 req/s
        self.backoff_multiplier = 1.0      # Aumenta em caso de erro

    def wait(self):
        # Aguarda: min_interval * backoff_multiplier
        # Exemplo: 2s -> 4s -> 8s -> 16s -> 32s (max)
```

**Taxas configuradas:**
- Wikipedia: 0.5 req/s (1 chamada a cada 2 segundos)
- Wikidata: 1.0 req/s (1 chamada por segundo)
- Jolpica/Ergast: 0.2 req/s (1 chamada a cada 5 segundos) ⚠️

#### 🔌 **2. Circuit Breaker Pattern**

Se a API Ergast falhar **5 vezes consecutivas**, o sistema **para de tentar** automaticamente:

```python
if self.ergast_consecutive_failures >= 5:
    logger.info("Ergast circuit breaker ativo. Pulando.")
    return None
```

**Vantagens:**
- Evita desperdício de tempo
- Reduz stress na API problemática
- Foca em fontes funcionais (Wikidata)

#### 🎯 **3. Estratégia de Fallback**

```python
def find_driver_date_of_birth(driver_name, driver_id):
    # 1. Tentar Wikidata primeiro
    result = wikidata.search(driver_name)
    if result:
        return result  # SUCESSO - para aqui

    # 2. Ergast APENAS se circuit breaker permitir
    if is_ergast_available():
        result = ergast.search(driver_id)
        return result

    return None
```

### **Passo 4: Cálculo do Score de Confiança**

Cada fonte retorna um score de confiança:

| Fonte | Score | Motivo |
|-------|-------|--------|
| Wikidata | 0.9 | Dados estruturados, verificados pela comunidade |
| Ergast | 0.95 | API oficial F1 (quando funciona) |
| Wikipedia | 0.7 | Dados textuais, menos estruturados |

**Como é usado:**
```python
# Se múltiplas fontes retornam dados, escolhe o de maior confiança
results = [wikidata_result, ergast_result]
best_result = max(results, key=lambda x: x['confidence'])
```

### **Passo 5: Criação da Sugestão**

Após encontrar um valor, o sistema cria uma **sugestão** no banco:

```python
DataAuditSuggestion.objects.create(
    report=report,
    table_name='Driver',
    field_name='date_of_birth',
    record_id=123,
    record_identifier='Fernando Alonso',
    current_value=None,  # Estava vazio
    suggested_value='1981-07-29',
    confidence_score=0.9,
    source_name='Wikidata',
    source_url='https://query.wikidata.org/sparql',
    applied=False,  # Não aplicado automaticamente
    rejected=False
)
```

---

## 📊 Estrutura dos Dados

### **DataAuditReport (Relatório)**

```python
{
  "id": 1,
  "execution_date": "2025-11-09T17:11:47Z",
  "status": "completed",
  "execution_time_seconds": 174.44,
  "total_tables_scanned": 2,
  "total_fields_scanned": 5,
  "total_empty_fields_found": 214,
  "total_suggestions_found": 18,
  "audit_results": {
    "tables": {
      "Driver": {
        "fields": {
          "date_of_birth": {
            "empty_count": 43,
            "suggestion_count": 9
          }
        }
      }
    }
  }
}
```

### **DataAuditSuggestion (Sugestão Individual)**

```python
{
  "id": 1,
  "table_name": "Driver",
  "field_name": "date_of_birth",
  "record_id": 42,
  "record_identifier": "Fernando Alonso",
  "current_value": null,
  "suggested_value": "1981-07-29",
  "confidence_score": 0.9,
  "source_name": "Wikidata",
  "source_url": "https://query.wikidata.org/sparql",
  "applied": false,
  "rejected": false,
  "created_at": "2025-11-09T17:11:57Z"
}
```

---

## 🚀 Performance e Otimizações

### **Limitações Implementadas**

1. **Máximo 10 sugestões por campo**
   - Evita sobrecarga em campos com muitos vazios
   - Exemplo: Se 43 drivers não têm data de nascimento, busca apenas 10

2. **Rate limiting adaptativo**
   - Aumenta intervalo automaticamente em caso de erro
   - Reduz quando tudo normaliza

3. **Circuit breaker**
   - Para de tentar APIs problemáticas
   - Economiza tempo e recursos

### **Tempo de Execução Típico**

- **Driver (43 campos vazios):** ~1-2 minutos
- **Circuit (17 campos vazios):** ~1-2 minutos
- **Total:** ~3 minutos

**Fatores que afetam:**
- Rate limiting (2-5 segundos por requisição)
- APIs lentas ou indisponíveis
- Número de campos vazios

---

## 🔄 Fluxo Completo (Exemplo Real)

### **Cenário: Driver sem data de nascimento**

1. **Detecção:**
```python
driver = Driver.objects.get(id=42)
# driver.full_name = "Fernando Alonso"
# driver.date_of_birth = None  ❌ VAZIO
```

2. **Busca no Wikidata:**
```
⏳ Aguardando rate limiter (2 segundos)...
🔎 Query SPARQL para "Fernando Alonso"
✅ Encontrado: 1981-07-29 (confidence: 0.9)
```

3. **Criação da Sugestão:**
```
💾 Sugestão criada:
   Tabela: Driver
   Campo: date_of_birth
   Registro: Fernando Alonso (#42)
   Valor atual: NULL
   Valor sugerido: 1981-07-29
   Fonte: Wikidata
   Confiança: 90%
```

4. **Exibição no Frontend:**
```
📊 Status > Auditoria de Dados
┌─────────────┬───────────────┬─────────────────┬─────────────┐
│ Tabela      │ Campo         │ Registro        │ Sugestão    │
├─────────────┼───────────────┼─────────────────┼─────────────┤
│ Driver      │ date_of_birth │ Fernando Alonso │ 1981-07-29  │
│             │               │                 │ 🟢 90%      │
└─────────────┴───────────────┴─────────────────┴─────────────┘
```

---

## 🛠️ Correções de Rate Limiting Aplicadas

### **Problema Anterior**
```
❌ ERROR 429: Too Many Requests
   Jolpica/Ergast bloqueando após 5-10 requisições
```

### **Soluções Implementadas**

#### ✅ **1. Rate Limiter com Backoff Exponencial**
```python
# ANTES: Intervalo fixo de 1 segundo
time.sleep(1.0)

# DEPOIS: Intervalo adaptativo
backoff_multiplier = 2 ** consecutive_errors  # 1x, 2x, 4x, 8x...
adjusted_interval = base_interval * backoff_multiplier
time.sleep(adjusted_interval)
```

#### ✅ **2. Taxas Mais Conservadoras**
```python
# ANTES
ErgastAPI: 1.0 req/s  ❌ Muito rápido

# DEPOIS
ErgastAPI: 0.2 req/s  ✅ 1 chamada a cada 5 segundos
Wikipedia: 0.5 req/s  ✅ 1 chamada a cada 2 segundos
Wikidata:  1.0 req/s  ✅ Sem problemas
```

#### ✅ **3. Circuit Breaker Pattern**
```python
if ergast_consecutive_failures >= 5:
    logger.warning("Ergast circuit breaker ativo. Usando apenas Wikidata.")
    return None  # Para de tentar
```

#### ✅ **4. Priorização de Fontes**
```python
# ANTES: Tentava todas as fontes em paralelo
# DEPOIS: Prioriza Wikidata, usa Ergast apenas como fallback

1. Wikidata (sempre tenta) ✅
2. Ergast (só se Wikidata falhar E circuit breaker permitir)
```

---

## 📈 Monitoramento e Logs

### **Logs Detalhados**

```
INFO: Auditando modelo: Driver
INFO:   Total de registros em Driver: 429
INFO:     Campo 'date_of_birth': 43 registros vazios
INFO:       Sugestão criada: Fernando Alonso -> date_of_birth = 1981-07-29
WARNING: Rate limit 429 para https://api.jolpi.ca/...
WARNING: Rate limit error. Backoff aumentado para 2x
INFO: Ergast circuit breaker ativo (5 falhas). Pulando.
INFO: Auditoria concluída em 174.44s
INFO: Total de sugestões: 18
```

### **Métricas no Frontend**

Acesse: `http://localhost:8102/status` > **🔍 Auditoria de Dados**

```
📊 Estatísticas:
   • Tabelas Escaneadas: 2
   • Campos Vazios: 214
   • Sugestões Encontradas: 18
   • Tempo de Execução: 174.4s

📋 Sugestões Pendentes: 18
✅ Sugestões Aplicadas: 0
❌ Sugestões Rejeitadas: 0
```

---

## 🎯 Próximos Passos Possíveis

1. **Aplicação Manual de Sugestões**
   - Adicionar botão "Aplicar" no frontend
   - Endpoint: `POST /api/data-audit-suggestions/{id}/apply/`

2. **Mais Modelos**
   - Auditar Team, Event, Session
   - Buscar dados históricos faltantes

3. **Mais Fontes**
   - OpenF1 API
   - Formula1.com scraping (com permissão)

4. **Filtros Avançados**
   - Filtrar por tabela/campo
   - Ordenar por confiança

---

## 📞 Troubleshooting

### **"Nenhum relatório encontrado"**
```bash
# Executar auditoria manual
docker exec f1-api python manage.py shell -c \
  "from data_auditor.auditor import run_audit; run_audit()"
```

### **"Muitos erros 429"**
```python
# Verificar logs
docker logs f1-api | grep "429"

# Se persistir, aumentar intervalo em web_sources.py:
ErgastAPISource(calls_per_second=0.1)  # 1 chamada a cada 10 segundos
```

### **"Circuit breaker sempre ativo"**
```python
# Resetar contador manualmente no Django shell
from data_auditor.web_sources import DataSourceAggregator
aggregator = DataSourceAggregator()
aggregator.ergast_consecutive_failures = 0
```

---

## 📚 Referências

- **Wikidata Query Service:** https://query.wikidata.org/
- **Wikipedia API:** https://www.mediawiki.org/wiki/API:Main_page
- **Jolpica F1 API:** https://github.com/jolpica/jolpica-f1
- **Circuit Breaker Pattern:** https://martinfowler.com/bliki/CircuitBreaker.html

---

**Desenvolvido com ❤️ para FastF1 React App**
