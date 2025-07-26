#!/usr/bin/env python3

"""
Script de análise e visualização dos resultados dos testes de desempenho TCP
Gera gráficos comparativos e identifica a configuração ótima
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import sys
from datetime import datetime

# Configurações de estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_results(timestamp=None):
    """Carrega os resultados processados do CSV"""
    processed_dir = Path("/results/processed")
    
    if timestamp:
        csv_file = processed_dir / f"{timestamp}_results.csv"
    else:
        # Pegar o arquivo mais recente
        csv_files = list(processed_dir.glob("*_results.csv"))
        if not csv_files:
            print("Nenhum arquivo de resultados encontrado!")
            sys.exit(1)
        csv_file = max(csv_files, key=lambda x: x.stat().st_mtime)
    
    print(f"Carregando resultados de: {csv_file}")
    df = pd.read_csv(csv_file)
    
    # Filtrar erros
    df = df[df['throughput_mbps'] != 'ERROR']
    df['throughput_mbps'] = pd.to_numeric(df['throughput_mbps'])
    
    return df

def categorize_tests(df):
    """Categoriza os testes por tipo"""
    df['category'] = 'outros'
    
    # Categorizar por nome do teste
    df.loc[df['test_name'].str.contains('baseline'), 'category'] = 'baseline'
    df.loc[df['test_name'].str.contains('window'), 'category'] = 'window_size'
    df.loc[df['test_name'].str.contains('streams'), 'category'] = 'parallel_streams'
    df.loc[df['test_name'].str.contains('cc_'), 'category'] = 'congestion_control'
    df.loc[df['test_name'].str.contains('latency'), 'category'] = 'network_latency'
    df.loc[df['test_name'].str.contains('bandwidth'), 'category'] = 'bandwidth_limit'
    df.loc[df['test_name'].str.contains('packet_loss'), 'category'] = 'packet_loss'
    df.loc[df['test_name'].str.contains('combined'), 'category'] = 'combined'
    
    return df

def plot_throughput_comparison(df, output_dir):
    """Gráfico comparativo de throughput por categoria"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Agrupar por teste e calcular média e desvio padrão
    summary = df.groupby(['category', 'test_name'])['throughput_mbps'].agg(['mean', 'std']).reset_index()
    
    # Plotar por categoria
    categories = summary['category'].unique()
    x_pos = 0
    x_ticks = []
    x_labels = []
    
    for cat in categories:
        cat_data = summary[summary['category'] == cat]
        positions = range(x_pos, x_pos + len(cat_data))
        
        ax.bar(positions, cat_data['mean'], yerr=cat_data['std'], 
               capsize=5, alpha=0.7, label=cat.replace('_', ' ').title())
        
        x_ticks.extend(positions)
        x_labels.extend(cat_data['test_name'])
        x_pos += len(cat_data) + 1
    
    ax.set_xlabel('Cenário de Teste')
    ax.set_ylabel('Throughput (Mbps)')
    ax.set_title('Comparação de Throughput por Cenário')
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_labels, rotation=45, ha='right')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'throughput_comparison.png', dpi=300)
    plt.close()

def plot_window_size_analysis(df, output_dir):
    """Análise específica do impacto do tamanho da janela TCP"""
    window_data = df[df['category'] == 'window_size'].copy()
    
    if window_data.empty:
        return
    
    # Extrair tamanho da janela do nome do teste
    window_data['window_kb'] = window_data['test_name'].str.extract(r'window_(\d+)').astype(int)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Throughput vs Window Size
    summary = window_data.groupby('window_kb')['throughput_mbps'].agg(['mean', 'std']).reset_index()
    ax1.errorbar(summary['window_kb'], summary['mean'], yerr=summary['std'], 
                 marker='o', markersize=8, capsize=5, linewidth=2)
    ax1.set_xlabel('Tamanho da Janela TCP (KB)')
    ax1.set_ylabel('Throughput (Mbps)')
    ax1.set_title('Impacto do Tamanho da Janela TCP no Throughput')
    ax1.grid(True, alpha=0.3)
    
    # Retransmissões vs Window Size
    retrans = window_data.groupby('window_kb')['retransmits'].mean().reset_index()
    ax2.bar(retrans['window_kb'], retrans['retransmits'], alpha=0.7, color='orange')
    ax2.set_xlabel('Tamanho da Janela TCP (KB)')
    ax2.set_ylabel('Retransmissões Médias')
    ax2.set_title('Retransmissões por Tamanho de Janela')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'window_size_analysis.png', dpi=300)
    plt.close()

def plot_parallel_streams_analysis(df, output_dir):
    """Análise do impacto de fluxos paralelos"""
    streams_data = df[df['category'] == 'parallel_streams'].copy()
    
    if streams_data.empty:
        return
    
    # Extrair número de streams
    streams_data['num_streams'] = streams_data['test_name'].str.extract(r'streams_(\d+)').astype(int)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Throughput vs Streams
    summary = streams_data.groupby('num_streams')['throughput_mbps'].agg(['mean', 'std']).reset_index()
    ax1.errorbar(summary['num_streams'], summary['mean'], yerr=summary['std'], 
                 marker='s', markersize=8, capsize=5, linewidth=2, color='green')
    ax1.set_xlabel('Número de Fluxos Paralelos')
    ax1.set_ylabel('Throughput (Mbps)')
    ax1.set_title('Impacto de Fluxos Paralelos no Throughput')
    ax1.set_xticks([1, 2, 4, 8])
    ax1.grid(True, alpha=0.3)
    
    # CPU Usage vs Streams
    cpu_data = streams_data.groupby('num_streams')[['cpu_sender', 'cpu_receiver']].mean().reset_index()
    x = np.arange(len(cpu_data))
    width = 0.35
    
    ax2.bar(x - width/2, cpu_data['cpu_sender'], width, label='CPU Sender', alpha=0.7)
    ax2.bar(x + width/2, cpu_data['cpu_receiver'], width, label='CPU Receiver', alpha=0.7)
    ax2.set_xlabel('Número de Fluxos Paralelos')
    ax2.set_ylabel('Uso de CPU (%)')
    ax2.set_title('Uso de CPU por Número de Fluxos')
    ax2.set_xticks(x)
    ax2.set_xticklabels(cpu_data['num_streams'])
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'parallel_streams_analysis.png', dpi=300)
    plt.close()

def plot_congestion_control_comparison(df, output_dir):
    """Comparação entre algoritmos de controle de congestionamento"""
    cc_data = df[df['category'] == 'congestion_control'].copy()
    
    if cc_data.empty:
        return
    
    # Extrair algoritmo
    cc_data['algorithm'] = cc_data['test_name'].str.extract(r'cc_(.+)')
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Box plot para mostrar distribuição
    cc_data.boxplot(column='throughput_mbps', by='algorithm', ax=ax)
    ax.set_xlabel('Algoritmo de Controle de Congestionamento')
    ax.set_ylabel('Throughput (Mbps)')
    ax.set_title('Comparação de Algoritmos de Controle de Congestionamento')
    plt.suptitle('')  # Remover título automático do boxplot
    
    plt.tight_layout()
    plt.savefig(output_dir / 'congestion_control_comparison.png', dpi=300)
    plt.close()

def plot_network_conditions_impact(df, output_dir):
    """Impacto das condições de rede simuladas"""
    # Filtrar dados relevantes
    network_data = df[df['category'].isin(['network_latency', 'bandwidth_limit', 'packet_loss'])]
    
    if network_data.empty:
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.ravel()
    
    # 1. Impacto da latência
    latency_data = df[df['category'] == 'network_latency']
    if not latency_data.empty:
        lat_summary = latency_data.groupby('test_name')['throughput_mbps'].mean().reset_index()
        axes[0].bar(range(len(lat_summary)), lat_summary['throughput_mbps'], alpha=0.7)
        axes[0].set_xticks(range(len(lat_summary)))
        axes[0].set_xticklabels([x.replace('latency_', '') for x in lat_summary['test_name']])
        axes[0].set_xlabel('Latência Adicionada')
        axes[0].set_ylabel('Throughput (Mbps)')
        axes[0].set_title('Impacto da Latência')
    
    # 2. Impacto da limitação de banda
    bw_data = df[df['category'] == 'bandwidth_limit']
    if not bw_data.empty:
        bw_summary = bw_data.groupby('test_name')['throughput_mbps'].mean().reset_index()
        axes[1].bar(range(len(bw_summary)), bw_summary['throughput_mbps'], alpha=0.7, color='orange')
        axes[1].set_xticks(range(len(bw_summary)))
        axes[1].set_xticklabels([x.replace('bandwidth_', '') for x in bw_summary['test_name']])
        axes[1].set_xlabel('Limite de Banda')
        axes[1].set_ylabel('Throughput (Mbps)')
        axes[1].set_title('Impacto da Limitação de Banda')
    
    # 3. Impacto da perda de pacotes
    loss_data = df[df['category'] == 'packet_loss']
    if not loss_data.empty:
        loss_summary = loss_data.groupby('test_name')['throughput_mbps'].mean().reset_index()
        axes[2].bar(range(len(loss_summary)), loss_summary['throughput_mbps'], alpha=0.7, color='red')
        axes[2].set_xticks(range(len(loss_summary)))
        axes[2].set_xticklabels([x.replace('packet_loss_', '') for x in loss_summary['test_name']])
        axes[2].set_xlabel('Perda de Pacotes')
        axes[2].set_ylabel('Throughput (Mbps)')
        axes[2].set_title('Impacto da Perda de Pacotes')
    
    # 4. Comparação geral
    baseline_throughput = df[df['category'] == 'baseline']['throughput_mbps'].mean()
    categories = ['baseline', 'network_latency', 'bandwidth_limit', 'packet_loss']
    avg_throughputs = []
    
    for cat in categories:
        cat_data = df[df['category'] == cat]
        avg_throughputs.append(cat_data['throughput_mbps'].mean() if not cat_data.empty else 0)
    
    axes[3].bar(categories, avg_throughputs, alpha=0.7, color='green')
    axes[3].set_xlabel('Categoria')
    axes[3].set_ylabel('Throughput Médio (Mbps)')
    axes[3].set_title('Comparação de Condições de Rede')
    axes[3].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'network_conditions_impact.png', dpi=300)
    plt.close()

def identify_optimal_configuration(df):
    """Identifica a configuração ótima baseada em múltiplas métricas"""
    # Calcular score composto
    summary = df.groupby('test_name').agg({
        'throughput_mbps': 'mean',
        'retransmits': 'mean',
        'cpu_sender': 'mean',
        'cpu_receiver': 'mean',
        'rtt_ms': 'mean'
    }).reset_index()
    
    # Normalizar métricas (0-1)
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler()
    
    # Métricas onde maior é melhor
    summary['throughput_norm'] = scaler.fit_transform(summary[['throughput_mbps']])
    
    # Métricas onde menor é melhor (inverter)
    if summary['retransmits'].max() > 0:
        summary['retransmits_norm'] = 1 - scaler.fit_transform(summary[['retransmits']])
    else:
        summary['retransmits_norm'] = 1
    
    summary['cpu_norm'] = 1 - scaler.fit_transform(summary[['cpu_sender']])
    
    if summary['rtt_ms'].max() > 0:
        summary['rtt_norm'] = 1 - scaler.fit_transform(summary[['rtt_ms']])
    else:
        summary['rtt_norm'] = 1
    
    # Score composto (pesos podem ser ajustados)
    weights = {
        'throughput': 0.5,
        'retransmits': 0.2,
        'cpu': 0.2,
        'rtt': 0.1
    }
    
    summary['score'] = (
        weights['throughput'] * summary['throughput_norm'] +
        weights['retransmits'] * summary['retransmits_norm'] +
        weights['cpu'] * summary['cpu_norm'] +
        weights['rtt'] * summary['rtt_norm']
    )
    
    # Encontrar configuração ótima
    optimal = summary.loc[summary['score'].idxmax()]
    
    return optimal, summary

def generate_report_figures(df, output_dir):
    """Gera todas as figuras para o relatório"""
    print("Gerando visualizações...")
    
    # Criar diretório de saída
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Categorizar testes
    df = categorize_tests(df)
    
    # Gerar gráficos
    plot_throughput_comparison(df, output_dir)
    plot_window_size_analysis(df, output_dir)
    plot_parallel_streams_analysis(df, output_dir)
    plot_congestion_control_comparison(df, output_dir)
    plot_network_conditions_impact(df, output_dir)
    
    # Identificar configuração ótima
    optimal, scores = identify_optimal_configuration(df)
    
    # Salvar análise da configuração ótima
    with open(output_dir / 'optimal_configuration.txt', 'w') as f:
        f.write("=== CONFIGURAÇÃO ÓTIMA IDENTIFICADA ===\n\n")
        f.write(f"Teste: {optimal['test_name']}\n")
        f.write(f"Throughput médio: {optimal['throughput_mbps']:.2f} Mbps\n")
        f.write(f"Retransmissões médias: {optimal['retransmits']:.0f}\n")
        f.write(f"CPU Sender: {optimal['cpu_sender']:.2f}%\n")
        f.write(f"RTT médio: {optimal['rtt_ms']:.2f} ms\n")
        f.write(f"Score composto: {optimal['score']:.3f}\n\n")
        
        f.write("=== TOP 5 CONFIGURAÇÕES ===\n")
        top5 = scores.nlargest(5, 'score')[['test_name', 'throughput_mbps', 'score']]
        f.write(top5.to_string(index=False))
    
    print(f"Visualizações salvas em: {output_dir}")
    print(f"Configuração ótima: {optimal['test_name']} (Score: {optimal['score']:.3f})")

def main():
    """Função principal"""
    # Verificar argumentos
    timestamp = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Carregar dados
    df = load_results(timestamp)
    
    # Gerar análises
    output_dir = Path("/results/plots")
    generate_report_figures(df, output_dir)
    
    print("\nAnálise concluída com sucesso!")

if __name__ == "__main__":
    main()