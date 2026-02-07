#!/usr/bin/env bash
set -euo pipefail

# ==============================================
# FastF1 React - Setup Environment
# ==============================================
# Este script:
#   1. Configura o arquivo .env interativamente
#   2. Sobe a aplicação via Docker Compose
#   3. Configura o hook de pre-commit do Git
# ==============================================

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Diretório do projeto (onde este script está)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${PROJECT_DIR}/.env"
ENV_EXAMPLE="${PROJECT_DIR}/.env.example"

# ----------------------------------------------
# Funções utilitárias
# ----------------------------------------------

print_header() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BOLD}  $1${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${CYAN}--- $1 ---${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

# Gera uma senha segura de N caracteres (padrão: 24)
generate_password() {
    local length="${1:-24}"
    if command -v openssl &>/dev/null; then
        openssl rand -base64 48 | tr -d '/+=\n' | head -c "$length"
    else
        < /dev/urandom tr -dc 'A-Za-z0-9!@#%' | head -c "$length"
    fi
}

# Gera uma secret key para Django
generate_secret_key() {
    if command -v openssl &>/dev/null; then
        openssl rand -base64 64 | tr -d '/+=\n' | head -c 50
    else
        < /dev/urandom tr -dc 'A-Za-z0-9!@#$%^&*' | head -c 50
    fi
}

# Pergunta um valor ao usuário
# Uso: ask "DESCRICAO" "VALOR_PADRAO" [true se senha]
ask() {
    local description="$1"
    local default_value="$2"
    local is_password="${3:-false}"
    local value

    if [ "$is_password" = "true" ]; then
        echo -e "  ${description}"
        echo -e "  ${YELLOW}(Enter = gerar senha segura automaticamente)${NC}"
        read -r -p "  > " value
        if [ -z "$value" ]; then
            value="$(generate_password)"
            echo -e "  ${GREEN}Senha gerada: ${value}${NC}"
        fi
    else
        read -r -p "  ${description} [${default_value}]: " value
        if [ -z "$value" ]; then
            value="$default_value"
        fi
    fi

    echo "$value"
}

# ----------------------------------------------
# ETAPA 1: Configurar .env
# ----------------------------------------------

setup_env() {
    print_header "FastF1 React - Configuracao do Ambiente"

    if [ -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}Arquivo .env ja existe.${NC}"
        read -r -p "  Deseja recriar o .env? (s/N): " recreate
        if [[ ! "$recreate" =~ ^[sS]$ ]]; then
            print_success "Mantendo .env existente."
            return 0
        fi
        cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d%H%M%S)"
        print_warn "Backup salvo em .env.backup.*"
    fi

    if [ ! -f "$ENV_EXAMPLE" ]; then
        print_error ".env.example nao encontrado! Abortando."
        exit 1
    fi

    # --- Portas ---
    print_section "Configuracao de Portas"
    MYSQL_PORT=$(ask "Porta do MySQL" "22111")
    REDIS_PORT=$(ask "Porta do Redis" "22222")
    DJANGO_PORT=$(ask "Porta do Django API" "22333")
    FRONTEND_PORT=$(ask "Porta do Frontend" "22444")

    # --- Banco de Dados ---
    print_section "Configuracao do Banco de Dados"
    MYSQL_DATABASE=$(ask "Nome do banco de dados" "fastf1")
    MYSQL_USER=$(ask "Usuario do banco de dados" "admin")
    echo ""
    echo -e "  ${BOLD}Senha root do MySQL:${NC}"
    MYSQL_ROOT_PASSWORD=$(ask "Senha root do MySQL" "" true)
    echo ""
    echo -e "  ${BOLD}Senha do usuario '${MYSQL_USER}' do MySQL:${NC}"
    MYSQL_PASSWORD=$(ask "Senha do usuario MySQL" "" true)

    # --- Django ---
    print_section "Configuracao do Django"
    DEBUG=$(ask "Modo debug (True/False)" "True")
    echo ""
    echo -e "  ${BOLD}Secret Key do Django:${NC}"
    SECRET_KEY_VALUE=$(ask "SECRET_KEY do Django" "" true)
    # Se gerou automaticamente, usar generate_secret_key para formato adequado
    if [ ${#SECRET_KEY_VALUE} -eq 24 ]; then
        SECRET_KEY_VALUE="$(generate_secret_key)"
        echo -e "  ${GREEN}Secret key gerada: ${SECRET_KEY_VALUE}${NC}"
    fi

    # --- Rede ---
    print_section "Configuracao de Rede"
    ALLOWED_HOSTS=$(ask "Hosts permitidos (comma-separated)" "localhost,127.0.0.1")

    # --- Celery ---
    print_section "Configuracao do Celery"
    CELERY_WORKER_CONCURRENCY=$(ask "Concorrencia dos workers" "2")
    CELERY_MAX_TASKS_PER_CHILD=$(ask "Max tasks por worker child" "100")
    CELERY_PREFETCH_MULTIPLIER=$(ask "Prefetch multiplier" "1")

    # --- Resource Limits ---
    print_section "Limites de Recursos (Docker)"
    echo -e "  ${YELLOW}Pressione Enter para manter os valores padrao recomendados.${NC}"
    echo ""
    REDIS_MEMORY_LIMIT=$(ask "Redis - memoria limite" "256m")
    REDIS_MEMORY_RESERVE=$(ask "Redis - memoria reservada" "128m")
    MYSQL_MEMORY_LIMIT=$(ask "MySQL - memoria limite" "512m")
    MYSQL_MEMORY_RESERVE=$(ask "MySQL - memoria reservada" "256m")
    DJANGO_MEMORY_LIMIT=$(ask "Django API - memoria limite" "512m")
    DJANGO_MEMORY_RESERVE=$(ask "Django API - memoria reservada" "256m")
    CELERY_WORKER_CPU_LIMIT=$(ask "Celery Worker - CPU limite" "1.0")
    CELERY_WORKER_CPU_RESERVE=$(ask "Celery Worker - CPU reservada" "0.25")
    CELERY_WORKER_MEMORY_LIMIT=$(ask "Celery Worker - memoria limite" "512m")
    CELERY_WORKER_MEMORY_RESERVE=$(ask "Celery Worker - memoria reservada" "256m")
    CELERY_BEAT_MEMORY_LIMIT=$(ask "Celery Beat - memoria limite" "256m")
    CELERY_BEAT_MEMORY_RESERVE=$(ask "Celery Beat - memoria reservada" "128m")
    FRONTEND_MEMORY_LIMIT=$(ask "Frontend - memoria limite" "256m")
    FRONTEND_MEMORY_RESERVE=$(ask "Frontend - memoria reservada" "128m")

    # --- Derivar valores automaticos ---
    DATABASE_NAME="$MYSQL_DATABASE"
    DATABASE_USER="$MYSQL_USER"
    DATABASE_PASSWORD="$MYSQL_PASSWORD"
    VITE_API_URL="http://localhost:${DJANGO_PORT}"
    CORS_ALLOWED_ORIGINS="http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}"

    # --- Escrever .env ---
    cat > "$ENV_FILE" <<EOF
# ==============================================
# PORT CONFIGURATION (External Access)
# ==============================================
# Porta do MySQL (padrao: 22111)
MYSQL_PORT=${MYSQL_PORT}

# Porta do Redis (padrao: 22222)
REDIS_PORT=${REDIS_PORT}

# Porta do Backend Django API (padrao: 22333)
DJANGO_PORT=${DJANGO_PORT}

# Porta do Frontend React (padrao: 22444)
FRONTEND_PORT=${FRONTEND_PORT}

# ==============================================
# DATABASE CONFIGURATION
# ==============================================
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
MYSQL_DATABASE=${MYSQL_DATABASE}
MYSQL_USER=${MYSQL_USER}
MYSQL_PASSWORD=${MYSQL_PASSWORD}

# ==============================================
# DJANGO CONFIGURATION
# ==============================================
DEBUG=${DEBUG}
SECRET_KEY=${SECRET_KEY_VALUE}
DATABASE_ENGINE=django.db.backends.mysql
DATABASE_NAME=${DATABASE_NAME}
DATABASE_USER=${DATABASE_USER}
DATABASE_PASSWORD=${DATABASE_PASSWORD}
DATABASE_HOST=mysql
# Porta INTERNA do MySQL na rede Docker (sempre 3306)
DATABASE_PORT=3306

# ==============================================
# REDIS CONFIGURATION
# ==============================================
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# ==============================================
# FRONTEND CONFIGURATION
# ==============================================
NODE_ENV=development
VITE_API_URL=${VITE_API_URL}
VITE_DOCKER_ENV=true

# ==============================================
# PYTHON CONFIGURATION
# ==============================================
PYTHONUNBUFFERED=1

# ==============================================
# NETWORK CONFIGURATION
# ==============================================
# Allowed Hosts (comma-separated) - Add your VPS IP/domain here
ALLOWED_HOSTS=${ALLOWED_HOSTS}

# CORS Configuration (comma-separated) - Add your VPS IP/domain here
CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}

# ==============================================
# CELERY WORKER CONFIGURATION
# ==============================================
CELERY_WORKER_CONCURRENCY=${CELERY_WORKER_CONCURRENCY}
CELERY_MAX_TASKS_PER_CHILD=${CELERY_MAX_TASKS_PER_CHILD}
CELERY_PREFETCH_MULTIPLIER=${CELERY_PREFETCH_MULTIPLIER}

# ==============================================
# RESOURCE LIMITS (Docker Deploy)
# ==============================================
# Redis
REDIS_MEMORY_LIMIT=${REDIS_MEMORY_LIMIT}
REDIS_MEMORY_RESERVE=${REDIS_MEMORY_RESERVE}

# MySQL
MYSQL_MEMORY_LIMIT=${MYSQL_MEMORY_LIMIT}
MYSQL_MEMORY_RESERVE=${MYSQL_MEMORY_RESERVE}

# Django API
DJANGO_MEMORY_LIMIT=${DJANGO_MEMORY_LIMIT}
DJANGO_MEMORY_RESERVE=${DJANGO_MEMORY_RESERVE}

# Celery Workers
CELERY_WORKER_CPU_LIMIT=${CELERY_WORKER_CPU_LIMIT}
CELERY_WORKER_CPU_RESERVE=${CELERY_WORKER_CPU_RESERVE}
CELERY_WORKER_MEMORY_LIMIT=${CELERY_WORKER_MEMORY_LIMIT}
CELERY_WORKER_MEMORY_RESERVE=${CELERY_WORKER_MEMORY_RESERVE}

# Celery Beat
CELERY_BEAT_MEMORY_LIMIT=${CELERY_BEAT_MEMORY_LIMIT}
CELERY_BEAT_MEMORY_RESERVE=${CELERY_BEAT_MEMORY_RESERVE}

# Frontend
FRONTEND_MEMORY_LIMIT=${FRONTEND_MEMORY_LIMIT}
FRONTEND_MEMORY_RESERVE=${FRONTEND_MEMORY_RESERVE}

# ==============================================
# PRODUCTION SETTINGS (for VPS deployment)
# ==============================================
# Uncomment and configure for production
# DOMAIN=your-domain.com
# SSL_ENABLED=true
EOF

    print_success "Arquivo .env criado com sucesso!"
}

# ----------------------------------------------
# ETAPA 2: Subir a aplicação
# ----------------------------------------------

start_application() {
    print_header "Subindo a Aplicacao"

    if ! command -v docker &>/dev/null; then
        print_error "Docker nao encontrado. Instale o Docker primeiro."
        exit 1
    fi

    if ! docker info &>/dev/null 2>&1; then
        print_error "Docker daemon nao esta rodando. Inicie o Docker primeiro."
        exit 1
    fi

    echo -e "  Executando ${BOLD}docker compose up --build -d${NC} ..."
    echo ""

    cd "$PROJECT_DIR"
    docker compose up --build -d

    echo ""
    print_success "Aplicacao iniciada com sucesso!"
    echo ""
    echo -e "  ${BOLD}Servicos disponiveis:${NC}"
    echo -e "    Frontend:   ${GREEN}http://localhost:$(grep '^FRONTEND_PORT=' "$ENV_FILE" | cut -d= -f2)${NC}"
    echo -e "    Backend:    ${GREEN}http://localhost:$(grep '^DJANGO_PORT=' "$ENV_FILE" | cut -d= -f2)${NC}"
    echo -e "    MySQL:      porta $(grep '^MYSQL_PORT=' "$ENV_FILE" | cut -d= -f2)"
    echo -e "    Redis:      porta $(grep '^REDIS_PORT=' "$ENV_FILE" | cut -d= -f2)"
    echo ""
    echo -e "  ${YELLOW}Use 'docker compose logs -f' para acompanhar os logs.${NC}"
}

# ----------------------------------------------
# ETAPA 3: Configurar pre-commit hook
# ----------------------------------------------

setup_precommit() {
    print_header "Configurando Pre-commit Hook"

    local hooks_dir="${PROJECT_DIR}/.git/hooks"

    if [ ! -d "${PROJECT_DIR}/.git" ]; then
        print_warn "Nao e um repositorio Git. Pulando configuracao de pre-commit."
        return 0
    fi

    mkdir -p "$hooks_dir"

    cat > "${hooks_dir}/pre-commit" <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Executando pre-commit hooks...${NC}"

ERRORS=0

# 1. Verificar se arquivos .env estao sendo commitados
ENV_FILES=$(git diff --cached --name-only | grep -E '^\.(env|env\.local|env\.production)$' || true)
if [ -n "$ENV_FILES" ]; then
    echo -e "${RED}[BLOQUEADO]${NC} Arquivos .env detectados no commit:"
    echo "$ENV_FILES" | while read -r f; do echo "  - $f"; done
    echo "  Use 'git reset HEAD <arquivo>' para remover do staging."
    ERRORS=1
fi

# 2. Verificar credenciais hardcoded em arquivos staged
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|ts|tsx|js|jsx|json|yml|yaml)$' || true)
if [ -n "$STAGED_FILES" ]; then
    SECRETS_FOUND=$(echo "$STAGED_FILES" | xargs grep -lnE '(password|secret_key|api_key|token)\s*=\s*["\x27][^"\x27]{8,}' 2>/dev/null || true)
    if [ -n "$SECRETS_FOUND" ]; then
        echo -e "${YELLOW}[AVISO]${NC} Possiveis credenciais encontradas em:"
        echo "$SECRETS_FOUND" | while read -r f; do echo "  - $f"; done
        echo "  Verifique se nao esta commitando senhas reais."
    fi
fi

# 3. Verificar syntax Python (se houver arquivos .py no staging)
PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)
if [ -n "$PY_FILES" ]; then
    echo -e "Verificando syntax Python..."
    for file in $PY_FILES; do
        if [ -f "$file" ]; then
            if ! python3 -c "import py_compile; py_compile.compile('$file', doraise=True)" 2>/dev/null; then
                echo -e "${RED}[ERRO]${NC} Erro de syntax em: $file"
                ERRORS=1
            fi
        fi
    done
fi

# 4. Verificar se ha conflitos de merge nao resolvidos
CONFLICT_FILES=$(git diff --cached --name-only | xargs grep -l '<<<<<<< ' 2>/dev/null || true)
if [ -n "$CONFLICT_FILES" ]; then
    echo -e "${RED}[BLOQUEADO]${NC} Conflitos de merge nao resolvidos em:"
    echo "$CONFLICT_FILES" | while read -r f; do echo "  - $f"; done
    ERRORS=1
fi

if [ "$ERRORS" -eq 1 ]; then
    echo ""
    echo -e "${RED}Commit bloqueado. Corrija os problemas acima.${NC}"
    exit 1
fi

echo -e "${GREEN}Pre-commit hooks concluidos com sucesso!${NC}"
exit 0
HOOK

    chmod +x "${hooks_dir}/pre-commit"
    print_success "Pre-commit hook configurado em .git/hooks/pre-commit"
}

# ----------------------------------------------
# Execução principal
# ----------------------------------------------

main() {
    print_header "FastF1 React - Setup Completo"
    echo -e "  Este script ira configurar o ambiente de desenvolvimento."
    echo -e "  Serao realizadas 3 etapas:"
    echo -e "    1. Configurar variaveis de ambiente (.env)"
    echo -e "    2. Subir a aplicacao via Docker Compose"
    echo -e "    3. Configurar hook de pre-commit do Git"
    echo ""
    read -r -p "  Pressione Enter para continuar ou Ctrl+C para cancelar... "

    # Etapa 1
    setup_env

    # Etapa 2
    start_application

    # Etapa 3
    setup_precommit

    print_header "Setup Concluido!"
    echo -e "  ${GREEN}Tudo pronto! A aplicacao esta rodando.${NC}"
    echo ""
}

main "$@"
