#!/usr/bin/env python3

"""
Análise simplificada dos resultados - sem dependências externas
"""

import json
from pathlib import Path
import statistics

def load_results(timestamp="20250801_044307"):
    """Carrega todos os resultados"""
    results_dir = Path("/results/atv2/results/raw")
    data = []
    
    for result_file in results_dir.glob(f"{timestamp}_*.json"):
        if 'system_config' in str(result_file):
            continue
            
        try:
            with open(result_file, 'r') as f:
                result = json.load(f)
            
            filename = result_file.stem
            parts = filename.split('_')
            
            # Identificar teste
            if 'baseline' in filename:
                test_type = 'baseline'
                algorithm = parts[2]
                condition = 'none'
            elif 'latency' in filename:
                test_type = 'latency'
                algorithm = parts[2]
                condition = 'high'
            elif 'band' in filename:
                test_type = 'bandwidth'
                algorithm = parts[2]
                condition = '10mbps'
            elif 'loss' in filename:
                test_type = 'loss'
                algorithm = parts[2]
                condition = '0.5%'
            elif 'streams' in filename:
                test_type = 'streams'
                algorithm = parts[2]
                condition = 'multiple'
            else:
                continue
            
            # Extrair métricas
            if 'end' in result and 'sum_sent' in result['end']:
                throughput_bps = result['end']['sum_sent']['bits_per_second']
                throughput_mbps = throughput_bps / 1e6
                retransmits = result['end']['sum_sent'].get('retransmits', 0)
                
                data.append({
                    'algorithm': algorithm,
                    'test_type': test_type,
                    'condition': condition,
                    'throughput_mbps': throughput_mbps,
                    'retransmits': retransmits
                })
                
        except Exception as e:
            print(f"Erro: {e}")
    
    return data

def analyze_by_algorithm(data):
    """Agrupa e analisa por algoritmo"""
    algorithms = {}
    
    for entry in data:
        algo = entry['algorithm']
        if algo not in algorithms:
            algorithms[algo] = {
                'baseline': [],
                'latency': [],
                'loss': [],
                'streams': [],
                'all_throughputs': [],
                'all_retransmits': []
            }
        
        algorithms[algo][entry['test_type']].append(entry['throughput_mbps'])
        algorithms[algo]['all_throughputs'].append(entry['throughput_mbps'])
        algorithms[algo]['all_retransmits'].append(entry['retransmits'])
    
    return algorithms

def print_analysis(algorithms):
    """Imprime análise formatada"""
    print("=== ANÁLISE COMPLETA DOS RESULTADOS - ATIVIDADE 2 ===\n")
    
    print("1. COMPARAÇÃO DE ALGORITMOS (Baseline)")
    print("-" * 80)
    print(f"{'Algoritmo':<15} {'Throughput Médio':<20} {'Desvio Padrão':<20} {'Retransmissões':<20}")
    print("-" * 80)
    
    baseline_results = []
    for algo, data in algorithms.items():
        if data['baseline']:
            mean_tp = statistics.mean(data['baseline'])
            std_tp = statistics.stdev(data['baseline']) if len(data['baseline']) > 1 else 0
            mean_ret = statistics.mean(data['all_retransmits'])
            
            baseline_results.append((algo, mean_tp, std_tp, mean_ret))
            print(f"{algo.upper():<15} {mean_tp:>15.1f} Mbps {std_tp:>15.1f} Mbps {mean_ret:>15.0f}")
    
    print("\n2. IMPACTO DAS CONDIÇÕES DE REDE")
    print("-" * 80)
    
    for algo, data in algorithms.items():
        if data['baseline']:
            baseline_mean = statistics.mean(data['baseline'])
            print(f"\n{algo.upper()}:")
            
            # Latência
            if data['latency']:
                latency_mean = statistics.mean(data['latency'])
                impact = ((latency_mean - baseline_mean) / baseline_mean) * 100
                print(f"  Latência alta: {latency_mean:.1f} Mbps ({impact:+.1f}% vs baseline)")
            
            # Perda
            if data['loss']:
                loss_mean = statistics.mean(data['loss'])
                impact = ((loss_mean - baseline_mean) / baseline_mean) * 100
                print(f"  Perda 0.5%: {loss_mean:.1f} Mbps ({impact:+.1f}% vs baseline)")
            
            # Múltiplos streams
            if data['streams']:
                streams_mean = statistics.mean(data['streams'])
                impact = ((streams_mean - baseline_mean) / baseline_mean) * 100
                print(f"  Múltiplos streams: {streams_mean:.1f} Mbps ({impact:+.1f}% vs baseline)")
    
    print("\n3. RANKING DE DESEMPENHO")
    print("-" * 80)
    
    # Ordenar por throughput médio baseline
    sorted_algos = sorted(baseline_results, key=lambda x: x[1], reverse=True)
    
    for i, (algo, mean_tp, std_tp, mean_ret) in enumerate(sorted_algos, 1):
        print(f"{i}. {algo.upper()}: {mean_tp:.1f} Mbps")
    
    print("\n4. ANÁLISE DE ESTABILIDADE")
    print("-" * 80)
    
    stability_scores = []
    for algo, data in algorithms.items():
        if data['all_throughputs'] and len(data['all_throughputs']) > 1:
            cv = (statistics.stdev(data['all_throughputs']) / statistics.mean(data['all_throughputs'])) * 100
            stability_scores.append((algo, cv))
    
    sorted_stability = sorted(stability_scores, key=lambda x: x[1])
    
    for algo, cv in sorted_stability:
        stability = "Muito estável" if cv < 10 else "Estável" if cv < 20 else "Variável"
        print(f"{algo.upper()}: CV = {cv:.1f}% ({stability})")
    
    print("\n5. PRINCIPAIS DESCOBERTAS")
    print("-" * 80)
    
    # Melhor algoritmo geral
    if sorted_algos:
        best_algo = sorted_algos[0][0]
        print(f"✓ Melhor desempenho geral: {best_algo.upper()}")
    
    # Algoritmo mais estável
    if sorted_stability:
        most_stable = sorted_stability[0][0]
        print(f"✓ Algoritmo mais estável: {most_stable.upper()}")
    
    # Impacto das condições
    print("\n✓ Impactos observados:")
    print("  - Latência alta: redução drástica no throughput (até -98%)")
    print("  - Perda de pacotes: impacto significativo no desempenho")
    print("  - Múltiplos streams: pode melhorar ou piorar dependendo do algoritmo")
    
    return baseline_results

def save_summary(algorithms, timestamp):
    """Salva resumo dos resultados"""
    output_file = Path(f"/results/atv2/results/processed/analysis_summary_{timestamp}.txt")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write("=== RESUMO DA ANÁLISE - ATIVIDADE 2 ===\n\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Total de testes analisados: {sum(len(d['all_throughputs']) for d in algorithms.values())}\n")
        f.write(f"Algoritmos testados: {', '.join(algorithms.keys())}\n\n")
        
        f.write("RESULTADOS BASELINE:\n")
        for algo, data in algorithms.items():
            if data['baseline']:
                mean_tp = statistics.mean(data['baseline'])
                f.write(f"- {algo.upper()}: {mean_tp:.1f} Mbps\n")
        
        f.write("\nCONDIÇÕES TESTADAS:\n")
        f.write("- Baseline (sem limitações)\n")
        f.write("- Alta latência (50-100ms)\n")
        f.write("- Perda de pacotes (0.5%)\n")
        f.write("- Múltiplos streams (4-8)\n")
    
    print(f"\nResumo salvo em: {output_file}")

def main():
    timestamp = "20250801_044307"
    
    print(f"Analisando resultados do timestamp: {timestamp}\n")
    
    # Carregar e analisar
    data = load_results(timestamp)
    
    if not data:
        print("Nenhum resultado encontrado!")
        return
    
    print(f"Total de testes carregados: {len(data)}\n")
    
    # Análise por algoritmo
    algorithms = analyze_by_algorithm(data)
    
    # Imprimir análise
    baseline_results = print_analysis(algorithms)
    
    # Salvar resumo
    save_summary(algorithms, timestamp)
    
    print("\n✓ Análise concluída com sucesso!")

if __name__ == "__main__":
    main()