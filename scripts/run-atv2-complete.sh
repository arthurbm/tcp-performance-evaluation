#!/bin/bash

# Script completo para executar testes da Atividade 2 com todos os algoritmos

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}=== Executando Testes Completos da Atividade 2 ===${NC}"

SERVER_IP="10.5.0.10"
RESULTS_DIR="/results/atv2/results/raw"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_DURATION=20  # Reduzido para 20s para agilizar

mkdir -p "$RESULTS_DIR"

# Salvar configurações
echo -e "\n${BLUE}Salvando configurações do sistema...${NC}"
{
    echo "=== Configurações do Sistema - Atividade 2 ==="
    echo "Data: $(date)"
    echo "Timestamp: $TIMESTAMP"
    echo ""
    echo "=== Algoritmos TCP Disponíveis ==="
    sysctl net.ipv4.tcp_available_congestion_control
    echo ""
    echo "=== Algoritmo Atual ==="
    sysctl net.ipv4.tcp_congestion_control
} > "${RESULTS_DIR}/${TIMESTAMP}_system_config.txt"

# Salvar algoritmo original
ORIGINAL_CC=$(sysctl -n net.ipv4.tcp_congestion_control)

# Função para executar teste
run_test() {
    local name="$1"
    local params="$2"
    local rep="$3"
    
    echo -e "${YELLOW}  Repetição $rep/3...${NC}"
    iperf3 -c $SERVER_IP -t $TEST_DURATION -J $params > "${RESULTS_DIR}/${TIMESTAMP}_${name}_rep${rep}.json" 2>&1 || true
    sleep 3
}

# Função para limpar tc
cleanup_tc() {
    tc qdisc del dev eth0 root 2>/dev/null || true
}

# 1. CENÁRIO 1: Baseline (CUBIC)
echo -e "\n${PURPLE}=== Cenário 1: Baseline (CUBIC) ===${NC}"
sysctl -w net.ipv4.tcp_congestion_control=cubic >/dev/null 2>&1
for i in 1 2 3; do
    run_test "scenario_1_baseline" "" $i
done

# 2. CENÁRIO 2: High Performance (CUBIC com janela grande)
echo -e "\n${PURPLE}=== Cenário 2: High Performance (CUBIC, 512K, 8 streams) ===${NC}"
for i in 1 2 3; do
    run_test "scenario_2_high_performance" "-w 512K -P 8" $i || run_test "scenario_2_high_performance" "-w 256K -P 8" $i
done

# 3. CENÁRIO 3: Rede Congestionada (Vegas)
echo -e "\n${PURPLE}=== Cenário 3: Rede Congestionada (Vegas) ===${NC}"
if sysctl -w net.ipv4.tcp_congestion_control=vegas >/dev/null 2>&1; then
    cleanup_tc
    tc qdisc add dev eth0 root handle 1: netem delay 50ms
    tc qdisc add dev eth0 parent 1: handle 2: tbf rate 10mbit burst 32kbit latency 400ms
    for i in 1 2 3; do
        run_test "scenario_3_congested_vegas" "-w 128K -P 4" $i
    done
    cleanup_tc
else
    echo -e "${YELLOW}Vegas não disponível, usando Westwood${NC}"
    sysctl -w net.ipv4.tcp_congestion_control=westwood >/dev/null 2>&1
    cleanup_tc
    tc qdisc add dev eth0 root handle 1: netem delay 50ms
    tc qdisc add dev eth0 parent 1: handle 2: tbf rate 10mbit burst 32kbit latency 400ms
    for i in 1 2 3; do
        run_test "scenario_3_congested_westwood" "-w 128K -P 4" $i
    done
    cleanup_tc
fi

# 4. CENÁRIO 4: Rede com Perdas (Reno)
echo -e "\n${PURPLE}=== Cenário 4: Rede com Perdas (Reno) ===${NC}"
sysctl -w net.ipv4.tcp_congestion_control=reno >/dev/null 2>&1
cleanup_tc
tc qdisc add dev eth0 root netem delay 30ms loss 0.5%
for i in 1 2 3; do
    run_test "scenario_4_lossy_reno" "-w 256K -P 2" $i
done
cleanup_tc

# 5. CENÁRIO 5: Datacenter Legacy (CUBIC)
echo -e "\n${PURPLE}=== Cenário 5: Datacenter Legacy (CUBIC) ===${NC}"
sysctl -w net.ipv4.tcp_congestion_control=cubic >/dev/null 2>&1
cleanup_tc
tc qdisc add dev eth0 root handle 1: netem delay 5ms
tc qdisc add dev eth0 parent 1: handle 2: tbf rate 100mbit burst 32kbit latency 400ms
for i in 1 2 3; do
    run_test "scenario_5_legacy_cubic" "-w 64K" $i
done
cleanup_tc

# 6. CENÁRIO 6: WAN Intercontinental (BBR)
echo -e "\n${PURPLE}=== Cenário 6: WAN Intercontinental (BBR) ===${NC}"
if sysctl -w net.ipv4.tcp_congestion_control=bbr >/dev/null 2>&1; then
    cleanup_tc
    tc qdisc add dev eth0 root netem delay 100ms loss 0.1%
    for i in 1 2 3; do
        run_test "scenario_6_wan_bbr" "-w 256K -P 4" $i
    done
    cleanup_tc
else
    echo -e "${YELLOW}BBR não disponível, usando Illinois${NC}"
    sysctl -w net.ipv4.tcp_congestion_control=illinois >/dev/null 2>&1
    cleanup_tc
    tc qdisc add dev eth0 root netem delay 100ms loss 0.1%
    for i in 1 2 3; do
        run_test "scenario_6_wan_illinois" "-w 256K -P 4" $i
    done
    cleanup_tc
fi

# TESTES EXTRAS: Comparação direta de algoritmos
echo -e "\n${PURPLE}=== Testes Extras: Comparação de Algoritmos ===${NC}"

# Extra 1: H-TCP em alta latência
if sysctl -w net.ipv4.tcp_congestion_control=htcp >/dev/null 2>&1; then
    echo -e "\n${BLUE}Extra: H-TCP com alta latência${NC}"
    cleanup_tc
    tc qdisc add dev eth0 root netem delay 75ms
    for i in 1 2 3; do
        run_test "extra_htcp_highlatency" "-w 256K" $i
    done
    cleanup_tc
fi

# Extra 2: Westwood com perda
if sysctl -w net.ipv4.tcp_congestion_control=westwood >/dev/null 2>&1; then
    echo -e "\n${BLUE}Extra: Westwood com perda de pacotes${NC}"
    cleanup_tc
    tc qdisc add dev eth0 root netem loss 0.3%
    for i in 1 2 3; do
        run_test "extra_westwood_loss" "-w 256K" $i
    done
    cleanup_tc
fi

# Restaurar configurações originais
echo -e "\n${BLUE}Restaurando configurações originais...${NC}"
sysctl -w net.ipv4.tcp_congestion_control=$ORIGINAL_CC >/dev/null 2>&1
cleanup_tc

# Contar resultados
num_files=$(ls -1 "${RESULTS_DIR}/${TIMESTAMP}_*.json" 2>/dev/null | wc -l)

echo -e "\n${GREEN}=== Testes Concluídos ===${NC}"
echo "Timestamp: $TIMESTAMP"
echo "Total de arquivos gerados: $num_files"
echo "Resultados em: $RESULTS_DIR"

# Criar resumo
{
    echo "=== Resumo da Execução - Atividade 2 Completa ==="
    echo "Timestamp: $TIMESTAMP"
    echo "Total de testes: $num_files"
    echo ""
    echo "Cenários executados:"
    echo "1. Baseline (CUBIC)"
    echo "2. High Performance (CUBIC + otimizações)"
    echo "3. Rede Congestionada (Vegas/Westwood)"
    echo "4. Rede com Perdas (Reno)"
    echo "5. Datacenter Legacy (CUBIC)"
    echo "6. WAN Intercontinental (BBR/Illinois)"
    echo ""
    echo "Algoritmos testados:"
    sysctl net.ipv4.tcp_available_congestion_control
} > "${RESULTS_DIR}/${TIMESTAMP}_execution_summary.txt"

echo -e "\n${GREEN}Execute analyze-atv2.py para processar os resultados${NC}"