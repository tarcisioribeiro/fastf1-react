# Documentação do Projeto FastF1 React

Bem-vindo à documentação completa do projeto FastF1 React - uma aplicação full-stack para visualização de dados da Fórmula 1 usando a biblioteca FastF1.

## 📚 Índice Geral

### 🗂️ Documentação por Área

1. **[Modelos do Banco de Dados](models/README.md)**
   - Todos os modelos Django (Season, Driver, Team, Circuit, etc.)
   - Relacionamentos entre modelos
   - Campos, índices e validações
   - Boas práticas para queries

2. **[API REST](api/README.md)**
   - Todos os endpoints disponíveis
   - Parâmetros de request/response
   - Exemplos de uso com cURL e JavaScript
   - Códigos de status e erros
   - Cache e performance

3. **[Celery Tasks](tasks/README.md)**
   - Tasks de coleta de dados
   - Processadores de dados (corridas, classificações, sprints)
   - Funções auxiliares
   - Execução manual e monitoramento
   - Troubleshooting

4. **[Frontend React + TypeScript](frontend/README.md)**
   - Tipos TypeScript (interfaces)
   - Componentes reutilizáveis
   - Contextos (tema)
   - Serviços (API client)
   - Rotas e navegação
   - Sistema de temas

5. **[Guia de Desenvolvimento](guides/DEVELOPMENT.md)**
   - Setup do ambiente
   - Padrões de código (Python, TypeScript, CSS)
   - Estrutura de commits
   - Testing e debugging
   - **Consulta à documentação FastF1** ⚠️
   - Troubleshooting comum

---

## 🚀 Quick Start

### Para Desenvolvedores

```bash
# 1. Clonar repositório
git clone <repo-url>
cd fastf1-react

# 2. Criar .env
cp .env.example .env
nano .env

# 3. Iniciar com Docker
docker compose up -d

# 4. Verificar status
docker compose ps
docker compose logs -f

# 5. Acessar
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API: http://localhost:8000/api/
```

### Coletar Dados Iniciais

```bash
# Via Django shell
docker compose exec django-api python manage.py shell

# Coletar uma sessão específica
from data_collector.tasks import collect_session_data
collect_session_data(2025, 1, 'R')  # Bahrain 2025 Race

# Coletar tudo (pode levar horas)
from data_collector.tasks import start_all_data_collection
start_all_data_collection.delay()
```

---

## 📖 Leitura Recomendada

### Para Novos Desenvolvedores

1. **Primeiro:** [Guia de Desenvolvimento](guides/DEVELOPMENT.md) - Setup e padrões
2. **Segundo:** [Modelos](models/README.md) - Entender estrutura de dados
3. **Terceiro:** [API](api/README.md) - Endpoints disponíveis
4. **Quarto:** [Tasks](tasks/README.md) - Como dados são coletados
5. **Quinto:** [Frontend](frontend/README.md) - Componentes e tipos

### Para Melhorias/Correções

1. **Sempre:** [Consultar Documentação FastF1](#-importante-consulta-à-fastf1) ⚠️
2. Identificar área afetada (modelo, API, task, frontend)
3. Ler documentação específica da área
4. Seguir padrões do [Guia de Desenvolvimento](guides/DEVELOPMENT.md)
5. Testar mudanças
6. Atualizar documentação se necessário

---

## ⚠️ IMPORTANTE: Consulta à FastF1

**SEMPRE consulte a [documentação oficial da FastF1](https://docs.fastf1.dev/) antes de:**

- ✅ Implementar nova coleta de dados
- ✅ Corrigir bugs relacionados a dados
- ✅ Investigar problemas de formato de dados
- ✅ Adicionar novos campos aos modelos
- ✅ Modificar processadores de dados

**Links Essenciais:**
- [FastF1 Docs](https://docs.fastf1.dev/) - Documentação geral
- [API Reference](https://docs.fastf1.dev/api.html) - Referência completa da API
- [Examples](https://docs.fastf1.dev/examples/index.html) - Exemplos práticos

**Principais Módulos:**
- [Session](https://docs.fastf1.dev/api.html#session) - Carregar sessões
- [Laps](https://docs.fastf1.dev/api.html#laps) - Dados de voltas
- [Weather](https://docs.fastf1.dev/api.html#weather) - Dados meteorológicos
- [Telemetry](https://docs.fastf1.dev/api.html#telemetry) - Telemetria

---

## 🏗️ Arquitetura do Projeto

```
fastf1-react/
├── backend/                  # Django + Celery
│   ├── api/                 # ViewSets e Serializers
│   ├── core/                # Models
│   ├── data_collector/      # Celery Tasks
│   └── config/              # Settings
│
├── frontend/                # React + TypeScript
│   ├── src/
│   │   ├── components/     # Componentes reutilizáveis
│   │   ├── pages/          # Páginas
│   │   ├── contexts/       # Contextos React
│   │   ├── services/       # API client
│   │   ├── types/          # Tipos TypeScript
│   │   └── styles/         # CSS
│   └── public/
│
├── docs/                    # Documentação
│   ├── models/             # Docs dos modelos
│   ├── api/                # Docs da API
│   ├── tasks/              # Docs das tasks
│   ├── frontend/           # Docs do frontend
│   └── guides/             # Guias
│
├── docker-compose.yml       # Configuração Docker
├── .env                     # Variáveis de ambiente
└── README.md                # README principal
```

---

## 🔗 Navegação Rápida

### Por Componente

| Componente | Documentação | Código |
|------------|--------------|--------|
| **Modelos** | [docs/models/](models/README.md) | `backend/core/models.py` |
| **API Views** | [docs/api/](api/README.md) | `backend/api/views.py` |
| **Serializers** | [docs/api/](api/README.md) | `backend/api/serializers.py` |
| **Celery Tasks** | [docs/tasks/](tasks/README.md) | `backend/data_collector/tasks.py` |
| **Frontend Types** | [docs/frontend/](frontend/README.md) | `frontend/src/types/f1.ts` |
| **Components** | [docs/frontend/](frontend/README.md) | `frontend/src/components/` |
| **Pages** | [docs/frontend/](frontend/README.md) | `frontend/src/pages/` |

### Por Funcionalidade

| Funcionalidade | Onde Consultar |
|----------------|----------------|
| **Adicionar novo modelo** | [Modelos](models/README.md) + [Guia Dev](guides/DEVELOPMENT.md#python-backend) |
| **Criar novo endpoint** | [API](api/README.md) + [Guia Dev](guides/DEVELOPMENT.md#django-views) |
| **Coletar novos dados** | [Tasks](tasks/README.md) + **[FastF1 Docs](https://docs.fastf1.dev/)** |
| **Adicionar componente** | [Frontend](frontend/README.md) + [Guia Dev](guides/DEVELOPMENT.md#typescript-frontend) |
| **Corrigir bug de dados** | **[FastF1 Docs](https://docs.fastf1.dev/)** + [Tasks](tasks/README.md) |
| **Estilizar tema** | [Frontend](frontend/README.md#estilização) |
| **Setup ambiente** | [Guia Dev](guides/DEVELOPMENT.md#setup-do-ambiente) |
| **Fazer deploy** | [Guia Dev](guides/DEVELOPMENT.md#deployment) |

---

## 🐛 Troubleshooting

### Problemas Comuns

| Problema | Solução | Documentação |
|----------|---------|--------------|
| Containers não iniciam | Ver logs, rebuild | [Guia Dev](guides/DEVELOPMENT.md#problema-containers-não-iniciam) |
| Dados não aparecem | Verificar coleta, API, frontend | [Guia Dev](guides/DEVELOPMENT.md#problema-dados-não-aparecem-no-frontend) |
| Tasks não executam | Verificar worker, Redis | [Guia Dev](guides/DEVELOPMENT.md#problema-celery-tasks-não-executam) |
| Frontend não conecta | Verificar CORS, VITE_API_URL | [Guia Dev](guides/DEVELOPMENT.md#problema-frontend-não-conecta-ao-backend) |
| FastF1 Session error | Aguardar ou verificar dados | [Guia Dev](guides/DEVELOPMENT.md#problema-fastf1-session-not-available) + **[FastF1 Docs](https://docs.fastf1.dev/)** |

---

## 📊 Status do Projeto

### Funcionalidades Implementadas

- ✅ Coleta de dados de corridas (2018+)
- ✅ Coleta de classificações (2018+)
- ✅ Coleta de sprints (2021+)
- ✅ Cálculo de standings
- ✅ Pit stops
- ✅ Dados meteorológicos
- ✅ Tempos de volta
- ✅ API REST completa
- ✅ Frontend com temas
- ✅ Histórico de corridas/classificações/sprints
- ✅ Predição de desempenho (pilotos e equipes)

### Em Desenvolvimento

- ⏳ Telemetria detalhada
- ⏳ Estratégias de pneus (2025+)
- ⏳ Gráficos e visualizações avançadas
- ⏳ Comparação de pilotos
- ⏳ API pública com autenticação

---

## 🤝 Contribuindo

1. Ler [Guia de Desenvolvimento](guides/DEVELOPMENT.md)
2. Seguir padrões de código
3. Consultar [documentação FastF1](https://docs.fastf1.dev/) quando trabalhar com dados
4. Adicionar/atualizar tests
5. Atualizar documentação
6. Seguir [Conventional Commits](https://www.conventionalcommits.org/)

**Pull Request Checklist:**
- [ ] Código segue os padrões
- [ ] Tests adicionados/atualizados
- [ ] Documentação atualizada
- [ ] Consultou FastF1 docs (se aplicável)
- [ ] Commits seguem convenção
- [ ] Sem erros de lint

---

## 📝 Changelog

### [Unreleased]

- Documentação completa do projeto
- Guia de desenvolvimento
- Padrões de código

### [1.0.0] - 2025-03-XX

- Release inicial
- Coleta de dados F1
- API REST
- Frontend React
- Sistema de temas

---

## 📞 Suporte

### Dúvidas sobre Código

1. Consultar esta documentação
2. Ver exemplos no código
3. Abrir issue no GitHub

### Dúvidas sobre Dados F1

1. **Sempre consultar [FastF1 Docs](https://docs.fastf1.dev/) primeiro**
2. Ver [exemplos oficiais](https://docs.fastf1.dev/examples/index.html)
3. Consultar [FastF1 GitHub](https://github.com/theOehrly/Fast-F1)

### Bugs e Features

- Abrir issue no GitHub com:
  - Descrição clara
  - Steps to reproduce (se bug)
  - Versões (Python, Node, etc.)
  - Logs relevantes

---

## 📄 Licença

[Adicionar informações de licença]

---

## 🙏 Agradecimentos

- [FastF1](https://github.com/theOehrly/Fast-F1) - Biblioteca incrível para dados F1
- [Formula 1](https://www.formula1.com/) - Fonte dos dados
- Comunidade open source

---

## 📚 Recursos Externos

### Documentação Oficial

- [Django](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [FastF1](https://docs.fastf1.dev/) ⭐
- [React](https://react.dev/)
- [TypeScript](https://www.typescriptlang.org/)
- [Celery](https://docs.celeryq.dev/)
- [Docker](https://docs.docker.com/)

### Tutoriais e Guias

- [FastF1 Examples](https://docs.fastf1.dev/examples/index.html) ⭐
- [Django Best Practices](https://django-best-practices.readthedocs.io/)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)

### Ferramentas

- [Postman](https://www.postman.com/) - Testar API
- [React DevTools](https://react.dev/learn/react-developer-tools)
- [Celery Flower](https://flower.readthedocs.io/)

---

**Última Atualização:** 2025-03-02

**Versão da Documentação:** 1.0.0
