# Guia de Testes - Sistema de ML para Previsões F1

Este documento descreve como testar o sistema de Machine Learning implementado para previsões de desempenho na Fórmula 1.

## 📋 Pré-requisitos

1. **Instalar dependências atualizadas**:
```bash
cd backend
source backend_venv/bin/activate
pip install -r requirements.txt
```

2. **Verificar se os serviços estão rodando via Docker**:
```bash
docker compose ps
```

Certifique-se de que os seguintes serviços estão UP:
- `mysql`
- `redis`
- `django-api`
- `celery-worker`
- `celery-beat`

## 🚀 Passo 1: Treinar os Modelos pela Primeira Vez

### Opção A: Via Django Shell (Recomendado para teste inicial)

```bash
# Entrar no container Django
docker compose exec django-api bash

# Ativar ambiente virtual
source backend_venv/bin/activate

# Abrir Django shell
python manage.py shell
```

Dentro do shell Python:

```python
# Importar a função de treinamento
from ml.trainer import train_all_models

# Treinar modelos do zero (pode levar vários minutos)
results = train_all_models(year_start=2018, year_end=None, incremental=False)

# Ver resultados
print(results)

# Ver métricas do modelo de lap_time
if results['lap_time']['status'] == 'success':
    metrics = results['lap_time']['metrics']
    print(f"Lap Time Model - Test MAE: {metrics['test']['mae']:.2f}")
    print(f"Lap Time Model - Test RMSE: {metrics['test']['rmse']:.2f}")
    print(f"Lap Time Model - Test R²: {metrics['test']['r2']:.3f}")

# Ver métricas do modelo de position
if results['position']['status'] == 'success':
    metrics = results['position']['metrics']
    print(f"Position Model - Test MAE: {metrics['test']['mae']:.2f}")
    print(f"Position Model - Test RMSE: {metrics['test']['rmse']:.2f}")
    print(f"Position Model - Test R²: {metrics['test']['r2']:.3f}")
```

### Opção B: Via Celery Task

```bash
# Entrar no container Django
docker compose exec django-api bash

# Ativar ambiente virtual
source backend_venv/bin/activate

# Executar tarefa de treinamento
python manage.py shell
```

```python
from data_collector.tasks import train_ml_models_from_scratch

# Executar tarefa assíncrona
result = train_ml_models_from_scratch.delay()

# Verificar status
print(f"Task ID: {result.id}")
print(f"Task Status: {result.status}")

# Aguardar conclusão (pode levar vários minutos)
result.wait()

# Ver resultado
print(result.result)
```

## 🧪 Passo 2: Verificar Modelos Salvos

```bash
# Listar arquivos de modelos
docker compose exec django-api ls -lh /app/models/

# Você deve ver arquivos como:
# - lap_time_predictor.pkl
# - lap_time_scaler.pkl
# - lap_time_metadata.json
# - lap_time_features.json
# - position_predictor.pkl
# - position_scaler.pkl
# - position_metadata.json
# - position_features.json
```

## 📊 Passo 3: Testar Previsões via API

### 3.1 Testar Previsão de Piloto

```bash
# Via curl (substituir VER e Monaco pelos valores desejados)
curl "http://localhost:8000/api/predictions/driver/?driver=VER&circuit=Monaco&use_ml=true"

# Ou via navegador
http://localhost:8000/api/predictions/driver/?driver=VER&circuit=Monaco&use_ml=true
```

**Resposta esperada**: JSON com campos `prediction` (método estatístico) e `mlPrediction` (ML):

```json
{
  "status": "success",
  "driver": {
    "code": "VER",
    "fullName": "Max Verstappen",
    "number": 1
  },
  "circuit": {
    "name": "Monaco",
    "location": "Monte Carlo",
    "country": "Monaco"
  },
  "prediction": {
    "averagePosition": 2.5,
    "averagePoints": 18.3,
    "predictedPositionRange": {
      "min": 1,
      "max": 4
    },
    "probabilities": {
      "win": 45.2,
      "podium": 78.5,
      "points": 92.1
    },
    "blendedPosition": 2.3
  },
  "mlPrediction": {
    "predictedPosition": 2.1,
    "positionRange": {
      "min": 1,
      "max": 4
    },
    "raceLapTime": 78.5,
    "qualifyingLapTime": 72.3,
    "modelInfo": {
      "lap_time_model": {...},
      "position_model": {...}
    }
  },
  "statistics": {...},
  "history": [...]
}
```

### 3.2 Testar Previsão de Equipe

```bash
# Via curl
curl "http://localhost:8000/api/predictions/constructor/?team=Red%20Bull&circuit=Monza&use_ml=true"

# Ou via navegador
http://localhost:8000/api/predictions/constructor/?team=Red Bull&circuit=Monza&use_ml=true
```

### 3.3 Desabilitar ML (usar apenas método estatístico)

```bash
curl "http://localhost:8000/api/predictions/driver/?driver=HAM&circuit=Silverstone&use_ml=false"
```

## 🔄 Passo 4: Testar Treinamento Incremental

Após coletar novos dados, testar atualização incremental:

```bash
docker compose exec django-api python manage.py shell
```

```python
from ml.trainer import train_all_models

# Treinamento incremental (atualiza modelos existentes)
results = train_all_models(year_start=2018, incremental=True)

print(results)
```

## ⏰ Passo 5: Verificar Execução Automática via Celery Beat

```bash
# Ver logs do Celery Beat para confirmar que a tarefa está agendada
docker compose logs -f celery-beat | grep "ml-models"

# Você deve ver logs como:
# celery-beat | Scheduler: Sending due task train-ml-models-every-6h
```

```bash
# Ver logs do Celery Worker para ver execução
docker compose logs -f celery-worker | grep -i "ml"
```

## 🔍 Passo 6: Verificar Métricas dos Modelos

```bash
docker compose exec django-api python manage.py shell
```

```python
from ml.predictor import get_predictor

# Carregar preditor
predictor = get_predictor()

# Ver informações dos modelos
info = predictor.get_model_info()
print(info)

# Verificar se modelos estão prontos
print(f"Ready: {predictor.is_ready()}")
```

## 📈 Passo 7: Monitorar Performance

### Ver logs de treinamento

```bash
# Ver logs de ML no container Django
docker compose exec django-api tail -f /app/logs/ml.log

# Ou ver logs gerais
docker compose logs -f django-api | grep -i "ml"
```

### Verificar metadata dos modelos

```bash
# Ver metadata do modelo de lap_time
docker compose exec django-api cat /app/models/lap_time_metadata.json

# Ver metadata do modelo de position
docker compose exec django-api cat /app/models/position_metadata.json
```

## 🐛 Troubleshooting

### Problema: Modelos não são encontrados

**Solução**: Execute o treinamento inicial (Passo 1).

### Problema: Erro "ML_AVAILABLE = False"

**Solução**: Verifique se as dependências foram instaladas:
```bash
docker compose exec django-api pip list | grep scikit-learn
docker compose exec django-api pip list | grep joblib
```

Se não aparecerem, reinstale:
```bash
docker compose exec django-api pip install scikit-learn joblib
```

### Problema: Erro "Not enough samples"

**Solução**: Certifique-se de que há dados suficientes no banco:
```bash
docker compose exec django-api python manage.py shell
```

```python
from core.models import LapTime, RaceResult

print(f"Lap Times: {LapTime.objects.count()}")
print(f"Race Results: {RaceResult.objects.count()}")

# Você precisa de pelo menos 100 lap times e 50 race results
```

### Problema: Previsões não incluem campo mlPrediction

**Possíveis causas**:
1. Parâmetro `use_ml=false` na URL
2. Modelos não foram treinados
3. Erro durante previsão (verificar logs)

**Solução**: Verificar logs e status dos modelos conforme Passo 6.

## ✅ Checklist Final

- [ ] Dependências instaladas (scikit-learn, joblib)
- [ ] Modelos treinados pela primeira vez
- [ ] Arquivos .pkl presentes em `/app/models/`
- [ ] API retorna campo `mlPrediction` nas respostas
- [ ] Celery Beat agendou tarefa `train-ml-models-every-6h`
- [ ] Logs de ML aparecem corretamente
- [ ] Treinamento incremental funciona

## 📞 Comandos Úteis

```bash
# Rebuild containers após adicionar dependências
docker compose build
docker compose restart

# Ver todos os logs
docker compose logs -f

# Restart apenas o Django
docker compose restart django-api

# Restart Celery workers
docker compose restart celery-worker celery-beat

# Limpar cache Redis (se necessário)
docker compose exec redis redis-cli FLUSHALL
```
