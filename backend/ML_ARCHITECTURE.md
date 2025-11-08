# Arquitetura do Sistema de Machine Learning - F1 Predictions

## 📐 Visão Geral

Este documento descreve a arquitetura completa do sistema de Machine Learning implementado para previsões de desempenho na Fórmula 1.

## 🏗️ Estrutura de Diretórios

```
backend/
├── ml/                              # Módulo de Machine Learning
│   ├── __init__.py
│   ├── feature_engineering.py      # Preparação de features do banco de dados
│   ├── trainer.py                  # Treinamento e gerenciamento de modelos
│   └── predictor.py                # Interface para fazer previsões
│
├── models/                          # Modelos treinados (não versionados)
│   ├── .gitignore
│   ├── .gitkeep
│   ├── lap_time_predictor.pkl      # Modelo para previsão de tempos de volta
│   ├── lap_time_scaler.pkl         # Scaler para normalização de features
│   ├── lap_time_metadata.json      # Metadados do modelo (métricas, datas)
│   ├── lap_time_features.json      # Lista de features esperadas
│   ├── position_predictor.pkl      # Modelo para previsão de posições
│   ├── position_scaler.pkl
│   ├── position_metadata.json
│   └── position_features.json
│
├── data_collector/
│   └── tasks.py                    # Tarefas Celery (inclui treinamento ML)
│
└── api/
    └── views.py                    # Endpoints API (integrado com ML)
```

## 🧩 Componentes

### 1. Feature Engineering (`ml/feature_engineering.py`)

**Responsabilidade**: Extrair e preparar features do banco de dados MySQL para treinamento e previsão.

**Principais Funções**:

- `prepare_lap_time_features()`: Prepara features para previsão de tempos de volta
  - **Features**:
    - `lap_number`, `sector1_time`, `sector2_time`, `sector3_time`
    - `compound` (pneu), `tyre_life` (idade do pneu)
    - `session_type` (R, Q, etc.)
    - `driver_code`, `team_name`, `circuit_name` (one-hot encoded)
    - `air_temp`, `track_temp`, `humidity`, `rainfall`, `wind_speed`
  - **Target**: `lap_time` (em segundos)

- `prepare_position_features()`: Prepara features para previsão de posições finais
  - **Features**:
    - `grid_position`, `quali_position`
    - `driver_code`, `team_name`, `circuit_name` (one-hot encoded)
    - `year`, `laps_completed`, `pit_stops`, `dnf`
    - `air_temp`, `track_temp`, `humidity`, `rainfall`
  - **Target**: `position` (posição final)

- `encode_categorical()`: One-hot encoding para variáveis categóricas
- `align_features()`: Alinha features de entrada com features esperadas pelo modelo

**Otimizações**:
- Limite de 50.000 lap times para evitar estouro de memória
- Tratamento de valores ausentes e NaN
- Conversão de timedelta para segundos
- Filtragem de dados inválidos (is_accurate=True)

### 2. Trainer (`ml/trainer.py`)

**Responsabilidade**: Treinar, atualizar e persistir modelos de ML.

**Classe Principal**: `F1PerformanceModel`

**Modelos Suportados**:
1. **Lap Time Predictor**:
   - Algoritmo: `GradientBoostingRegressor`
   - Parâmetros: 100 estimators, learning_rate=0.1, max_depth=5
   - Suporta `warm_start` para treinamento incremental

2. **Position Predictor**:
   - Algoritmo: `RandomForestRegressor`
   - Parâmetros: 100 estimators, max_depth=10
   - Suporta `warm_start` para treinamento incremental

**Métodos Principais**:

- `train()`: Treina ou atualiza o modelo
  - Modo inicial: treina do zero com todos os dados históricos
  - Modo incremental: carrega modelo existente e continua treinamento
  - Split: 80% treino, 20% teste
  - Normalização: `StandardScaler`
  - Avaliação: MAE, RMSE, R²

- `save_model()`: Persiste modelo, scaler, metadata e feature names
- `load_model()`: Carrega modelo e configurações do disco
- `predict()`: Faz previsões com dados novos

**Função Global**: `train_all_models()`
- Treina todos os modelos (lap_time e position)
- Retorna métricas de desempenho
- Usado pelas tarefas Celery

**Métricas de Avaliação**:
- **MAE (Mean Absolute Error)**: Erro médio absoluto
- **RMSE (Root Mean Squared Error)**: Raiz do erro quadrático médio
- **R² (Coefficient of Determination)**: Capacidade de explicar variância

### 3. Predictor (`ml/predictor.py`)

**Responsabilidade**: Interface de alto nível para fazer previsões usando modelos treinados.

**Classe Principal**: `F1Predictor`

**Padrão Singleton**: Instância global compartilhada (`get_predictor()`)

**Métodos Principais**:

- `predict_lap_time()`: Prevê tempo de volta para condições específicas
  - Parâmetros: driver, team, circuit, session_type, lap_number, compound, tyre_life, weather
  - Retorna: tempo em segundos

- `predict_position()`: Prevê posição final de corrida
  - Parâmetros: driver, team, circuit, grid_position, quali_position, weather
  - Retorna: posição prevista (float)

- `predict_driver_performance()`: Previsão completa para um piloto
  - Combina previsões de lap_time (race e quali) e position
  - Retorna: dict com todas as previsões + metadata

- `predict_constructor_performance()`: Previsão completa para uma equipe
  - Agrega previsões dos 2 pilotos da equipe
  - Retorna: dict com previsões agregadas + metadata

- `reload_models()`: Recarrega modelos do disco (usado após treinamento)
- `is_ready()`: Verifica se modelos estão carregados
- `get_model_info()`: Retorna metadata dos modelos

**Tratamento de Erros**:
- Se modelo não disponível, retorna None
- Logs de warning/error para debugging
- Não quebra a aplicação se ML falhar

### 4. Tarefas Celery (`data_collector/tasks.py`)

**Novas Tarefas Adicionadas**:

- `train_ml_models()`: Tarefa principal de treinamento
  - Parâmetros: incremental (bool), year_start (int)
  - Retries: 3 tentativas com countdown de 5 minutos
  - Recarrega predictor após treinamento
  - Registra métricas nos logs

- `train_ml_models_from_scratch()`: Treina do zero (não incremental)
  - Usado para treinamento inicial ou rebuild completo

- `update_ml_models()`: Atualização incremental
  - Usado para updates regulares com novos dados

- `check_and_train_ml_models()`: Verifica existência dos modelos
  - Se não existem: treina do zero
  - Se existem: atualização incremental
  - **Executada automaticamente a cada 6 horas via Celery Beat**

**Configuração Celery Beat** (`config/celery.py`):
```python
'train-ml-models-every-6h': {
    'task': 'data_collector.tasks.check_and_train_ml_models',
    'schedule': crontab(minute=0, hour='*/6'),  # A cada 6 horas
}
```

### 5. API Integration (`api/views.py`)

**Modificações nos Endpoints Existentes**:

#### `driver_prediction`
- **Novo parâmetro**: `use_ml` (default: true)
- **Fluxo**:
  1. Tenta usar ML se disponível e `use_ml=true`
  2. Executa método estatístico (média histórica ponderada)
  3. Combina ambos os resultados (blend: 60% ML + 40% estatístico)
- **Resposta**:
  - `prediction`: método estatístico original
  - `mlPrediction`: previsões do modelo ML
  - `blendedPosition`: combinação dos dois métodos

#### `constructor_prediction`
- **Novo parâmetro**: `use_ml` (default: true)
- **Fluxo**: similar ao driver_prediction
- **Resposta**: estrutura similar com ML + estatístico

**Fallback Automático**:
- Se ML falhar ou não estiver disponível, API continua funcionando com método estatístico
- Logs de warning registram falhas de ML
- 100% retrocompatível com versões anteriores

## 🔄 Fluxo de Dados

### Treinamento Inicial (First-time)
```
1. Coletar dados via FastF1 API → MySQL
2. Executar train_ml_models_from_scratch()
3. Feature Engineering lê dados do MySQL
4. Preparar features (one-hot encoding, normalização)
5. Treinar modelos (GradientBoosting + RandomForest)
6. Avaliar com teste set (20%)
7. Salvar modelos (.pkl) + metadata (.json)
8. Predictor carrega modelos em memória
```

### Treinamento Incremental (Periodic)
```
1. Novos dados coletados → MySQL
2. Celery Beat trigger (a cada 6h)
3. check_and_train_ml_models() executa
4. Carregar modelos existentes
5. Feature Engineering lê novos dados
6. Treinar incrementalmente (warm_start=True)
7. Re-avaliar métricas
8. Salvar modelos atualizados
9. Predictor recarrega modelos
```

### Previsão via API
```
1. Request: GET /api/predictions/driver/?driver=VER&circuit=Monaco
2. API valida parâmetros (driver, circuit)
3. Se use_ml=true:
   a. get_predictor() retorna singleton
   b. Buscar últimos dados de weather
   c. predict_driver_performance()
   d. Modelo carregado faz previsão
4. Executar método estatístico (sempre)
5. Combinar resultados (blend)
6. Response com prediction + mlPrediction
```

## 📊 Dados e Features

### Fontes de Dados

**Período**: 2018 até presente (FastF1 API)

**Tabelas Principais**:
- `LapTime`: ~50k registros por temporada
- `RaceResult`: ~400 registros por temporada
- `WeatherData`: ~1000 registros por corrida
- `PitStop`: ~60 registros por corrida

### Pipeline de Features

1. **Extração**: SQL queries via Django ORM
2. **Transformação**:
   - Conversão de timedelta → segundos
   - One-hot encoding de categóricas (driver, team, circuit, compound)
   - Tratamento de valores ausentes
3. **Normalização**: StandardScaler (μ=0, σ=1)
4. **Alinhamento**: garantir mesmas features entre treino e previsão

### Feature Importance (Estimado)

**Lap Time Model**:
1. Sector times (alto impacto)
2. Circuit (médio-alto)
3. Weather (track_temp, air_temp)
4. Team/Driver (médio)
5. Tyre compound/life (médio)

**Position Model**:
1. Grid position (alto impacto)
2. Team (alto)
3. Circuit (médio-alto)
4. Driver (médio)
5. Weather (baixo-médio)

## 🎯 Métricas de Performance Esperadas

### Lap Time Model
- **MAE**: 0.5 - 2.0 segundos (quanto menor, melhor)
- **RMSE**: 1.0 - 3.0 segundos
- **R²**: 0.75 - 0.90 (quanto mais próximo de 1, melhor)

### Position Model
- **MAE**: 1.5 - 3.0 posições
- **RMSE**: 2.0 - 4.0 posições
- **R²**: 0.60 - 0.80

**Nota**: Métricas variam conforme quantidade e qualidade dos dados disponíveis.

## 🔧 Configuração e Deployment

### Variáveis de Ambiente
```bash
# Nenhuma configuração adicional necessária
# Modelos são salvos em settings.BASE_DIR/models/
```

### Requirements
```
scikit-learn==1.5.2
joblib==1.4.2
```

### Docker
- Modelos são salvos em volume persistente (opcional)
- Container Django precisa acessar `/app/models/`
- Celery worker precisa acesso ao mesmo volume

### Logs
```python
import logging
logger = logging.getLogger('ml')
logger.info("Training complete")
```

Logs aparecem em:
- Django logs: `docker compose logs django-api | grep ml`
- Celery logs: `docker compose logs celery-worker | grep ml`

## 🚀 Próximas Melhorias

### Curto Prazo
- [ ] Adicionar modelo para previsão de fastest lap
- [ ] Implementar cross-validation para validação mais robusta
- [ ] Adicionar feature de form recente (últimas 3 corridas)
- [ ] Grid search para otimização de hiperparâmetros

### Médio Prazo
- [ ] Implementar ensemble de modelos (combinar vários algoritmos)
- [ ] Adicionar previsões de probabilidade (classificação)
- [ ] Feature engineering avançado (rolling averages, lag features)
- [ ] A/B testing entre diferentes algoritmos

### Longo Prazo
- [ ] Deep Learning com redes neurais (LSTM para séries temporais)
- [ ] Auto-ML para seleção automática de modelos
- [ ] Previsões em tempo real durante corridas
- [ ] Sistema de recomendação de estratégia de pneus

## 📚 Referências

- **Scikit-learn**: https://scikit-learn.org/
- **FastF1 API**: https://docs.fastf1.dev/
- **GradientBoosting**: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html
- **RandomForest**: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html

## 🤝 Contribuindo

Para adicionar novos modelos ou features:

1. Adicionar nova função em `feature_engineering.py`
2. Criar novo modelo em `trainer.py` (herdar de `F1PerformanceModel`)
3. Adicionar método de previsão em `predictor.py`
4. Integrar no endpoint API em `views.py`
5. Adicionar testes em `ML_TESTING.md`
6. Atualizar esta documentação
