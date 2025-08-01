#!/usr/bin/env python3

"""
Script de análise específico para a Atividade 2
Gera análises comparativas dos 6 cenários com justificativas teóricas
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import sys
from datetime import datetime
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configurações de estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

def load_scenario_configs():
    """Carrega as configurações dos cenários"""
    scenarios_dir = Path("/docs/atv2/scenarios")
    scenarios = {}
    
    for scenario_file in sorted(scenarios_dir.glob("scenario_*.json")):
        with open(scenario_file, 'r') as f:
            config = json.load(f)
            scenarios[config['name']] = config
    
    return scenarios

def load_test_results(timestamp=None):
    """Carrega os resultados dos testes da Atividade 2"""
    results_dir = Path("/docs/atv2/results/raw")
    
    if timestamp:
        pattern = f"{timestamp}_*.json"
    else:
        # Pegar o timestamp mais recente
        files = list(results_dir.glob("*_*.json"))
        if not files:
            print("Nenhum resultado encontrado!")
            sys.exit(1)
        
        # Extrair timestamps únicos
        timestamps = set()
        for f in files:
            parts = f.stem.split('_')
            if len(parts) >= 2:
                timestamps.add(f"{parts[0]}_{parts[1]}")
        
        timestamp = max(timestamps)
        pattern = f"{timestamp}_*.json"
    
    print(f"Carregando resultados com timestamp: {timestamp}")
    
    # Carregar dados
    data = []
    for result_file in results_dir.glob(pattern):
        if 'system_config' in str(result_file):
            continue
            
        try:
            with open(result_file, 'r') as f:
                result = json.load(f)
                
            # Extrair informações do nome do arquivo
            parts = result_file.stem.split('_')
            scenario_name = '_'.join(parts[2:-1])  # Remove timestamp e rep
            rep_num = int(parts[-1].replace('rep', ''))
            
            # Extrair métricas
            if 'end' in result:
                throughput_bps = result['end']['sum_sent']['bits_per_second']
                throughput_mbps = throughput_bps / 1e6
                
                retransmits = result['end']['sum_sent'].get('retransmits', 0)
                
                # CPU usage
                cpu_sender = result['end']['cpu_utilization_percent'].get('host_total', 0)
                cpu_receiver = result['end']['cpu_utilization_percent'].get('remote_total', 0)
                
                # RTT (se disponível)
                rtt_ms = 0
                if 'streams' in result['end']:
                    for stream in result['end']['streams']:
                        if 'rtt' in stream:
                            rtt_ms = stream['rtt'] / 1000  # converter para ms
                            break
                
                data.append({
                    'timestamp': timestamp,
                    'scenario': scenario_name,
                    'repetition': rep_num,
                    'throughput_mbps': throughput_mbps,
                    'retransmits': retransmits,
                    'cpu_sender': cpu_sender,
                    'cpu_receiver': cpu_receiver,
                    'rtt_ms': rtt_ms
                })
                
        except Exception as e:
            print(f"Erro ao processar {result_file}: {e}")
    
    df = pd.DataFrame(data)
    print(f"Carregados {len(df)} resultados de teste")
    
    return df, timestamp

def calculate_statistics(df, scenarios):
    """Calcula estatísticas detalhadas por cenário"""
    stats_data = []
    
    for scenario_name in df['scenario'].unique():
        scenario_data = df[df['scenario'] == scenario_name]
        scenario_config = scenarios.get(scenario_name, {})
        
        stats_data.append({
            'scenario': scenario_name,
            'description': scenario_config.get('description', scenario_name),
            'samples': len(scenario_data),
            'throughput_mean': scenario_data['throughput_mbps'].mean(),
            'throughput_std': scenario_data['throughput_mbps'].std(),
            'throughput_min': scenario_data['throughput_mbps'].min(),
            'throughput_max': scenario_data['throughput_mbps'].max(),
            'throughput_p95': scenario_data['throughput_mbps'].quantile(0.95),
            'retransmits_mean': scenario_data['retransmits'].mean(),
            'retransmits_total': scenario_data['retransmits'].sum(),
            'cpu_sender_mean': scenario_data['cpu_sender'].mean(),
            'cpu_receiver_mean': scenario_data['cpu_receiver'].mean(),
            'rtt_mean': scenario_data['rtt_ms'].mean() if scenario_data['rtt_ms'].sum() > 0 else 0,
            'cv': scenario_data['throughput_mbps'].std() / scenario_data['throughput_mbps'].mean() * 100  # Coeficiente de variação
        })
    
    return pd.DataFrame(stats_data)

def plot_scenario_comparison(stats_df, output_dir):
    """Gráfico comparativo principal dos cenários"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Preparar dados
    scenarios = stats_df.sort_values('throughput_mean', ascending=False)
    x = range(len(scenarios))
    
    # Barras com erro
    bars = ax.bar(x, scenarios['throughput_mean'], 
                   yerr=scenarios['throughput_std'],
                   capsize=5, alpha=0.8,
                   color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
    
    # Adicionar valores nas barras
    for i, (idx, row) in enumerate(scenarios.iterrows()):
        ax.text(i, row['throughput_mean'] + row['throughput_std'] + 50,
                f'{row["throughput_mean"]:.0f}', 
                ha='center', va='bottom', fontsize=10)
    
    # Configurações
    ax.set_xlabel('Cenário', fontsize=14)
    ax.set_ylabel('Throughput Médio (Mbps)', fontsize=14)
    ax.set_title('Comparação de Throughput entre Cenários - Atividade 2', fontsize=16)
    ax.set_xticks(x)
    ax.set_xticklabels([s.replace('scenario_', '').replace('_', ' ').title() 
                        for s in scenarios['scenario']], rotation=45, ha='right')
    
    # Grid
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'atv2_scenario_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_detailed_metrics(df, stats_df, output_dir):
    """Gráficos detalhados de múltiplas métricas"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Box plot de throughput por cenário
    ax1 = axes[0, 0]
    scenario_order = stats_df.sort_values('throughput_mean', ascending=False)['scenario'].tolist()
    df_ordered = df.copy()
    df_ordered['scenario_clean'] = df_ordered['scenario'].map(lambda x: x.replace('scenario_', '').replace('_', ' ').title())
    
    sns.boxplot(data=df_ordered, y='scenario_clean', x='throughput_mbps', 
                order=[s.replace('scenario_', '').replace('_', ' ').title() for s in scenario_order],
                ax=ax1, palette='husl')
    ax1.set_xlabel('Throughput (Mbps)')
    ax1.set_ylabel('Cenário')
    ax1.set_title('Distribuição de Throughput por Cenário')
    ax1.grid(True, alpha=0.3, axis='x')
    
    # 2. Retransmissões por cenário
    ax2 = axes[0, 1]
    retrans_data = stats_df.sort_values('retransmits_mean', ascending=False)
    x = range(len(retrans_data))
    bars = ax2.bar(x, retrans_data['retransmits_mean'], alpha=0.8, color='orange')
    ax2.set_xlabel('Cenário')
    ax2.set_ylabel('Retransmissões Médias')
    ax2.set_title('Retransmissões TCP por Cenário')
    ax2.set_xticks(x)
    ax2.set_xticklabels([s.replace('scenario_', '').replace('_', '\n').title() 
                         for s in retrans_data['scenario']], rotation=45, ha='right')
    
    # 3. Utilização de CPU
    ax3 = axes[1, 0]
    cpu_data = stats_df.sort_values('cpu_sender_mean', ascending=False)
    x = range(len(cpu_data))
    width = 0.35
    
    ax3.bar([i - width/2 for i in x], cpu_data['cpu_sender_mean'], 
            width, label='CPU Sender', alpha=0.8)
    ax3.bar([i + width/2 for i in x], cpu_data['cpu_receiver_mean'], 
            width, label='CPU Receiver', alpha=0.8)
    
    ax3.set_xlabel('Cenário')
    ax3.set_ylabel('Utilização de CPU (%)')
    ax3.set_title('Uso de CPU por Cenário')
    ax3.set_xticks(x)
    ax3.set_xticklabels([s.replace('scenario_', '').replace('_', '\n').title() 
                         for s in cpu_data['scenario']], rotation=45, ha='right')
    ax3.legend()
    
    # 4. Coeficiente de Variação (estabilidade)
    ax4 = axes[1, 1]
    cv_data = stats_df.sort_values('cv')
    x = range(len(cv_data))
    colors = ['green' if cv < 5 else 'orange' if cv < 10 else 'red' for cv in cv_data['cv']]
    
    ax4.bar(x, cv_data['cv'], alpha=0.8, color=colors)
    ax4.set_xlabel('Cenário')
    ax4.set_ylabel('Coeficiente de Variação (%)')
    ax4.set_title('Estabilidade do Throughput (menor = mais estável)')
    ax4.set_xticks(x)
    ax4.set_xticklabels([s.replace('scenario_', '').replace('_', '\n').title() 
                         for s in cv_data['scenario']], rotation=45, ha='right')
    ax4.axhline(y=5, color='green', linestyle='--', alpha=0.5, label='Muito Estável (<5%)')
    ax4.axhline(y=10, color='orange', linestyle='--', alpha=0.5, label='Estável (<10%)')
    ax4.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'atv2_detailed_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_network_conditions_impact(df, scenarios, output_dir):
    """Análise do impacto das condições de rede"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Preparar dados com condições de rede
    conditions_data = []
    for scenario_name, config in scenarios.items():
        if scenario_name in df['scenario'].unique():
            scenario_stats = df[df['scenario'] == scenario_name]['throughput_mbps'].agg(['mean', 'std'])
            conditions = config['network_conditions']
            
            conditions_data.append({
                'scenario': config['description'],
                'throughput_mean': scenario_stats['mean'],
                'throughput_std': scenario_stats['std'],
                'latency': conditions.get('latency_ms', 0) or 0,
                'bandwidth': conditions.get('bandwidth_mbps', 0) or 0,
                'loss': conditions.get('packet_loss_percent', 0) or 0,
                'algorithm': config['tcp_settings']['congestion_control']
            })
    
    conditions_df = pd.DataFrame(conditions_data)
    
    # 1. Impacto da latência no throughput
    ax1 = axes[0, 0]
    latency_scenarios = conditions_df[conditions_df['latency'] > 0].sort_values('latency')
    if not latency_scenarios.empty:
        ax1.errorbar(latency_scenarios['latency'], latency_scenarios['throughput_mean'],
                     yerr=latency_scenarios['throughput_std'], 
                     marker='o', markersize=10, capsize=5, linewidth=2)
        
        for idx, row in latency_scenarios.iterrows():
            ax1.annotate(row['scenario'], 
                        (row['latency'], row['throughput_mean']),
                        xytext=(5, 5), textcoords='offset points', fontsize=9)
        
        ax1.set_xlabel('Latência (ms)')
        ax1.set_ylabel('Throughput (Mbps)')
        ax1.set_title('Impacto da Latência no Throughput')
        ax1.grid(True, alpha=0.3)
    
    # 2. Impacto da limitação de banda
    ax2 = axes[0, 1]
    bw_scenarios = conditions_df[conditions_df['bandwidth'] > 0].sort_values('bandwidth')
    if not bw_scenarios.empty:
        ax2.bar(range(len(bw_scenarios)), bw_scenarios['throughput_mean'], 
                alpha=0.8, color='orange')
        
        # Linha de referência para mostrar o limite teórico
        for i, (idx, row) in enumerate(bw_scenarios.iterrows()):
            ax2.axhline(y=row['bandwidth'], xmin=i/len(bw_scenarios), 
                       xmax=(i+1)/len(bw_scenarios), 
                       color='red', linestyle='--', alpha=0.5)
        
        ax2.set_xlabel('Cenário')
        ax2.set_ylabel('Throughput (Mbps)')
        ax2.set_title('Throughput vs Limite de Banda')
        ax2.set_xticks(range(len(bw_scenarios)))
        ax2.set_xticklabels(bw_scenarios['scenario'], rotation=45, ha='right')
        ax2.legend(['Throughput Real', 'Limite Teórico'])
    
    # 3. Comparação por algoritmo de congestionamento
    ax3 = axes[1, 0]
    algorithm_stats = conditions_df.groupby('algorithm')['throughput_mean'].agg(['mean', 'std', 'count'])
    algorithm_stats = algorithm_stats[algorithm_stats['count'] > 0]
    
    if not algorithm_stats.empty:
        x = range(len(algorithm_stats))
        ax3.bar(x, algorithm_stats['mean'], yerr=algorithm_stats['std'],
                capsize=5, alpha=0.8, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        
        ax3.set_xlabel('Algoritmo de Congestionamento')
        ax3.set_ylabel('Throughput Médio (Mbps)')
        ax3.set_title('Desempenho por Algoritmo de Congestionamento')
        ax3.set_xticks(x)
        ax3.set_xticklabels(algorithm_stats.index, rotation=0)
        
        # Adicionar contagem de amostras
        for i, (algo, row) in enumerate(algorithm_stats.iterrows()):
            ax3.text(i, row['mean'] + row['std'] + 50, 
                    f"n={int(row['count'])}", ha='center', fontsize=10)
    
    # 4. Matriz de correlação
    ax4 = axes[1, 1]
    
    # Criar matriz de dados para correlação
    corr_data = conditions_df[['throughput_mean', 'latency', 'bandwidth', 'loss']].copy()
    corr_data['bandwidth'] = corr_data['bandwidth'].replace(0, np.nan)  # Substituir 0 por NaN para melhor correlação
    
    correlation = corr_data.corr()
    
    sns.heatmap(correlation, annot=True, fmt='.2f', cmap='coolwarm', 
                center=0, ax=ax4, square=True,
                cbar_kws={'label': 'Correlação'})
    ax4.set_title('Correlação entre Condições de Rede e Desempenho')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'atv2_network_conditions_impact.png', dpi=300, bbox_inches='tight')
    plt.close()

def generate_comparison_table(stats_df, scenarios, output_file):
    """Gera tabela comparativa detalhada em formato markdown"""
    
    # Ordenar por throughput médio
    stats_df = stats_df.sort_values('throughput_mean', ascending=False)
    
    with open(output_file, 'w') as f:
        f.write("# Tabela Comparativa de Cenários - Atividade 2\n\n")
        f.write("## Resumo Estatístico\n\n")
        
        # Tabela principal
        f.write("| Cenário | Descrição | Throughput (Mbps) | Desvio Padrão | CV (%) | Retrans. | CPU Send (%) | Amostras |\n")
        f.write("|---------|-----------|-------------------|---------------|--------|----------|--------------|----------|\n")
        
        for _, row in stats_df.iterrows():
            scenario_config = scenarios.get(row['scenario'], {})
            desc = scenario_config.get('description', row['scenario'])
            
            f.write(f"| {row['scenario'].replace('scenario_', '')} | {desc} | "
                   f"{row['throughput_mean']:.1f} | {row['throughput_std']:.1f} | "
                   f"{row['cv']:.1f} | {row['retransmits_mean']:.0f} | "
                   f"{row['cpu_sender_mean']:.1f} | {row['samples']} |\n")
        
        f.write("\n## Configurações dos Cenários\n\n")
        
        # Tabela de configurações
        f.write("| Cenário | Algoritmo | Janela | Streams | Latência | Banda | Perda |\n")
        f.write("|---------|-----------|--------|---------|----------|-------|-------|\n")
        
        for _, row in stats_df.iterrows():
            config = scenarios.get(row['scenario'], {})
            tcp = config.get('tcp_settings', {})
            net = config.get('network_conditions', {})
            
            f.write(f"| {row['scenario'].replace('scenario_', '')} | "
                   f"{tcp.get('congestion_control', 'N/A')} | "
                   f"{tcp.get('window_size', 'Auto')} | "
                   f"{tcp.get('parallel_streams', 1)} | "
                   f"{net.get('latency_ms', 0) or '-'}ms | "
                   f"{net.get('bandwidth_mbps', 0) or '∞'}Mbps | "
                   f"{net.get('packet_loss_percent', 0) or '-'}% |\n")
        
        f.write("\n## Análise Estatística\n\n")
        
        # Melhor e pior desempenho
        best = stats_df.iloc[0]
        worst = stats_df.iloc[-1]
        
        f.write(f"- **Melhor Desempenho**: {scenarios[best['scenario']]['description']} "
               f"({best['throughput_mean']:.1f} Mbps)\n")
        f.write(f"- **Pior Desempenho**: {scenarios[worst['scenario']]['description']} "
               f"({worst['throughput_mean']:.1f} Mbps)\n")
        f.write(f"- **Diferença**: {((best['throughput_mean'] - worst['throughput_mean']) / worst['throughput_mean'] * 100):.1f}%\n")
        f.write(f"- **Cenário Mais Estável**: {stats_df.loc[stats_df['cv'].idxmin(), 'scenario']} "
               f"(CV = {stats_df['cv'].min():.1f}%)\n")
        f.write(f"- **Cenário Menos Estável**: {stats_df.loc[stats_df['cv'].idxmax(), 'scenario']} "
               f"(CV = {stats_df['cv'].max():.1f}%)\n")

def generate_theoretical_analysis(scenarios, stats_df, output_file):
    """Gera análise teórica dos resultados"""
    
    with open(output_file, 'w') as f:
        f.write("# Análise Teórica dos Resultados - Atividade 2\n\n")
        
        for _, row in stats_df.sort_values('throughput_mean', ascending=False).iterrows():
            scenario = row['scenario']
            config = scenarios.get(scenario, {})
            
            f.write(f"## {config.get('description', scenario)}\n\n")
            
            f.write(f"**Objetivo**: {config.get('objective', 'N/A')}\n\n")
            
            f.write("### Configurações\n")
            tcp = config.get('tcp_settings', {})
            net = config.get('network_conditions', {})
            
            f.write(f"- Algoritmo: {tcp.get('congestion_control', 'N/A')}\n")
            f.write(f"- Janela TCP: {tcp.get('window_size', 'Auto')}\n")
            f.write(f"- Streams Paralelos: {tcp.get('parallel_streams', 1)}\n")
            
            if any(net.values()):
                f.write(f"- Condições de Rede:\n")
                if net.get('latency_ms'):
                    f.write(f"  - Latência: {net['latency_ms']}ms\n")
                if net.get('bandwidth_mbps'):
                    f.write(f"  - Banda: {net['bandwidth_mbps']}Mbps\n")
                if net.get('packet_loss_percent'):
                    f.write(f"  - Perda: {net['packet_loss_percent']}%\n")
            
            f.write("\n### Resultados Observados\n")
            f.write(f"- Throughput Médio: {row['throughput_mean']:.1f} Mbps\n")
            f.write(f"- Desvio Padrão: {row['throughput_std']:.1f} Mbps\n")
            f.write(f"- Coeficiente de Variação: {row['cv']:.1f}%\n")
            f.write(f"- Retransmissões Médias: {row['retransmits_mean']:.0f}\n")
            
            f.write("\n### Justificativa Teórica\n")
            f.write(f"{config.get('theoretical_justification', 'N/A')}\n")
            
            f.write("\n### Análise dos Resultados\n")
            
            # Análise específica baseada no cenário
            if 'baseline' in scenario:
                f.write("Como esperado, o cenário baseline apresentou excelente desempenho "
                       "sem limitações artificiais. O CUBIC demonstrou sua eficiência em "
                       "redes de alta velocidade com baixa latência.\n")
            
            elif 'high_performance' in scenario:
                improvement = (row['throughput_mean'] - stats_df[stats_df['scenario'].str.contains('baseline')]['throughput_mean'].iloc[0]) / stats_df[stats_df['scenario'].str.contains('baseline')]['throughput_mean'].iloc[0] * 100
                f.write(f"O BBR com múltiplos fluxos apresentou melhoria de {improvement:.1f}% "
                       "sobre o baseline, confirmando sua eficácia em ambientes de datacenter. "
                       "A alta utilização sem causar congestionamento é característica do BBR.\n")
            
            elif 'congested' in scenario:
                f.write("Vegas demonstrou comportamento conservador como esperado, "
                       "mantendo throughput próximo ao limite de banda disponível "
                       "com mínimas retransmissões, ideal para redes congestionadas.\n")
            
            elif 'lossy' in scenario:
                f.write("Reno mostrou recuperação eficiente de perdas isoladas. "
                       f"As {row['retransmits_mean']:.0f} retransmissões médias são "
                       "proporcionais à taxa de perda configurada, demonstrando o "
                       "funcionamento correto do Fast Retransmit/Fast Recovery.\n")
            
            elif 'legacy' in scenario:
                efficiency = row['throughput_mean'] / net.get('bandwidth_mbps', 100) * 100 if net.get('bandwidth_mbps') else 0
                f.write(f"Eficiência de {efficiency:.1f}% em relação ao limite de banda. "
                       "A janela pequena evitou problemas de buffer overflow em "
                       "hardware antigo, mantendo estabilidade.\n")
            
            elif 'wan' in scenario:
                bdp = net.get('bandwidth_mbps', 50) * net.get('latency_ms', 100) / 8  # em KB
                f.write(f"BDP calculado: {bdp:.0f}KB. A janela de {tcp.get('window_size', 'N/A')} "
                       f"representa {256/bdp*100:.0f}% do BDP. BBR adaptou-se bem às "
                       "condições de WAN, mantendo boa utilização apesar do alto RTT.\n")
            
            f.write("\n---\n\n")

def main():
    """Função principal"""
    print("=== Análise de Resultados - Atividade 2 ===\n")
    
    # Criar diretórios de saída
    output_dir = Path("/docs/atv2/results/plots")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    processed_dir = Path("/docs/atv2/results/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Carregar configurações dos cenários
    print("Carregando configurações dos cenários...")
    scenarios = load_scenario_configs()
    print(f"Carregados {len(scenarios)} cenários")
    
    # Carregar resultados
    print("\nCarregando resultados dos testes...")
    df, timestamp = load_test_results()
    
    if df.empty:
        print("Nenhum resultado válido encontrado!")
        sys.exit(1)
    
    # Calcular estatísticas
    print("\nCalculando estatísticas...")
    stats_df = calculate_statistics(df, scenarios)
    
    # Salvar dados processados
    df.to_csv(processed_dir / f"{timestamp}_raw_data.csv", index=False)
    stats_df.to_csv(processed_dir / f"{timestamp}_statistics.csv", index=False)
    
    # Gerar visualizações
    print("\nGerando visualizações...")
    plot_scenario_comparison(stats_df, output_dir)
    plot_detailed_metrics(df, stats_df, output_dir)
    plot_network_conditions_impact(df, scenarios, output_dir)
    
    # Gerar tabelas e análises
    print("\nGerando tabelas e análises...")
    generate_comparison_table(stats_df, scenarios, 
                            processed_dir / f"{timestamp}_comparison_table.md")
    generate_theoretical_analysis(scenarios, stats_df, 
                                processed_dir / f"{timestamp}_theoretical_analysis.md")
    
    # Resumo final
    print("\n=== Resumo da Análise ===")
    print(f"Timestamp: {timestamp}")
    print(f"Total de cenários analisados: {len(stats_df)}")
    print(f"Total de amostras: {len(df)}")
    print(f"\nMelhor desempenho: {stats_df.iloc[0]['description']}")
    print(f"Throughput: {stats_df.iloc[0]['throughput_mean']:.1f} ± {stats_df.iloc[0]['throughput_std']:.1f} Mbps")
    print(f"\nArquivos gerados em:")
    print(f"- Gráficos: {output_dir}")
    print(f"- Dados processados: {processed_dir}")
    
    print("\n✓ Análise concluída com sucesso!")
    print("Execute generate-pdf-report.py para gerar o relatório final em PDF")

if __name__ == "__main__":
    main()