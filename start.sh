#!/bin/bash

# Script para iniciar a aplicação completa (Backend + Frontend)

echo "🏎️  Iniciando F1 Dashboard..."
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 não encontrado. Por favor, instale Python 3.${NC}"
    exit 1
fi

# Verificar se Node.js está instalado
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js não encontrado. Por favor, instale Node.js.${NC}"
    exit 1
fi

# Função para cleanup ao sair
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Encerrando aplicação...${NC}"

    # Matar processos do backend e frontend
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi

    echo -e "${GREEN}✅ Aplicação encerrada com sucesso!${NC}"
    exit 0
}

# Registrar handler para Ctrl+C
trap cleanup SIGINT SIGTERM

# Verificar se dependências Python estão instaladas
echo "📦 Verificando dependências Python..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Dependências Python não encontradas. Instalando...${NC}"
    pip install -r requirements.txt
fi

# Iniciar Backend (API Flask)
echo ""
echo -e "${GREEN}🚀 Iniciando Backend (API Flask)...${NC}"
python3 api.py > backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend iniciado (PID: $BACKEND_PID)${NC}"
echo "   API disponível em: http://localhost:5000"

# Aguardar backend iniciar
echo "   Aguardando backend iniciar..."
sleep 3

# Verificar se o backend está rodando
if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo -e "${RED}❌ Erro ao iniciar backend. Verifique backend.log${NC}"
    exit 1
fi

# Verificar se dependências do frontend estão instaladas
echo ""
echo "📦 Verificando dependências do Frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  Dependências do frontend não encontradas. Instalando...${NC}"
    npm install
fi

# Iniciar Frontend (React + Vite)
echo ""
echo -e "${GREEN}🚀 Iniciando Frontend (React + Vite)...${NC}"
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}✅ Frontend iniciado (PID: $FRONTEND_PID)${NC}"
echo "   Frontend disponível em: http://localhost:5173"

# Aguardar frontend iniciar
echo "   Aguardando frontend iniciar..."
sleep 3

# Verificar se o frontend está rodando
if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo -e "${RED}❌ Erro ao iniciar frontend. Verifique frontend.log${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Aplicação iniciada com sucesso!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🏎️  F1 Dashboard está rodando!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  📊 Frontend: http://localhost:5173"
echo "  🔌 Backend:  http://localhost:5000"
echo ""
echo "  Logs:"
echo "    Backend:  tail -f backend.log"
echo "    Frontend: tail -f frontend.log"
echo ""
echo "  Pressione Ctrl+C para encerrar a aplicação"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Manter script rodando e monitorar processos
while true; do
    # Verificar se backend ainda está rodando
    if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${RED}❌ Backend parou de responder!${NC}"
        cleanup
    fi

    # Verificar se frontend ainda está rodando
    if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${RED}❌ Frontend parou de responder!${NC}"
        cleanup
    fi

    sleep 2
done
