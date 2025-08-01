#!/bin/bash

# Teste simples para verificar execução de um cenário

echo "=== Teste Simples Atividade 2 ==="
echo "Testando conectividade..."

ping -c 3 10.5.0.10

echo -e "\nTestando iperf3 básico..."
iperf3 -c 10.5.0.10 -t 5 -J > /tmp/test_result.json

if [ $? -eq 0 ]; then
    echo "✓ Teste básico bem sucedido"
    throughput=$(jq -r '.end.sum_sent.bits_per_second' /tmp/test_result.json 2>/dev/null || echo "N/A")
    if [ "$throughput" != "N/A" ] && [ "$throughput" != "null" ]; then
        throughput_mbps=$(echo "scale=2; $throughput / 1000000" | bc)
        echo "Throughput: ${throughput_mbps} Mbps"
    fi
else
    echo "✗ Teste falhou"
    cat /tmp/test_result.json
fi

echo -e "\nVerificando algoritmos de congestionamento disponíveis..."
sysctl net.ipv4.tcp_available_congestion_control

echo -e "\nAlgoritmo atual:"
sysctl net.ipv4.tcp_congestion_control