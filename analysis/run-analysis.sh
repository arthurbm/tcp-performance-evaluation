#!/bin/bash

# Script wrapper para executar análise com uv

set -e

# Cores para output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Verificar se estamos no container correto
if [ ! -f /app/pyproject.toml ]; then
    print_info "Este script deve ser executado dentro do container analyzer"
    print_info "Use: docker-compose exec analyzer /app/run-analysis.sh"
    exit 1
fi

# Mudar para o diretório da aplicação
cd /app

# Executar coleta de resultados
print_info "Coletando resultados..."
bash ./collect-results.sh "$@"

# Executar análise e geração de gráficos
print_info "Gerando análises e visualizações..."
uv run python analyze.py "$@"

print_success "Análise completa! Verifique os resultados em /results/"