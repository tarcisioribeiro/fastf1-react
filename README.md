# F1 Dashboard - React + FastF1 API

Dashboard interativo para visualização de dados da Fórmula 1 em tempo real, utilizando React no frontend e Flask + FastF1 no backend.

## Características

- 🏎️ **Classificação de Pilotos**: Visualize o ranking completo do campeonato de pilotos
- 🏁 **Classificação de Construtores**: Acompanhe a classificação das equipes
- 🏆 **Resultados de Corridas**: Veja os resultados das últimas corridas com pódio destacado
- ⏱️ **Resultados de Qualificação**: Confira os tempos de volta e grid de largada
- 📊 **Visualizações Interativas**: Tabelas, cards e componentes visuais premium
- 🔄 **Atualização Automática**: Dados atualizados automaticamente a cada 5 minutos
- 🎨 **Design Moderno**: Interface inspirada no design oficial da F1

## Tecnologias Utilizadas

### Backend
- **Python 3.x**
- **Flask**: Framework web para API REST
- **FastF1**: Biblioteca para acesso aos dados oficiais da F1
- **SQLite**: Cache de dados processados
- **Pandas**: Manipulação de dados

### Frontend
- **React 18**: Biblioteca para interface de usuário
- **TypeScript**: Tipagem estática
- **Vite**: Build tool rápido
- **React Router**: Navegação entre páginas
- **Axios**: Cliente HTTP para consumir a API

## Instalação

### Pré-requisitos

- Python 3.8+
- Node.js 18+
- npm ou yarn

### Instalação Rápida

1. **Instale as dependências Python**:
```bash
pip install -r requirements.txt
```

2. **Instale as dependências do Frontend**:
```bash
cd frontend
npm install
cd ..
```

## Como Usar

### Opção 1: Script Automático (Recomendado)

Execute o script que inicia automaticamente backend e frontend:

```bash
./start.sh
```

O script irá:
- Iniciar a API Flask na porta 5000
- Iniciar o frontend React na porta 5173
- Monitorar ambos os processos
- Gerar logs em `backend.log` e `frontend.log`

Acesse a aplicação em: **http://localhost:5173**

### Opção 2: Iniciar Manualmente

**Terminal 1 - Backend:**
```bash
python3 api.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Opção 3: Apenas a API (Background)

Para manter a API rodando continuamente consumindo dados da F1:

```bash
python3 start_api.py
```

## Estrutura do Projeto

```
fastf1-react/
├── api.py                  # API Flask com endpoints REST
├── f1_data.py             # Gerenciador de dados FastF1
├── database.py            # Cache SQLite
├── start.sh               # Script para iniciar aplicação completa
├── start_api.py           # Script para API em background
├── requirements.txt       # Dependências Python
├── .fastf1_cache/        # Cache de dados da FastF1 (gerado automaticamente)
├── f1_cache.db           # Banco SQLite (gerado automaticamente)
└── frontend/
    ├── src/
    │   ├── components/    # Componentes React reutilizáveis
    │   │   ├── Navbar.tsx
    │   │   ├── Hero.tsx
    │   │   ├── Card.tsx
    │   │   ├── Table.tsx
    │   │   └── Podium.tsx
    │   ├── pages/         # Páginas da aplicação
    │   │   ├── Home.tsx
    │   │   ├── Race.tsx
    │   │   ├── Qualifying.tsx
    │   │   ├── Drivers.tsx
    │   │   └── Constructors.tsx
    │   ├── services/      # Serviços de API
    │   │   └── api.ts
    │   ├── types/         # Definições TypeScript
    │   │   └── f1.ts
    │   └── styles/        # Estilos globais
    │       └── globals.css
    ├── package.json
    └── vite.config.ts
```

## Endpoints da API

A API Flask expõe os seguintes endpoints:

### Health Check
- **GET** `/health`
  - Verifica se a API está respondendo

### Classificações
- **GET** `/api/drivers/standings`
  - Retorna classificação de pilotos do ano atual

- **GET** `/api/constructors/standings`
  - Retorna classificação de construtores do ano atual

### Resultados
- **GET** `/api/races/latest`
  - Retorna dados da última corrida disponível

- **GET** `/api/qualifying/latest`
  - Retorna dados da última qualificação disponível

## Configuração

### Variáveis de Ambiente

#### Frontend
Crie `frontend/.env`:
```env
VITE_API_URL=http://localhost:5000
```

## Cache e Performance

A aplicação utiliza dois níveis de cache:

1. **Cache FastF1** (`.fastf1_cache/`): Armazena dados brutos da API FastF1
2. **Cache SQLite** (`f1_cache.db`): Armazena dados processados com TTL de 24 horas

Isso significa que:
- Na primeira execução, a API vai baixar dados da internet (pode demorar alguns minutos)
- Execuções subsequentes serão muito mais rápidas usando o cache
- Os dados são atualizados automaticamente após 24 horas

## Desenvolvimento

### Frontend

```bash
cd frontend
npm run dev      # Iniciar em modo desenvolvimento
npm run build    # Build para produção
npm run preview  # Preview do build de produção
```

### Backend

```bash
python3 api.py   # Modo desenvolvimento com debug
```

## Notas Importantes

1. **Temporada 2025**: Como a temporada de 2025 ainda não começou, a aplicação mostra dados de 2024
2. **Primeira Execução**: O download inicial de dados pode demorar alguns minutos
3. **Conexão**: Requer conexão com internet para buscar dados da FastF1 API
4. **Cache**: Os arquivos de cache podem ocupar espaço significativo (centenas de MB)
5. **Atualização Automática**: A aplicação atualiza os dados automaticamente a cada 5 minutos

## Solução de Problemas

### API não inicia

```bash
# Verificar se a porta 5000 está em uso
lsof -i :5000

# Instalar dependências novamente
pip install --force-reinstall -r requirements.txt
```

### Frontend não conecta à API

1. Verifique se a API está rodando: `curl http://localhost:5000/health`
2. Verifique as variáveis de ambiente em `frontend/.env`
3. Verifique o console do navegador para erros de CORS

### Dados não carregam

1. Verifique a conexão com internet
2. Verifique os logs: `tail -f backend.log` (ou os logs no terminal)
3. Aguarde alguns minutos na primeira execução (download de dados)
4. Se necessário, limpe o cache: `rm -rf .fastf1_cache/ f1_cache.db`

## Créditos

- **FastF1**: Biblioteca Python para dados da F1 (https://github.com/theOehrly/Fast-F1)
- **Formula 1**: Dados oficiais via FastF1 API
- **Design**: Inspirado no design oficial da Fórmula 1

---

**Desenvolvido com ❤️ para entusiastas da Fórmula 1**
