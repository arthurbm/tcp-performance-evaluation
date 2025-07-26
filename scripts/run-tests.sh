#!/bin/bash

# Script principal para executar todos os cenários de teste
# Autor: Sistema automatizado de avaliação de desempenho TCP

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
SERVER_IP="172.20.0.10"
TEST_DURATION=30
RESULTS_DIR="/results/raw"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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

# Função para limpar configurações tc
cleanup_tc() {
    print_info "Limpando configurações tc..."
    tc qdisc del dev eth0 root 2>/dev/null || true
}

# Função para aplicar configurações tc
apply_tc() {
    local tc_command="$1"
    if [ -n "$tc_command" ]; then
        print_info "Aplicando: $tc_command"
        eval "$tc_command"
    fi
}

# Função para mudar algoritmo de congestionamento
change_congestion_control() {
    local algorithm="$1"
    if [ -n "$algorithm" ]; then
        print_info "Mudando algoritmo de congestionamento para: $algorithm"
        
        # Verificar se o algoritmo está disponível
        if sysctl net.ipv4.tcp_available_congestion_control | grep -q "$algorithm"; then
            sysctl -w net.ipv4.tcp_congestion_control=$algorithm
            print_success "Algoritmo $algorithm ativado"
        else
            print_warning "Algoritmo $algorithm não disponível, tentando carregar módulo..."
            modprobe tcp_$algorithm 2>/dev/null || true
            
            if sysctl net.ipv4.tcp_available_congestion_control | grep -q "$algorithm"; then
                sysctl -w net.ipv4.tcp_congestion_control=$algorithm
                print_success "Algoritmo $algorithm carregado e ativado"
            else
                print_error "Algoritmo $algorithm não pôde ser ativado"
                return 1
            fi
        fi
    fi
}

# Função para executar um teste
run_single_test() {
    local test_name="$1"
    local params="$2"
    local repetition="$3"
    local output_file="${RESULTS_DIR}/${TIMESTAMP}_${test_name}_rep${repetition}.json"
    
    print_info "Executando teste: $test_name (repetição $repetition)"
    print_info "Parâmetros: $params"
    
    # Executar iperf3
    iperf3 -c $SERVER_IP -t $TEST_DURATION -J $params > "$output_file" 2>&1
    
    if [ $? -eq 0 ]; then
        print_success "Teste $test_name completado"
    else
        print_error "Teste $test_name falhou"
        cat "$output_file"
    fi
    
    # Aguardar entre testes
    sleep 5
}

# Função principal
main() {
    print_info "=== Iniciando bateria de testes de desempenho TCP ==="
    print_info "Timestamp: $TIMESTAMP"
    print_info "Servidor: $SERVER_IP"
    print_info "Duração por teste: ${TEST_DURATION}s"
    
    # Criar diretório de resultados
    mkdir -p "$RESULTS_DIR"
    
    # Salvar configurações iniciais
    print_info "Salvando configurações do sistema..."
    {
        echo "=== Configurações do Sistema ==="
        echo "Data: $(date)"
        echo "Kernel: $(uname -r)"
        echo ""
        echo "=== TCP Configuration ==="
        sysctl net.ipv4.tcp_congestion_control
        sysctl net.ipv4.tcp_available_congestion_control
        echo ""
        echo "=== Network Configuration ==="
        ip addr show
        echo ""
    } > "${RESULTS_DIR}/${TIMESTAMP}_system_config.txt"
    
    # Testar conectividade
    print_info "Testando conectividade com servidor..."
    if ping -c 3 $SERVER_IP > /dev/null 2>&1; then
        print_success "Servidor alcançável"
    else
        print_error "Servidor não alcançável!"
        exit 1
    fi
    
    # Salvar algoritmo de congestionamento original
    ORIGINAL_CC=$(sysctl -n net.ipv4.tcp_congestion_control)
    
    # 1. TESTE BASELINE
    print_info "=== Executando testes baseline ==="
    for rep in 1 2 3; do
        run_single_test "baseline_default" "" $rep
    done
    
    # 2. TESTES DE JANELA TCP
    print_info "=== Executando testes de janela TCP ==="
    for window in "64K" "128K" "256K" "512K"; do
        for rep in 1 2 3; do
            run_single_test "window_${window}" "-w ${window}" $rep
        done
    done
    
    # 3. TESTES DE FLUXOS PARALELOS
    print_info "=== Executando testes de fluxos paralelos ==="
    for streams in 1 2 4 8; do
        for rep in 1 2 3; do
            run_single_test "streams_${streams}" "-P ${streams}" $rep
        done
    done
    
    # 4. TESTES DE ALGORITMOS DE CONGESTIONAMENTO
    print_info "=== Executando testes de algoritmos de congestionamento ==="
    for algorithm in "cubic" "reno" "vegas" "bbr"; do
        if change_congestion_control "$algorithm"; then
            for rep in 1 2 3; do
                run_single_test "cc_${algorithm}" "" $rep
            done
        fi
    done
    
    # Restaurar algoritmo original
    change_congestion_control "$ORIGINAL_CC"
    
    # 5. TESTES COM CONDIÇÕES DE REDE
    print_info "=== Executando testes com condições de rede simuladas ==="
    
    # Latência
    for delay in "50ms" "100ms"; do
        cleanup_tc
        apply_tc "tc qdisc add dev eth0 root netem delay ${delay}"
        for rep in 1 2 3; do
            run_single_test "latency_${delay}" "" $rep
        done
    done
    
    # Limitação de banda
    for rate in "10mbit" "100mbit"; do
        cleanup_tc
        apply_tc "tc qdisc add dev eth0 root tbf rate ${rate} burst 32kbit latency 400ms"
        for rep in 1 2 3; do
            run_single_test "bandwidth_${rate}" "" $rep
        done
    done
    
    # Perda de pacotes
    for loss in "0.1%" "1%"; do
        cleanup_tc
        apply_tc "tc qdisc add dev eth0 root netem loss ${loss}"
        for rep in 1 2 3; do
            run_single_test "packet_loss_${loss}" "" $rep
        done
    done
    
    # Limpar tc no final
    cleanup_tc
    
    # 6. TESTES COMBINADOS
    print_info "=== Executando testes combinados ==="
    for rep in 1 2 3; do
        run_single_test "combined_256k_4streams" "-w 256K -P 4" $rep
        run_single_test "combined_512k_2streams" "-w 512K -P 2" $rep
    done
    
    # Teste com BBR + configurações otimizadas (se disponível)
    if change_congestion_control "bbr"; then
        for rep in 1 2 3; do
            run_single_test "combined_bbr_256k_4streams" "-w 256K -P 4" $rep
        done
    fi
    
    # Restaurar configurações originais
    change_congestion_control "$ORIGINAL_CC"
    cleanup_tc
    
    print_success "=== Todos os testes foram completados ==="
    print_info "Resultados salvos em: $RESULTS_DIR"
    print_info "Timestamp: $TIMESTAMP"
    
    # Contar arquivos de resultado
    num_results=$(find "$RESULTS_DIR" -name "${TIMESTAMP}_*.json" | wc -l)
    print_info "Total de testes executados: $num_results"
}

# Executar função principal
main "$@"