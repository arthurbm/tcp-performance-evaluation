#!/bin/bash

echo "=== TCP Performance Test Client ==="
echo "Client IP: 172.20.0.20"
echo "Server IP: 172.20.0.10"
echo "=================================="

# Aguardar servidor iniciar
echo "Waiting for server to start..."
sleep 5

# Testar conectividade
echo -e "\nTesting connectivity to server..."
ping -c 3 172.20.0.10

# Exibir configurações TCP
echo -e "\nTCP Configuration:"
sysctl net.ipv4.tcp_congestion_control
sysctl net.ipv4.tcp_available_congestion_control

# Manter container rodando para testes manuais
echo -e "\nClient ready for testing."
echo "Run tests manually or use /scripts/run-tests.sh"
echo "Example: iperf3 -c 172.20.0.10 -t 30"

# Manter bash interativo
/bin/bash