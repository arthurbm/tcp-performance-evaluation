#!/bin/bash

echo "=== TCP Performance Test Server ==="
echo "Starting iperf3 server on port 5201..."
echo "Server IP: 172.20.0.10"
echo "=================================="

# Exibir informações do sistema
echo -e "\nSystem Information:"
uname -a
echo -e "\nNetwork Configuration:"
ip addr show
echo -e "\nTCP Configuration:"
sysctl net.ipv4.tcp_congestion_control
sysctl net.ipv4.tcp_available_congestion_control

# Iniciar servidor iperf3
# -s: modo servidor
# -D: rodar como daemon
# -J: output em JSON
# --logfile: salvar logs
echo -e "\nStarting iperf3 server..."
iperf3 -s -J --logfile /results/server.log

# Manter container rodando
tail -f /dev/null