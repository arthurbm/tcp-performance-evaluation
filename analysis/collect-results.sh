#!/bin/bash

# Script para coletar e organizar resultados dos testes
# Converte JSONs do iperf3 para formato tabular

set -e

# Configurações
RAW_DIR="/results/raw"
PROCESSED_DIR="/results/processed"
TIMESTAMP=${1:-$(ls -t $RAW_DIR | head -1 | cut -d'_' -f1-2)}

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Criar diretório de saída
mkdir -p "$PROCESSED_DIR"

# Arquivo de saída CSV
OUTPUT_CSV="$PROCESSED_DIR/${TIMESTAMP}_results.csv"

# Cabeçalho do CSV
echo "test_name,repetition,throughput_mbps,retransmits,cpu_sender,cpu_receiver,rtt_ms,window_size,streams" > "$OUTPUT_CSV"

# Função para extrair dados de um arquivo JSON do iperf3
extract_data() {
    local json_file="$1"
    local test_name=$(basename "$json_file" | sed -E 's/^[0-9]+_[0-9]+_(.*)_rep[0-9]+\.json$/\1/')
    local repetition=$(basename "$json_file" | sed -E 's/.*_rep([0-9]+)\.json$/\1/')
    
    # Verificar se o arquivo existe e não está vazio
    if [ ! -s "$json_file" ]; then
        print_info "Arquivo vazio ou não encontrado: $json_file"
        return
    fi
    
    # Extrair métricas usando Python com uv (mais confiável para JSON)
    uv run python - <<EOF
import json
import sys

try:
    with open('$json_file', 'r') as f:
        data = json.load(f)
    
    # Extrair métricas principais
    if 'end' in data:
        end_data = data['end']
        
        # Throughput em Mbps
        throughput = end_data.get('sum_sent', {}).get('bits_per_second', 0) / 1e6
        
        # Retransmissões
        retransmits = end_data.get('sum_sent', {}).get('retransmits', 0)
        
        # CPU usage
        cpu_sender = end_data.get('cpu_utilization_percent', {}).get('host_total', 0)
        cpu_receiver = end_data.get('cpu_utilization_percent', {}).get('remote_total', 0)
        
        # RTT (se disponível)
        rtt = end_data.get('streams', [{}])[0].get('sender', {}).get('mean_rtt', 0) / 1000  # converter para ms
        
        # Window size
        window_size = end_data.get('streams', [{}])[0].get('sender', {}).get('socket', 0)
        
        # Número de streams
        streams = len(end_data.get('streams', []))
        
        # Imprimir linha CSV
        print(f"$test_name,$repetition,{throughput:.2f},{retransmits},{cpu_sender:.2f},{cpu_receiver:.2f},{rtt:.2f},{window_size},{streams}")
    else:
        print(f"$test_name,$repetition,0,0,0,0,0,0,0")
        
except Exception as e:
    print(f"$test_name,$repetition,ERROR,ERROR,ERROR,ERROR,ERROR,ERROR,ERROR", file=sys.stderr)
    print(f"Erro ao processar {json_file}: {str(e)}", file=sys.stderr)
EOF
}

# Processar todos os arquivos JSON
print_info "Processando arquivos do timestamp: $TIMESTAMP"

json_files=$(find "$RAW_DIR" -name "${TIMESTAMP}_*.json" | sort)
total_files=$(echo "$json_files" | wc -l)
processed=0

for json_file in $json_files; do
    if [ -f "$json_file" ]; then
        extract_data "$json_file" >> "$OUTPUT_CSV"
        ((processed++))
        echo -ne "\rProcessando: $processed/$total_files"
    fi
done

echo ""
print_success "Processamento concluído!"

# Criar resumo estatístico
SUMMARY_FILE="$PROCESSED_DIR/${TIMESTAMP}_summary.txt"

print_info "Gerando resumo estatístico..."

uv run python - <<EOF
import pandas as pd
import numpy as np

# Ler CSV
df = pd.read_csv('$OUTPUT_CSV')

# Remover linhas com erro
df = df[df['throughput_mbps'] != 'ERROR']
df['throughput_mbps'] = pd.to_numeric(df['throughput_mbps'])

# Agrupar por teste e calcular estatísticas
summary = df.groupby('test_name').agg({
    'throughput_mbps': ['mean', 'std', 'min', 'max'],
    'retransmits': ['mean', 'sum'],
    'cpu_sender': 'mean',
    'cpu_receiver': 'mean',
    'rtt_ms': 'mean'
}).round(2)

# Salvar resumo
with open('$SUMMARY_FILE', 'w') as f:
    f.write("=== RESUMO DOS TESTES DE DESEMPENHO TCP ===\n")
    f.write(f"Timestamp: $TIMESTAMP\n")
    f.write(f"Total de testes: {len(df)}\n\n")
    f.write(str(summary))
    
    # Identificar melhor configuração
    f.write("\n\n=== MELHOR CONFIGURAÇÃO ===\n")
    best_idx = df.groupby('test_name')['throughput_mbps'].mean().idxmax()
    best_throughput = df.groupby('test_name')['throughput_mbps'].mean().max()
    f.write(f"Teste: {best_idx}\n")
    f.write(f"Throughput médio: {best_throughput:.2f} Mbps\n")

print("Resumo salvo em: $SUMMARY_FILE")
EOF

# Criar tabela formatada para o relatório
TABLE_FILE="$PROCESSED_DIR/${TIMESTAMP}_table.md"

print_info "Gerando tabela Markdown..."

uv run python - <<EOF
import pandas as pd

# Ler CSV
df = pd.read_csv('$OUTPUT_CSV')

# Remover linhas com erro
df = df[df['throughput_mbps'] != 'ERROR']
df['throughput_mbps'] = pd.to_numeric(df['throughput_mbps'])

# Criar tabela resumida
summary = df.groupby('test_name').agg({
    'throughput_mbps': 'mean',
    'retransmits': 'mean',
    'cpu_sender': 'mean',
    'rtt_ms': 'mean'
}).round(2)

# Resetar índice para ter test_name como coluna
summary = summary.reset_index()

# Renomear colunas para português
summary.columns = ['Cenário', 'Throughput (Mbps)', 'Retransmissões', 'CPU Sender (%)', 'RTT (ms)']

# Salvar como Markdown
with open('$TABLE_FILE', 'w') as f:
    f.write("## Tabela de Resultados dos Testes\n\n")
    f.write(summary.to_markdown(index=False))
    f.write("\n")

print("Tabela salva em: $TABLE_FILE")
EOF

print_success "Coleta de resultados concluída!"
print_info "Arquivos gerados:"
print_info "  - CSV: $OUTPUT_CSV"
print_info "  - Resumo: $SUMMARY_FILE"
print_info "  - Tabela: $TABLE_FILE"