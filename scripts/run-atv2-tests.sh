#!/bin/bash

# Script para executar os 6 cenários específicos da Atividade 2
# Autor: Sistema de Avaliação de Desempenho TCP - Atividade 2

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configurações
SERVER_IP="10.5.0.10"
SCENARIOS_DIR="/results/atv2/scenarios"
RESULTS_DIR="/results/atv2/results/raw"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Criar diretório de resultados se não existir
mkdir -p "$RESULTS_DIR"

# Função para imprimir com cor
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_scenario() {
    echo -e "${PURPLE}[SCENARIO]${NC} $1"
}

# Função para limpar configurações tc
cleanup_tc() {
    tc qdisc del dev eth0 root 2>/dev/null || true
}

# Função para aplicar condições de rede
apply_network_conditions() {
    local latency="$1"
    local bandwidth="$2"
    local loss="$3"
    local jitter="$4"
    
    cleanup_tc
    
    # Construir comando tc baseado nos parâmetros
    local tc_cmd=""
    local netem_params=""
    
    if [ -n "$latency" ] && [ "$latency" != "null" ]; then
        netem_params="delay ${latency}ms"
        
        if [ -n "$jitter" ] && [ "$jitter" != "null" ]; then
            netem_params="$netem_params ${jitter}ms distribution normal"
        fi
    fi
    
    if [ -n "$loss" ] && [ "$loss" != "null" ]; then
        if [ -n "$netem_params" ]; then
            netem_params="$netem_params loss ${loss}%"
        else
            netem_params="loss ${loss}%"
        fi
    fi
    
    # Aplicar netem se houver parâmetros
    if [ -n "$netem_params" ]; then
        if [ -n "$bandwidth" ] && [ "$bandwidth" != "null" ]; then
            # Combinar netem com tbf para limitação de banda
            print_info "Aplicando: tc qdisc add dev eth0 root handle 1: netem $netem_params"
            tc qdisc add dev eth0 root handle 1: netem $netem_params
            
            print_info "Aplicando: tc qdisc add dev eth0 parent 1: handle 2: tbf rate ${bandwidth}mbit burst 32kbit latency 400ms"
            tc qdisc add dev eth0 parent 1: handle 2: tbf rate ${bandwidth}mbit burst 32kbit latency 400ms
        else
            print_info "Aplicando: tc qdisc add dev eth0 root netem $netem_params"
            tc qdisc add dev eth0 root netem $netem_params
        fi
    elif [ -n "$bandwidth" ] && [ "$bandwidth" != "null" ]; then
        # Apenas limitação de banda
        print_info "Aplicando: tc qdisc add dev eth0 root tbf rate ${bandwidth}mbit burst 32kbit latency 400ms"
        tc qdisc add dev eth0 root tbf rate ${bandwidth}mbit burst 32kbit latency 400ms
    fi
}

# Função para mudar algoritmo de congestionamento
change_congestion_control() {
    local algorithm="$1"
    
    if [ -z "$algorithm" ] || [ "$algorithm" == "null" ]; then
        return 0
    fi
    
    print_info "Mudando algoritmo de congestionamento para: $algorithm"
    
    # Verificar se o algoritmo está disponível
    if sysctl net.ipv4.tcp_available_congestion_control | grep -q "$algorithm"; then
        sysctl -w net.ipv4.tcp_congestion_control=$algorithm >/dev/null 2>&1
        print_success "Algoritmo $algorithm ativado"
    else
        print_warning "Algoritmo $algorithm não disponível, tentando carregar módulo..."
        modprobe tcp_$algorithm 2>/dev/null || true
        
        if sysctl net.ipv4.tcp_available_congestion_control | grep -q "$algorithm"; then
            sysctl -w net.ipv4.tcp_congestion_control=$algorithm >/dev/null 2>&1
            print_success "Algoritmo $algorithm carregado e ativado"
        else
            print_error "Algoritmo $algorithm não pôde ser ativado"
            return 1
        fi
    fi
}

# Função para executar um cenário
run_scenario() {
    local scenario_file="$1"
    local scenario_name=$(basename "$scenario_file" .json)
    
    print_scenario "=== Executando: $scenario_name ==="
    
    # Ler configurações do JSON
    local name=$(jq -r '.name' "$scenario_file")
    local description=$(jq -r '.description' "$scenario_file")
    local iperf_params=$(jq -r '.iperf_params' "$scenario_file")
    local cc=$(jq -r '.tcp_settings.congestion_control' "$scenario_file")
    local latency=$(jq -r '.network_conditions.latency_ms' "$scenario_file")
    local bandwidth=$(jq -r '.network_conditions.bandwidth_mbps' "$scenario_file")
    local loss=$(jq -r '.network_conditions.packet_loss_percent' "$scenario_file")
    local jitter=$(jq -r '.network_conditions.jitter_ms' "$scenario_file")
    local duration=$(jq -r '.test_duration' "$scenario_file")
    local repetitions=$(jq -r '.repetitions' "$scenario_file")
    
    print_info "Descrição: $description"
    print_info "Parâmetros iperf3: $iperf_params"
    print_info "Repetições: $repetitions"
    
    # Configurar algoritmo de congestionamento
    if ! change_congestion_control "$cc"; then
        print_warning "Continuando com algoritmo padrão"
    fi
    
    # Aplicar condições de rede
    apply_network_conditions "$latency" "$bandwidth" "$loss" "$jitter"
    
    # Executar repetições
    for rep in $(seq 1 $repetitions); do
        local output_file="${RESULTS_DIR}/${TIMESTAMP}_${name}_rep${rep}.json"
        
        print_info "Executando repetição $rep/$repetitions..."
        
        # Executar iperf3
        if [ -n "$iperf_params" ] && [ "$iperf_params" != "null" ]; then
            iperf3 -c $SERVER_IP -t $duration -J $iperf_params > "$output_file" 2>&1
        else
            iperf3 -c $SERVER_IP -t $duration -J > "$output_file" 2>&1
        fi
        
        if [ $? -eq 0 ]; then
            print_success "Repetição $rep completada"
            
            # Extrair e mostrar throughput
            local throughput=$(jq -r '.end.sum_sent.bits_per_second' "$output_file" 2>/dev/null || echo "N/A")
            if [ "$throughput" != "N/A" ] && [ "$throughput" != "null" ]; then
                local throughput_mbps=$(echo "scale=2; $throughput / 1000000" | bc)
                print_info "Throughput: ${throughput_mbps} Mbps"
            fi
        else
            print_error "Repetição $rep falhou"
            print_error "Verificar arquivo: $output_file"
        fi
        
        # Aguardar entre repetições
        if [ $rep -lt $repetitions ]; then
            sleep 5
        fi
    done
    
    # Limpar configurações após o cenário
    cleanup_tc
    
    print_success "Cenário $scenario_name concluído"
    echo ""
}

# Função principal
main() {
    print_info "=== Iniciando Testes da Atividade 2 ==="
    print_info "Timestamp: $TIMESTAMP"
    print_info "Servidor: $SERVER_IP"
    echo ""
    
    # Salvar configurações iniciais
    print_info "Salvando configurações do sistema..."
    {
        echo "=== Configurações do Sistema - Atividade 2 ==="
        echo "Data: $(date)"
        echo "Timestamp: $TIMESTAMP"
        echo "Kernel: $(uname -r)"
        echo ""
        echo "=== TCP Configuration ==="
        sysctl net.ipv4.tcp_congestion_control
        sysctl net.ipv4.tcp_available_congestion_control
        echo ""
        echo "=== Network Configuration ==="
        ip addr show eth0
        echo ""
    } > "${RESULTS_DIR}/${TIMESTAMP}_system_config.txt"
    
    # Salvar algoritmo original
    ORIGINAL_CC=$(sysctl -n net.ipv4.tcp_congestion_control)
    
    # Testar conectividade
    print_info "Testando conectividade com servidor..."
    if ping -c 3 $SERVER_IP > /dev/null 2>&1; then
        print_success "Servidor alcançável"
    else
        print_error "Servidor não alcançável!"
        exit 1
    fi
    echo ""
    
    # Executar cada cenário
    local scenario_count=0
    local total_scenarios=6
    
    for scenario_file in ${SCENARIOS_DIR}/scenario_*.json; do
        if [ -f "$scenario_file" ]; then
            ((scenario_count++))
            print_info "Progresso: $scenario_count/$total_scenarios cenários"
            run_scenario "$scenario_file"
        fi
    done
    
    # Restaurar configurações originais
    print_info "Restaurando configurações originais..."
    change_congestion_control "$ORIGINAL_CC" >/dev/null 2>&1
    cleanup_tc
    
    # Resumo final
    print_success "=== Todos os testes foram completados ==="
    print_info "Total de cenários executados: $scenario_count"
    print_info "Resultados salvos em: $RESULTS_DIR"
    print_info "Timestamp: $TIMESTAMP"
    
    # Contar arquivos de resultado
    local num_results=$(find "$RESULTS_DIR" -name "${TIMESTAMP}_*.json" | wc -l)
    print_info "Total de arquivos de resultado: $num_results"
    
    # Criar arquivo de resumo
    {
        echo "=== Resumo da Execução - Atividade 2 ==="
        echo "Timestamp: $TIMESTAMP"
        echo "Cenários executados: $scenario_count"
        echo "Total de testes: $num_results"
        echo "Duração aproximada: $((scenario_count * 30 * 5 / 60)) minutos"
        echo ""
        echo "Cenários:"
        for scenario_file in ${SCENARIOS_DIR}/scenario_*.json; do
            if [ -f "$scenario_file" ]; then
                local name=$(jq -r '.description' "$scenario_file")
                echo "- $name"
            fi
        done
    } > "${RESULTS_DIR}/${TIMESTAMP}_execution_summary.txt"
    
    print_info "Execute analyze-atv2.py para processar os resultados"
}

# Verificar se está sendo executado no container correto
if [ ! -f /scripts/run-tests.sh ]; then
    print_error "Este script deve ser executado dentro do container tcp-client"
    exit 1
fi

# Executar função principal
main "$@"