# Tarefas Pendentes - FastF1 React

## 🔴 Alta Prioridade

### Coletar Dados de Fastest Lap Time

**Status:** Pendente
**Prioridade:** Alta
**Estimativa:** 4-6 horas

#### Descrição
Atualmente, apenas 40 de 4156 resultados de corrida (< 1%) possuem o campo `fastest_lap_time` preenchido no banco de dados. Isso impede o treinamento do modelo de ML para previsão de volta mais rápida.

#### Objetivo
Modificar o sistema de coleta de dados para capturar e armazenar corretamente os tempos de volta mais rápida de cada piloto em todas as corridas.

#### Arquivos a Modificar

1. **`backend/data_collector/tasks.py`**
   - Modificar a função `collect_session_data()` para extrair `fastest_lap_time` dos dados da FastF1
   - Verificar se a API FastF1 fornece esses dados no objeto `session.results`

2. **`backend/core/models.py`** (verificar se já existe)
   - Confirmar que o campo `fastest_lap_time` existe no modelo `RaceResult`
   - Formato esperado: `DurationField` ou `FloatField` (segundos)

#### Passos para Implementação

```python
# 1. Em data_collector/tasks.py, função collect_session_data()

# Exemplo de código a adicionar:
if session_type == 'R':  # Race
    for driver_code in results.index:
        result = results.loc[driver_code]

        # ADICIONAR: Capturar fastest lap time
        fastest_lap = None
        try:
            if hasattr(result, 'FastestLapTime'):
                fastest_lap_td = result['FastestLapTime']
                if pd.notna(fastest_lap_td):
                    # Converter Timedelta para segundos
                    fastest_lap = fastest_lap_td.total_seconds()
        except Exception as e:
            logger.warning(f"Não foi possível obter fastest lap para {driver_code}: {e}")

        # Ao salvar RaceResult
        race_result, created = RaceResult.objects.update_or_create(
            session=session_obj,
            driver=driver_obj,
            defaults={
                'position': position,
                'grid_position': grid,
                'points': points,
                'laps_completed': laps,
                'total_race_time': total_time,
                'fastest_lap_time': fastest_lap,  # ADICIONAR ESTE CAMPO
                'fastest_lap_number': fastest_lap_num,
                'status': driver_status,
                'dnf': dnf
            }
        )
```

#### Verificação

Após implementar, executar:

```bash
# 1. Rebuild do container
docker compose build django-api

# 2. Restart dos serviços
docker compose restart django-api celery-worker

# 3. Reprocessar uma corrida recente para testar
docker compose exec django-api python manage.py shell
>>> from data_collector.tasks import collect_session_data
>>> collect_session_data(2024, 1, 'R')  # Bahrain 2024 Race

# 4. Verificar se os dados foram salvos
>>> from core.models import RaceResult
>>> results_with_fastest = RaceResult.objects.filter(
...     fastest_lap_time__isnull=False,
...     session__event__season__year=2024
... ).count()
>>> print(f"Resultados com fastest lap: {results_with_fastest}")
```

#### Documentação FastF1

Consultar documentação oficial:
- https://docs.fastf1.dev/core.html#session-results
- https://docs.fastf1.dev/core.html#fastf1.core.SessionResults

Campos disponíveis no `SessionResults`:
- `FastestLap`: Número da volta mais rápida
- `FastestLapTime`: Timedelta com o tempo da volta mais rápida
- `FastestLapSpeed`: Velocidade na volta mais rápida (km/h)

#### Após Conclusão

Uma vez implementado e com dados coletados, treinar o modelo:

```bash
docker compose exec django-api python manage.py train_ml_models --model fastest_lap --full
```

---

## 🟡 Média Prioridade

### Melhorar Precisão do Modelo de Pole Position

**Status:** Opcional
**Prioridade:** Média

#### Descrição
O modelo de pole position tem:
- Accuracy: 94.6% ✅
- F1-Score: 0.098 ⚠️ (baixo devido a classes desbalanceadas)

#### Possíveis Melhorias
1. Aplicar técnicas de balanceamento de classes (SMOTE, class_weight)
2. Ajustar threshold de classificação
3. Usar ensemble de modelos
4. Adicionar mais features específicas de qualifying

---

## 🟢 Baixa Prioridade

### Adicionar Previsão de Podium (Top 3)

**Status:** Ideia
**Prioridade:** Baixa

Criar modelo para prever probabilidade de pódio (top 3) em vez de apenas posição exata.

---

## ✅ Concluído

- [x] Implementar feature engineering avançado (momentum, histórico, trends)
- [x] Adicionar XGBoost e LightGBM
- [x] Treinar modelo de posição com 120 features
- [x] Treinar modelo de pole position
- [x] Criar endpoints de API para previsões de pole
- [x] Integrar previsões no frontend
- [x] Melhorar precisão do modelo de posição (MAE: 1.88)

---

## 📝 Notas

- Modelo de fastest lap depende de dados de `fastest_lap_time`
- Sistema de ML está otimizado e funcionando
- Todos os modelos treinados estão em `/app/models/`
- Logs disponíveis via `docker compose logs django-api`

**Última atualização:** 2025-11-11
