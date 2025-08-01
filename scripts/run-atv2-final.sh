#!/bin/bash

# Script final para executar testes da Atividade 2

set +e  # Continuar mesmo com erros

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}=== Testes Finais - Atividade 2 ===${NC}"

SERVER_IP="10.5.0.10"
RESULTS_DIR="/results/atv2/results/raw"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$RESULTS_DIR"

# Função para executar teste
run_test() {
    local name="$1"
    local params="$2"
    local rep="$3"
    echo "  Rep $rep..."
    
    # Tentar com parâmetros originais
    if ! iperf3 -c $SERVER_IP -t 15 -J $params > "${RESULTS_DIR}/${TIMESTAMP}_${name}_rep${rep}.json" 2>&1; then
        # Se falhar, tentar sem janela específica
        echo "    Retry sem janela..."
        iperf3 -c $SERVER_IP -t 15 -J -P ${params##*-P } > "${RESULTS_DIR}/${TIMESTAMP}_${name}_rep${rep}.json" 2>&1
    fi
    sleep 2
}

# Limpar tc
tc qdisc del dev eth0 root 2>/dev/null || true

echo -e "\n${PURPLE}1. Baseline (CUBIC)${NC}"
sysctl -w net.ipv4.tcp_congestion_control=cubic >/dev/null 2>&1
for i in 1 2 3; do
    run_test "baseline_cubic" "" $i
done

echo -e "\n${PURPLE}2. Vegas com banda limitada${NC}"
sysctl -w net.ipv4.tcp_congestion_control=vegas >/dev/null 2>&1
tc qdisc add dev eth0 root tbf rate 10mbit burst 32kbit latency 400ms
for i in 1 2 3; do
    run_test "vegas_10mbps" "" $i
done
tc qdisc del dev eth0 root 2>/dev/null || true

echo -e "\n${PURPLE}3. Reno com perda${NC}"
sysctl -w net.ipv4.tcp_congestion_control=reno >/dev/null 2>&1
tc qdisc add dev eth0 root netem loss 0.5%
for i in 1 2 3; do
    run_test "reno_loss" "" $i
done
tc qdisc del dev eth0 root 2>/dev/null || true

echo -e "\n${PURPLE}4. BBR com alta latência${NC}"
sysctl -w net.ipv4.tcp_congestion_control=bbr >/dev/null 2>&1
tc qdisc add dev eth0 root netem delay 100ms
for i in 1 2 3; do
    run_test "bbr_highlatency" "-P 4" $i
done
tc qdisc del dev eth0 root 2>/dev/null || true

echo -e "\n${PURPLE}5. Westwood com latência média${NC}"
sysctl -w net.ipv4.tcp_congestion_control=westwood >/dev/null 2>&1
tc qdisc add dev eth0 root netem delay 50ms
for i in 1 2 3; do
    run_test "westwood_50ms" "" $i
done
tc qdisc del dev eth0 root 2>/dev/null || true

echo -e "\n${PURPLE}6. Illinois (baseline alternativo)${NC}"
sysctl -w net.ipv4.tcp_congestion_control=illinois >/dev/null 2>&1
for i in 1 2 3; do
    run_test "illinois_baseline" "" $i
done

# Restaurar
sysctl -w net.ipv4.tcp_congestion_control=cubic >/dev/null 2>&1
tc qdisc del dev eth0 root 2>/dev/null || true

# Contar arquivos
num_files=$(ls -1 "${RESULTS_DIR}/${TIMESTAMP}_*.json" 2>/dev/null | wc -l)

echo -e "\n${GREEN}=== Concluído ===${NC}"
echo "Timestamp: $TIMESTAMP"
echo "Arquivos gerados: $num_files"

# Listar alguns resultados
echo -e "\nPrimeiros arquivos:"
ls -la "${RESULTS_DIR}/${TIMESTAMP}_*.json" 2>/dev/null | head -5