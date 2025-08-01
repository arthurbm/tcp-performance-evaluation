#!/usr/bin/env python3

"""
Análise completa dos resultados da Atividade 2
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import sys

# Configurações
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_results(timestamp="20250801_044307"):
    """Carrega todos os resultados do timestamp"""
    results_dir = Path("/results/atv2/results/raw")
    data = []
    
    for result_file in results_dir.glob(f"{timestamp}_*.json"):
        if 'system_config' in str(result_file):
            continue
            
        try:
            with open(result_file, 'r') as f:
                result = json.load(f)
            
            # Extrair nome do teste
            filename = result_file.stem
            parts = filename.split('_')
            
            # Identificar tipo de teste
            if 'baseline' in filename:
                test_type = 'baseline'
                algorithm = parts[2]
                condition = 'none'
            elif 'latency' in filename:
                test_type = 'latency'
                algorithm = parts[2]
                condition = parts[3]
            elif 'band' in filename:
                test_type = 'bandwidth'
                algorithm = parts[2]
                condition = parts[3]
            elif 'loss' in filename:
                test_type = 'loss'
                algorithm = parts[2]
                condition = parts[3]
            elif 'streams' in filename:
                test_type = 'streams'
                algorithm = parts[2]
                condition = parts[3]
            else:
                continue
            
            # Extrair métricas
            if 'end' in result and 'sum_sent' in result['end']:
                throughput_bps = result['end']['sum_sent']['bits_per_second']
                throughput_mbps = throughput_bps / 1e6
                
                retransmits = result['end']['sum_sent'].get('retransmits', 0)
                
                # Streams info
                streams = result['end'].get('streams', [])
                num_streams = len(streams)
                
                data.append({
                    'timestamp': timestamp,
                    'algorithm': algorithm,
                    'test_type': test_type,
                    'condition': condition,
                    'throughput_mbps': throughput_mbps,
                    'retransmits': retransmits,
                    'num_streams': num_streams if num_streams > 1 else 1
                })
                
        except Exception as e:
            print(f"Erro ao processar {result_file}: {e}")
    
    df = pd.DataFrame(data)
    print(f"Carregados {len(df)} resultados")
    return df

def analyze_algorithms(df):
    """Análise comparativa dos algoritmos"""
    print("\n=== Análise por Algoritmo ===\n")
    
    # Baseline comparison
    baseline_df = df[df['test_type'] == 'baseline']
    
    print("Desempenho Baseline (sem limitações):")
    print("-" * 60)
    
    for algo in baseline_df['algorithm'].unique():
        algo_data = baseline_df[baseline_df['algorithm'] == algo]
        mean_tp = algo_data['throughput_mbps'].mean()
        std_tp = algo_data['throughput_mbps'].std()
        mean_ret = algo_data['retransmits'].mean()
        
        print(f"{algo.upper():8} | Throughput: {mean_tp:>8.1f} ± {std_tp:>6.1f} Mbps | Retrans: {mean_ret:>6.0f}")
    
    return baseline_df.groupby('algorithm')['throughput_mbps'].agg(['mean', 'std', 'count'])

def analyze_conditions(df):
    """Análise do impacto das condições de rede"""
    print("\n=== Impacto das Condições de Rede ===\n")
    
    conditions_impact = []
    
    # Para cada algoritmo que temos dados completos
    for algo in ['cubic', 'bbr', 'reno']:
        baseline = df[(df['algorithm'] == algo) & (df['test_type'] == 'baseline')]['throughput_mbps'].mean()
        
        if baseline > 0:
            # Latência
            latency_data = df[(df['algorithm'] == algo) & (df['test_type'] == 'latency')]
            if not latency_data.empty:
                latency_tp = latency_data['throughput_mbps'].mean()
                impact = (latency_tp - baseline) / baseline * 100
                conditions_impact.append({
                    'algorithm': algo,
                    'condition': 'latency',
                    'baseline_mbps': baseline,
                    'condition_mbps': latency_tp,
                    'impact_percent': impact
                })
            
            # Perda
            loss_data = df[(df['algorithm'] == algo) & (df['test_type'] == 'loss')]
            if not loss_data.empty:
                loss_tp = loss_data['throughput_mbps'].mean()
                impact = (loss_tp - baseline) / baseline * 100
                conditions_impact.append({
                    'algorithm': algo,
                    'condition': 'loss_0.5%',
                    'baseline_mbps': baseline,
                    'condition_mbps': loss_tp,
                    'impact_percent': impact
                })
    
    impact_df = pd.DataFrame(conditions_impact)
    
    if not impact_df.empty:
        print("Impacto percentual vs baseline:")
        print("-" * 80)
        for _, row in impact_df.iterrows():
            print(f"{row['algorithm'].upper():8} | {row['condition']:12} | "
                  f"Baseline: {row['baseline_mbps']:>8.1f} | "
                  f"Com condição: {row['condition_mbps']:>8.1f} | "
                  f"Impacto: {row['impact_percent']:>+6.1f}%")
    
    return impact_df

def create_visualizations(df, output_dir):
    """Cria gráficos comparativos"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 1. Comparação de algoritmos (baseline)
    plt.figure(figsize=(10, 6))
    baseline_df = df[df['test_type'] == 'baseline']
    
    algorithms = []
    throughputs = []
    errors = []
    
    for algo in ['cubic', 'bbr', 'reno']:
        algo_data = baseline_df[baseline_df['algorithm'] == algo]
        if not algo_data.empty:
            algorithms.append(algo.upper())
            throughputs.append(algo_data['throughput_mbps'].mean())
            errors.append(algo_data['throughput_mbps'].std())
    
    x = range(len(algorithms))
    plt.bar(x, throughputs, yerr=errors, capsize=5, alpha=0.8)
    plt.xlabel('Algoritmo de Congestionamento')
    plt.ylabel('Throughput (Mbps)')
    plt.title('Comparação de Algoritmos TCP - Baseline')
    plt.xticks(x, algorithms)
    
    # Adicionar valores nas barras
    for i, (algo, tp) in enumerate(zip(algorithms, throughputs)):
        plt.text(i, tp + errors[i] + 500, f'{tp:.0f}', ha='center')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'algorithms_comparison.png', dpi=300)
    plt.close()
    
    # 2. Impacto das condições
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Latência
    ax = axes[0, 0]
    latency_data = []
    for algo in ['cubic', 'bbr']:
        baseline = df[(df['algorithm'] == algo) & (df['test_type'] == 'baseline')]['throughput_mbps'].mean()
        latency = df[(df['algorithm'] == algo) & (df['test_type'] == 'latency')]['throughput_mbps'].mean()
        if baseline > 0 and latency > 0:
            latency_data.append({
                'algorithm': algo.upper(),
                'baseline': baseline,
                'with_latency': latency
            })
    
    if latency_data:
        lat_df = pd.DataFrame(latency_data)
        x = range(len(lat_df))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], lat_df['baseline'], width, label='Baseline', alpha=0.8)
        ax.bar([i + width/2 for i in x], lat_df['with_latency'], width, label='Com Latência', alpha=0.8)
        ax.set_xlabel('Algoritmo')
        ax.set_ylabel('Throughput (Mbps)')
        ax.set_title('Impacto da Latência')
        ax.set_xticks(x)
        ax.set_xticklabels(lat_df['algorithm'])
        ax.legend()
    
    # Perda de pacotes
    ax = axes[0, 1]
    loss_data = []
    for algo in ['reno']:
        baseline = df[(df['algorithm'] == algo) & (df['test_type'] == 'baseline')]['throughput_mbps'].mean()
        loss = df[(df['algorithm'] == algo) & (df['test_type'] == 'loss')]['throughput_mbps'].mean()
        if baseline > 0 and loss > 0:
            loss_data.append({
                'algorithm': algo.upper(),
                'baseline': baseline,
                'with_loss': loss
            })
    
    if loss_data:
        loss_df = pd.DataFrame(loss_data)
        x = range(len(loss_df))
        
        ax.bar([i - width/2 for i in x], loss_df['baseline'], width, label='Baseline', alpha=0.8)
        ax.bar([i + width/2 for i in x], loss_df['with_loss'], width, label='Com Perda 0.5%', alpha=0.8)
        ax.set_xlabel('Algoritmo')
        ax.set_ylabel('Throughput (Mbps)')
        ax.set_title('Impacto da Perda de Pacotes')
        ax.set_xticks(x)
        ax.set_xticklabels(loss_df['algorithm'])
        ax.legend()
    
    # Múltiplos streams
    ax = axes[1, 0]
    streams_data = df[df['test_type'] == 'streams']
    if not streams_data.empty:
        for algo in ['cubic', 'bbr']:
            algo_baseline = df[(df['algorithm'] == algo) & (df['test_type'] == 'baseline')]['throughput_mbps'].mean()
            algo_streams = streams_data[streams_data['algorithm'] == algo]['throughput_mbps'].mean()
            if algo_baseline > 0 and algo_streams > 0:
                ax.bar([algo], [algo_baseline], alpha=0.8, label=f'{algo.upper()} - 1 stream' if algo == 'cubic' else None)
                ax.bar([algo + '_multi'], [algo_streams], alpha=0.8, label=f'{algo.upper()} - múltiplos' if algo == 'cubic' else None)
        
        ax.set_ylabel('Throughput (Mbps)')
        ax.set_title('Impacto de Múltiplos Streams')
        ax.legend()
    
    # Resumo geral
    ax = axes[1, 1]
    summary_data = []
    for algo in df['algorithm'].unique():
        algo_df = df[df['algorithm'] == algo]
        summary_data.append({
            'algorithm': algo.upper(),
            'mean_throughput': algo_df['throughput_mbps'].mean(),
            'mean_retransmits': algo_df['retransmits'].mean()
        })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        ax2 = ax.twinx()
        
        x = range(len(summary_df))
        ax.bar(x, summary_df['mean_throughput'], alpha=0.6, color='blue', label='Throughput')
        ax2.bar(x, summary_df['mean_retransmits'], alpha=0.6, color='red', label='Retransmissões')
        
        ax.set_xlabel('Algoritmo')
        ax.set_ylabel('Throughput Médio (Mbps)', color='blue')
        ax2.set_ylabel('Retransmissões Médias', color='red')
        ax.set_title('Resumo Geral por Algoritmo')
        ax.set_xticks(x)
        ax.set_xticklabels(summary_df['algorithm'])
    
    plt.tight_layout()
    plt.savefig(output_dir / 'complete_analysis.png', dpi=300)
    plt.close()
    
    print(f"\nGráficos salvos em: {output_dir}")

def generate_report_data(df):
    """Gera dados para o relatório"""
    report = {
        'total_tests': len(df),
        'algorithms_tested': sorted(df['algorithm'].unique()),
        'conditions_tested': sorted(df['test_type'].unique()),
        'timestamp': df['timestamp'].iloc[0] if not df.empty else 'N/A'
    }
    
    # Melhor desempenho geral
    best_idx = df['throughput_mbps'].idxmax()
    best = df.loc[best_idx]
    report['best_performance'] = {
        'algorithm': best['algorithm'],
        'test_type': best['test_type'],
        'throughput_mbps': best['throughput_mbps']
    }
    
    # Algoritmo mais estável (menor desvio padrão)
    stability = df.groupby('algorithm')['throughput_mbps'].std()
    most_stable = stability.idxmin()
    report['most_stable'] = most_stable
    
    return report

def main():
    print("=== Análise Completa - Atividade 2 ===\n")
    
    # Carregar dados
    df = load_results()
    
    if df.empty:
        print("Nenhum resultado encontrado!")
        return
    
    # Análises
    algo_stats = analyze_algorithms(df)
    impact_stats = analyze_conditions(df)
    
    # Visualizações
    output_dir = Path("/results/atv2/results/plots")
    create_visualizations(df, output_dir)
    
    # Salvar dados processados
    processed_dir = Path("/results/atv2/results/processed")
    processed_dir.mkdir(exist_ok=True)
    
    df.to_csv(processed_dir / "complete_results.csv", index=False)
    algo_stats.to_csv(processed_dir / "algorithm_stats.csv")
    if not impact_stats.empty:
        impact_stats.to_csv(processed_dir / "impact_analysis.csv", index=False)
    
    # Gerar dados do relatório
    report_data = generate_report_data(df)
    
    print("\n=== Resumo Final ===")
    print(f"Total de testes: {report_data['total_tests']}")
    print(f"Algoritmos testados: {', '.join(report_data['algorithms_tested'])}")
    print(f"Condições testadas: {', '.join(report_data['conditions_tested'])}")
    print(f"\nMelhor desempenho: {report_data['best_performance']['algorithm'].upper()} "
          f"({report_data['best_performance']['throughput_mbps']:.1f} Mbps)")
    print(f"Algoritmo mais estável: {report_data['most_stable'].upper()}")
    
    print("\n✓ Análise concluída!")

if __name__ == "__main__":
    main()