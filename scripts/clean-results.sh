#!/bin/bash

# Script para limpar resultados de testes anteriores
# Mantém a estrutura de diretórios mas remove os dados

echo "Limpando resultados anteriores..."

# Limpar arquivos de resultado
rm -f results/raw/*.json 2>/dev/null
rm -f results/processed/*.csv 2>/dev/null
rm -f results/plots/*.png 2>/dev/null
rm -f results/*.log 2>/dev/null

# Criar arquivos .gitkeep para manter diretórios no git
touch results/raw/.gitkeep
touch results/processed/.gitkeep
touch results/plots/.gitkeep

echo "Limpeza concluída!"
echo "Estrutura de diretórios mantida."