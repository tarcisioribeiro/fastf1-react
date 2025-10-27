#!/bin/bash

# =====================================================
# FastF1 React - Setup Interativo
# =====================================================
# Este script configura o ambiente e cria o arquivo .env
# para facilitar o deploy da aplicação
# =====================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir cabeçalho
print_header() {
    echo -e "${BLUE}"
    echo "=========================================="
    echo "  FastF1 React - Configuração Inicial"
    echo "=========================================="
    echo -e "${NC}"
}

# Função para imprimir informação
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Função para imprimir sucesso
print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

# Função para imprimir aviso
print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Função para imprimir erro
print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Função para ler input com valor padrão
read_with_default() {
    local prompt="$1"
    local default="$2"
    local value

    read -p "$(echo -e ${BLUE}${prompt}${NC} [${GREEN}${default}${NC}]: )" value
    echo "${value:-$default}"
}

# Função para validar porta
validate_port() {
    local port=$1
    if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
        return 1
    fi
    return 0
}

# Verificar se Docker está instalado
check_docker() {
    print_info "Verificando instalação do Docker..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker não está instalado!"
        print_info "Instale o Docker em: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker encontrado: $(docker --version)"

    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose não está instalado!"
        print_info "Instale o Docker Compose em: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose encontrado"
}

# Início do script
clear
print_header

check_docker

echo ""
print_info "Este script irá configurar as variáveis de ambiente para sua aplicação."
print_info "Pressione ENTER para usar o valor padrão (mostrado em verde)."
echo ""

# =====================================================
# CONFIGURAÇÃO DE PORTAS
# =====================================================
echo -e "${YELLOW}=== CONFIGURAÇÃO DE PORTAS ===${NC}"
echo ""

while true; do
    MYSQL_PORT=$(read_with_default "Porta do MySQL" "3306")
    if validate_port "$MYSQL_PORT"; then
        break
    else
        print_error "Porta inválida! Use um número entre 1 e 65535."
    fi
done

while true; do
    REDIS_PORT=$(read_with_default "Porta do Redis" "6379")
    if validate_port "$REDIS_PORT"; then
        break
    else
        print_error "Porta inválida! Use um número entre 1 e 65535."
    fi
done

while true; do
    DJANGO_PORT=$(read_with_default "Porta do Backend (Django API)" "8000")
    if validate_port "$DJANGO_PORT"; then
        break
    else
        print_error "Porta inválida! Use um número entre 1 e 65535."
    fi
done

while true; do
    FRONTEND_PORT=$(read_with_default "Porta do Frontend (React)" "3000")
    if validate_port "$FRONTEND_PORT"; then
        break
    else
        print_error "Porta inválida! Use um número entre 1 e 65535."
    fi
done

echo ""
# =====================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# =====================================================
echo -e "${YELLOW}=== CONFIGURAÇÃO DO BANCO DE DADOS ===${NC}"
echo ""

MYSQL_ROOT_PASSWORD=$(read_with_default "Senha do root do MySQL" "root_password")
MYSQL_DATABASE=$(read_with_default "Nome do banco de dados" "f1_database")
MYSQL_USER=$(read_with_default "Usuário do banco de dados" "f1_user")
MYSQL_PASSWORD=$(read_with_default "Senha do usuário do banco" "f1_password")

echo ""
# =====================================================
# CONFIGURAÇÃO DO DJANGO
# =====================================================
echo -e "${YELLOW}=== CONFIGURAÇÃO DO DJANGO ===${NC}"
echo ""

DEBUG=$(read_with_default "Modo DEBUG (True/False)" "True")

# Gerar SECRET_KEY aleatória sem depender do Django
# Usa openssl ou /dev/urandom para gerar uma chave segura
if command -v openssl &> /dev/null; then
    SECRET_KEY=$(openssl rand -base64 50 | tr -d '\n')
    print_info "SECRET_KEY gerada automaticamente com openssl"
else
    # Fallback para /dev/urandom
    SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9!@#$%^&*(-_=+)' | fold -w 50 | head -n 1)
    print_info "SECRET_KEY gerada automaticamente com /dev/urandom"
fi

echo ""
# =====================================================
# CONFIGURAÇÃO DE REDE (VPS)
# =====================================================
echo -e "${YELLOW}=== CONFIGURAÇÃO DE REDE (para VPS) ===${NC}"
echo ""

print_info "Se você está instalando em uma VPS, adicione o IP/domínio da VPS."
print_info "Exemplo: 192.168.1.100 ou meusite.com"
print_info "Para desenvolvimento local, use apenas 'localhost,127.0.0.1'"
echo ""

ALLOWED_HOSTS=$(read_with_default "ALLOWED_HOSTS (separados por vírgula)" "localhost,127.0.0.1")

# Construir CORS_ALLOWED_ORIGINS baseado nas portas configuradas
DEFAULT_CORS="http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}"
CORS_ALLOWED_ORIGINS=$(read_with_default "CORS_ALLOWED_ORIGINS (separados por vírgula)" "$DEFAULT_CORS")

# Construir VITE_API_URL
DEFAULT_API_URL="http://localhost:${DJANGO_PORT}"
VITE_API_URL=$(read_with_default "URL da API para o Frontend" "$DEFAULT_API_URL")

echo ""
# =====================================================
# CRIAR ARQUIVO .env
# =====================================================
print_info "Criando arquivo .env..."

cat > .env << EOF
# ==============================================
# PORT CONFIGURATION (External Access)
# ==============================================
# Gerado automaticamente pelo setup.sh
# Data: $(date)
# ==============================================

# Porta do MySQL (padrão: 3306)
MYSQL_PORT=${MYSQL_PORT}

# Porta do Redis (padrão: 6379)
REDIS_PORT=${REDIS_PORT}

# Porta do Backend Django API (padrão: 8000)
DJANGO_PORT=${DJANGO_PORT}

# Porta do Frontend React (padrão: 3000)
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
SECRET_KEY=${SECRET_KEY}
DATABASE_ENGINE=django.db.backends.mysql
DATABASE_NAME=${MYSQL_DATABASE}
DATABASE_USER=${MYSQL_USER}
DATABASE_PASSWORD=${MYSQL_PASSWORD}
DATABASE_HOST=mysql
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

# ==============================================
# NETWORK CONFIGURATION
# ==============================================
# Allowed Hosts (comma-separated)
ALLOWED_HOSTS=${ALLOWED_HOSTS}

# CORS Configuration (comma-separated)
CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}
EOF

print_success "Arquivo .env criado com sucesso!"

# Criar .env para o frontend também
print_info "Criando arquivo .env para o frontend..."
cat > frontend/.env << EOF
VITE_API_URL=${VITE_API_URL}
EOF

print_success "Arquivo frontend/.env criado com sucesso!"

echo ""
# =====================================================
# RESUMO DA CONFIGURAÇÃO
# =====================================================
echo -e "${GREEN}=========================================="
echo "  CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!"
echo "==========================================${NC}"
echo ""
echo -e "${BLUE}Resumo das portas configuradas:${NC}"
echo -e "  • MySQL:    ${GREEN}${MYSQL_PORT}${NC}"
echo -e "  • Redis:    ${GREEN}${REDIS_PORT}${NC}"
echo -e "  • Backend:  ${GREEN}${DJANGO_PORT}${NC}"
echo -e "  • Frontend: ${GREEN}${FRONTEND_PORT}${NC}"
echo ""

# =====================================================
# PERGUNTAR SE DESEJA FAZER BUILD
# =====================================================
echo -e "${YELLOW}Deseja fazer o build e subir os containers agora?${NC}"
read -p "$(echo -e ${BLUE}Digite [S/n]:${NC} )" -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]] || [[ -z $REPLY ]]; then
    print_info "Iniciando build dos containers..."
    echo ""

    # Parar containers existentes
    print_info "Parando containers existentes (se houver)..."
    docker compose down 2>/dev/null || true

    # Limpar sistema Docker
    print_info "Limpando sistema Docker..."
    docker system prune -f

    # Fazer build
    print_info "Fazendo build das imagens..."
    docker compose build

    # Subir containers
    print_info "Subindo containers..."
    docker compose up -d

    echo ""
    print_success "Containers iniciados com sucesso!"
    echo ""

    # Aguardar alguns segundos para os serviços iniciarem
    print_info "Aguardando serviços iniciarem (15 segundos)..."
    sleep 15

    # Mostrar status
    print_info "Status dos containers:"
    docker compose ps

    echo ""
    print_success "Aplicação disponível em:"
    echo -e "  • Frontend: ${GREEN}http://localhost:${FRONTEND_PORT}${NC}"
    echo -e "  • Backend API: ${GREEN}http://localhost:${DJANGO_PORT}${NC}"
    echo ""

    print_info "Para ver os logs, execute:"
    echo -e "  ${YELLOW}docker compose logs -f${NC}"
    echo ""

    print_info "Para parar os containers, execute:"
    echo -e "  ${YELLOW}docker compose down${NC}"
    echo ""
else
    print_info "Build cancelado pelo usuário."
    echo ""
    print_info "Para fazer o build manualmente, execute:"
    echo -e "  ${YELLOW}docker compose up --build -d${NC}"
    echo ""
fi

print_success "Setup concluído!"
