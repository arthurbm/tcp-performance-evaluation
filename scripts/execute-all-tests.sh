#!/bin/bash

# Script direto para executar todos os testes necessários

echo "=== Executando Testes Completos da Atividade 2 ==="

cd /results/atv2/results/raw
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Timestamp: $TIMESTAMP"

# Função auxiliar
test_algorithm() {
    local algo=$1
    local name=$2
    echo "Testando $name..."
    
    sysctl -w net.ipv4.tcp_congestion_control=$algo
    
    for i in 1 2 3; do
        echo "  Rep $i/3..."
        iperf3 -c 10.5.0.10 -t 10 -J > ${TIMESTAMP}_${name}_baseline_rep${i}.json 2>&1
        sleep 2
    done
}

# Limpar tc
tc qdisc del dev eth0 root 2>/dev/null || true

# 1. Testes baseline de cada algoritmo
echo -e "\n=== Fase 1: Baseline de cada algoritmo ==="
test_algorithm cubic "cubic"
test_algorithm bbr "bbr"
test_algorithm vegas "vegas"
test_algorithm reno "reno"
test_algorithm westwood "westwood"
test_algorithm illinois "illinois"

# 2. Testes com condições de rede
echo -e "\n=== Fase 2: Testes com condições de rede ==="

# CUBIC com latência 50ms
echo "CUBIC com latência 50ms..."
sysctl -w net.ipv4.tcp_congestion_control=cubic
tc qdisc add dev eth0 root netem delay 50ms
for i in 1 2 3; do
    iperf3 -c 10.5.0.10 -t 10 -J > ${TIMESTAMP}_cubic_latency50ms_rep${i}.json 2>&1
    sleep 2
done
tc qdisc del dev eth0 root

# BBR com latência 100ms
echo "BBR com latência 100ms..."
sysctl -w net.ipv4.tcp_congestion_control=bbr
tc qdisc add dev eth0 root netem delay 100ms
for i in 1 2 3; do
    iperf3 -c 10.5.0.10 -t 10 -J > ${TIMESTAMP}_bbr_latency100ms_rep${i}.json 2>&1
    sleep 2
done
tc qdisc del dev eth0 root

# Vegas com banda limitada 10Mbps
echo "Vegas com banda 10Mbps..."
sysctl -w net.ipv4.tcp_congestion_control=vegas
tc qdisc add dev eth0 root tbf rate 10mbit burst 32kbit latency 400ms
for i in 1 2 3; do
    iperf3 -c 10.5.0.10 -t 10 -J > ${TIMESTAMP}_vegas_band10mbps_rep${i}.json 2>&1
    sleep 2
done
tc qdisc del dev eth0 root

# Reno com perda 0.5%
echo "Reno com perda 0.5%..."
sysctl -w net.ipv4.tcp_congestion_control=reno
tc qdisc add dev eth0 root netem loss 0.5%
for i in 1 2 3; do
    iperf3 -c 10.5.0.10 -t 10 -J > ${TIMESTAMP}_reno_loss0.5_rep${i}.json 2>&1
    sleep 2
done
tc qdisc del dev eth0 root

# 3. Testes com múltiplos fluxos
echo -e "\n=== Fase 3: Testes com múltiplos fluxos ==="

# CUBIC com 4 fluxos
echo "CUBIC com 4 fluxos..."
sysctl -w net.ipv4.tcp_congestion_control=cubic
for i in 1 2 3; do
    iperf3 -c 10.5.0.10 -t 10 -P 4 -J > ${TIMESTAMP}_cubic_4streams_rep${i}.json 2>&1
    sleep 2
done

# BBR com 8 fluxos
echo "BBR com 8 fluxos..."
sysctl -w net.ipv4.tcp_congestion_control=bbr
for i in 1 2 3; do
    iperf3 -c 10.5.0.10 -t 10 -P 8 -J > ${TIMESTAMP}_bbr_8streams_rep${i}.json 2>&1
    sleep 2
done

# Restaurar
sysctl -w net.ipv4.tcp_congestion_control=cubic
tc qdisc del dev eth0 root 2>/dev/null || true

# Salvar configurações
echo -e "\nSalvando configurações..."
{
    echo "=== Configurações do Sistema ==="
    echo "Timestamp: $TIMESTAMP"
    echo "Data: $(date)"
    echo ""
    echo "Algoritmos disponíveis:"
    sysctl net.ipv4.tcp_available_congestion_control
    echo ""
    echo "Testes executados:"
    ls -1 ${TIMESTAMP}_*.json | wc -l
} > ${TIMESTAMP}_system_config.txt

# Contar resultados
num_files=$(ls -1 ${TIMESTAMP}_*.json 2>/dev/null | wc -l)

echo -e "\n=== Resumo ==="
echo "Timestamp: $TIMESTAMP"
echo "Total de arquivos: $num_files"
echo "Primeiros arquivos:"
ls -la ${TIMESTAMP}_*.json | head -5