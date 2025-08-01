#!/bin/bash

# Script simplificado para executar testes da Atividade 2

set -e

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Executando Testes Simplificados da Atividade 2 ===${NC}"

SERVER_IP="10.5.0.10"
RESULTS_DIR="/results/atv2/results/raw"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$RESULTS_DIR"

# Teste 1: Baseline
echo -e "\n${BLUE}Cenário 1: Baseline${NC}"
for i in 1 2 3; do
    echo "Repetição $i/3..."
    iperf3 -c $SERVER_IP -t 10 -J > "${RESULTS_DIR}/${TIMESTAMP}_baseline_rep${i}.json" 2>&1
    sleep 2
done

# Teste 2: Window 256K
echo -e "\n${BLUE}Cenário 2: Window 256K${NC}"
for i in 1 2 3; do
    echo "Repetição $i/3..."
    iperf3 -c $SERVER_IP -t 10 -w 256K -J > "${RESULTS_DIR}/${TIMESTAMP}_window256k_rep${i}.json" 2>&1
    sleep 2
done

# Teste 3: 4 Streams paralelos
echo -e "\n${BLUE}Cenário 3: 4 Streams Paralelos${NC}"
for i in 1 2 3; do
    echo "Repetição $i/3..."
    iperf3 -c $SERVER_IP -t 10 -P 4 -J > "${RESULTS_DIR}/${TIMESTAMP}_streams4_rep${i}.json" 2>&1
    sleep 2
done

# Teste 4: Latência 50ms
echo -e "\n${BLUE}Cenário 4: Latência 50ms${NC}"
tc qdisc add dev eth0 root netem delay 50ms 2>/dev/null || true
for i in 1 2 3; do
    echo "Repetição $i/3..."
    iperf3 -c $SERVER_IP -t 10 -J > "${RESULTS_DIR}/${TIMESTAMP}_latency50ms_rep${i}.json" 2>&1
    sleep 2
done
tc qdisc del dev eth0 root 2>/dev/null || true

# Teste 5: Banda limitada 10Mbps
echo -e "\n${BLUE}Cenário 5: Banda 10Mbps${NC}"
tc qdisc add dev eth0 root tbf rate 10mbit burst 32kbit latency 400ms 2>/dev/null || true
for i in 1 2 3; do
    echo "Repetição $i/3..."
    iperf3 -c $SERVER_IP -t 10 -J > "${RESULTS_DIR}/${TIMESTAMP}_bandwidth10mbps_rep${i}.json" 2>&1
    sleep 2
done
tc qdisc del dev eth0 root 2>/dev/null || true

# Teste 6: Perda de pacotes 0.5%
echo -e "\n${BLUE}Cenário 6: Perda 0.5%${NC}"
tc qdisc add dev eth0 root netem loss 0.5% 2>/dev/null || true
for i in 1 2 3; do
    echo "Repetição $i/3..."
    iperf3 -c $SERVER_IP -t 10 -J > "${RESULTS_DIR}/${TIMESTAMP}_loss0.5_rep${i}.json" 2>&1
    sleep 2
done
tc qdisc del dev eth0 root 2>/dev/null || true

echo -e "\n${GREEN}=== Testes Concluídos ===${NC}"
echo "Resultados salvos em: $RESULTS_DIR"
echo "Timestamp: $TIMESTAMP"

# Contar arquivos
num_files=$(ls -1 "${RESULTS_DIR}/${TIMESTAMP}_*.json" 2>/dev/null | wc -l)
echo "Total de arquivos gerados: $num_files"