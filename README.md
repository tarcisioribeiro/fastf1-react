# 🏎️ F1 Dashboard

Dashboard interativo para acompanhar dados da Fórmula 1, incluindo resultados de corridas, qualificações e classificações de pilotos e construtores.

## 🚀 Características

- ✅ Resultados da última corrida
- ✅ Resultados da última qualificação
- ✅ Classificação de pilotos
- ✅ Classificação de construtores
- ✅ Cache inteligente com SQLite
- ✅ Interface limpa e responsiva
- ✅ Destaque para pódio (ouro, prata, bronze)

## 📦 Tecnologias

- **Streamlit** - Framework web
- **FastF1** - API de dados da F1
- **SQLite** - Cache de dados
- **Pandas** - Manipulação de dados
- **Docker** - Containerização

## 🏁 Como executar

### Opção 1: Localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
streamlit run app.py
```

A aplicação estará disponível em `http://localhost:8501`

### Opção 2: Docker Compose (Recomendado)

```bash
# Construir e executar
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar
docker-compose down
```

A aplicação estará disponível em `http://localhost:8501`

## 📁 Estrutura do projeto

```
.
├── app.py              # Dashboard principal
├── f1_data.py          # Gerenciador de dados da F1
├── database.py         # Gerenciador de cache SQLite
├── requirements.txt    # Dependências Python
├── Dockerfile          # Imagem Docker
├── docker-compose.yml  # Orquestração Docker
└── README.md          # Este arquivo
```

## 💾 Cache

O sistema utiliza dois níveis de cache:

1. **FastF1 Cache** - Cache de dados brutos da API (`.fastf1_cache/`)
2. **SQLite Cache** - Cache de dados processados (`f1_cache.db`)

O cache SQLite tem validade de 24 horas e acelera significativamente o carregamento das páginas.

## 🎨 Interface

- Design limpo e minimalista
- Sem poluição visual
- Cores sutis para destaque (ouro, prata, bronze para pódio)
- Tabelas bem formatadas
- Responsivo e fácil de navegar

## 📊 Dados

Todos os dados são obtidos através da biblioteca FastF1, que fornece:
- Resultados oficiais de corridas
- Tempos de qualificação
- Pontuações de campeonatos
- Informações de pilotos e equipes

**Temporada atual:** 2025

## 🔧 Desenvolvimento

Para modificar o código:

1. `app.py` - Interface e visualização
2. `f1_data.py` - Lógica de busca e formatação de dados
3. `database.py` - Sistema de cache

## 📝 Licença

MIT
