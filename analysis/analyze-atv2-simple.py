#!/usr/bin/env python3

"""
Script simplificado de análise para os resultados da Atividade 2
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import sys

# Configurações de estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_results(timestamp="20250801_022946"):
    """Carrega os resultados dos testes"""
    results_dir = Path("/results/atv2/results/raw")
    
    print(f"Carregando resultados com timestamp: {timestamp}")
    
    data = []
    for result_file in results_dir.glob(f"{timestamp}_*.json"):
        if 'system_config' in str(result_file):
            continue
            
        try:
            with open(result_file, 'r') as f:
                result = json.load(f)
            
            # Extrair informações do nome
            parts = result_file.stem.split('_')
            if len(parts) >= 3:
                scenario = '_'.join(parts[2:-1])
                rep = int(parts[-1].replace('rep', ''))
                
                # Extrair métricas
                if 'end' in result and 'sum_sent' in result['end']:
                    throughput_bps = result['end']['sum_sent']['bits_per_second']
                    throughput_mbps = throughput_bps / 1e6
                    
                    retransmits = result['end']['sum_sent'].get('retransmits', 0)
                    
                    data.append({
                        'scenario': scenario,
                        'repetition': rep,
                        'throughput_mbps': throughput_mbps,
                        'retransmits': retransmits
                    })
                    
        except Exception as e:
            print(f"Erro ao processar {result_file}: {e}")
    
    df = pd.DataFrame(data)
    return df

def analyze_results(df):
    """Analisa e imprime resultados"""
    print("\n=== Análise dos Resultados ===\n")
    
    # Estatísticas por cenário
    stats = df.groupby('scenario')['throughput_mbps'].agg(['mean', 'std', 'count'])
    stats['retransmits_mean'] = df.groupby('scenario')['retransmits'].mean()
    
    print("Estatísticas por Cenário:")
    print("-" * 80)
    print(f"{'Cenário':<20} {'Throughput (Mbps)':<20} {'Desvio Padrão':<15} {'Retransmissões':<15}")
    print("-" * 80)
    
    for scenario, row in stats.iterrows():
        print(f"{scenario:<20} {row['mean']:>15.1f}      {row['std']:>10.1f}      {row['retransmits_mean']:>10.0f}")
    
    return stats

def create_simple_plot(stats, output_dir):
    """Cria gráfico simples de comparação"""
    plt.figure(figsize=(12, 8))
    
    scenarios = stats.index
    throughputs = stats['mean']
    errors = stats['std']
    
    # Cores diferentes para cada cenário
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    bars = plt.bar(range(len(scenarios)), throughputs, yerr=errors, 
                    capsize=5, alpha=0.8, color=colors[:len(scenarios)])
    
    # Adicionar valores nas barras
    for i, (scenario, throughput) in enumerate(zip(scenarios, throughputs)):
        plt.text(i, throughput + errors.iloc[i] + 100, f'{throughput:.0f}', 
                ha='center', va='bottom')
    
    plt.xlabel('Cenário', fontsize=14)
    plt.ylabel('Throughput Médio (Mbps)', fontsize=14)
    plt.title('Comparação de Throughput - Atividade 2', fontsize=16)
    plt.xticks(range(len(scenarios)), scenarios, rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'atv2_throughput_comparison.png', dpi=300)
    plt.close()
    
    print(f"\nGráfico salvo em: {output_dir / 'atv2_throughput_comparison.png'}")

def main():
    """Função principal"""
    print("=== Análise Simplificada - Atividade 2 ===")
    
    # Carregar resultados
    df = load_results()
    
    if df.empty:
        print("Nenhum resultado encontrado!")
        return
    
    print(f"\nTotal de amostras carregadas: {len(df)}")
    print(f"Cenários encontrados: {', '.join(df['scenario'].unique())}")
    
    # Analisar
    stats = analyze_results(df)
    
    # Criar diretório de saída
    output_dir = Path("/results/atv2/results/plots")
    output_dir.mkdir(exist_ok=True)
    
    # Gerar gráfico
    create_simple_plot(stats, output_dir)
    
    # Salvar estatísticas
    stats_file = Path("/results/atv2/results/processed/statistics_simple.csv")
    stats_file.parent.mkdir(exist_ok=True)
    stats.to_csv(stats_file)
    print(f"\nEstatísticas salvas em: {stats_file}")
    
    # Análise comparativa
    print("\n=== Análise Comparativa ===")
    print("\nMelhor desempenho:", stats['mean'].idxmax())
    print(f"Throughput: {stats['mean'].max():.1f} Mbps")
    
    print("\nPior desempenho:", stats['mean'].idxmin())
    print(f"Throughput: {stats['mean'].min():.1f} Mbps")
    
    # Impacto das condições
    baseline = stats.loc['baseline', 'mean'] if 'baseline' in stats.index else stats['mean'].max()
    
    print("\n=== Impacto das Condições de Rede ===")
    for scenario, row in stats.iterrows():
        if scenario != 'baseline':
            impact = (row['mean'] - baseline) / baseline * 100
            print(f"{scenario}: {impact:+.1f}% vs baseline")

if __name__ == "__main__":
    main()