#!/usr/bin/env python3

import json
import os
from pathlib import Path
from collections import defaultdict
import statistics

def analyze_final_results():
    results_dir = '/results/raw'
    files = list(Path(results_dir).glob('*.json'))
    
    print('=== ANÁLISE FINAL DOS RESULTADOS DE DESEMPENHO TCP ===\n')
    
    # Categorizar resultados
    categories = {
        'baseline': [],
        'window_64k': [],
        'window_128k': [],
        'window_256k': [],
        'window_512k': [],
        'streams_4': [],
        'combined': []
    }
    
    errors = []
    
    # Processar arquivos
    for f in files:
        try:
            with open(f, 'r') as file:
                data = json.load(file)
            
            if 'end' in data and 'sum_sent' in data['end']:
                throughput_gbps = data['end']['sum_sent'].get('bits_per_second', 0) / 1e9
                retrans = data['end']['sum_sent'].get('retransmits', 0)
                
                # Categorizar
                filename = f.name.lower()
                if 'baseline' in filename:
                    categories['baseline'].append((throughput_gbps, retrans))
                elif 'window_64k' in filename:
                    categories['window_64k'].append((throughput_gbps, retrans))
                elif 'window_128k' in filename:
                    categories['window_128k'].append((throughput_gbps, retrans))
                elif 'window_256k' in filename:
                    categories['window_256k'].append((throughput_gbps, retrans))
                elif 'window_512k' in filename:
                    categories['window_512k'].append((throughput_gbps, retrans))
                elif 'streams_4' in filename:
                    categories['streams_4'].append((throughput_gbps, retrans))
                elif 'combined' in filename:
                    categories['combined'].append((throughput_gbps, retrans))
                    
        except Exception as e:
            errors.append(f'{f.name}: {str(e)}')
    
    # Calcular estatísticas
    print('=== RESULTADOS POR CATEGORIA ===\n')
    print(f'{"Categoria":<20} {"Throughput Médio":<20} {"Desvio Padrão":<15} {"Retrans Médias":<15} {"Amostras":<10}')
    print('-' * 80)
    
    summary = {}
    
    for cat, results in categories.items():
        if results:
            throughputs = [r[0] for r in results]
            retrans = [r[1] for r in results]
            
            avg_throughput = statistics.mean(throughputs)
            std_throughput = statistics.stdev(throughputs) if len(throughputs) > 1 else 0
            avg_retrans = statistics.mean(retrans)
            
            summary[cat] = {
                'avg': avg_throughput,
                'std': std_throughput,
                'retrans': avg_retrans,
                'count': len(results)
            }
            
            print(f'{cat:<20} {avg_throughput:<20.2f} {std_throughput:<15.2f} {avg_retrans:<15.1f} {len(results):<10}')
    
    # Análise comparativa
    print('\n=== ANÁLISE COMPARATIVA (% em relação ao baseline) ===\n')
    
    if 'baseline' in summary and summary['baseline']['avg'] > 0:
        baseline_avg = summary['baseline']['avg']
        
        comparisons = []
        for cat, stats in summary.items():
            if cat != 'baseline':
                improvement = ((stats['avg'] - baseline_avg) / baseline_avg) * 100
                comparisons.append((cat, stats['avg'], improvement))
        
        # Ordenar por melhoria
        comparisons.sort(key=lambda x: x[2], reverse=True)
        
        print(f'{"Configuração":<20} {"Throughput (Gbps)":<20} {"Melhoria (%)":<15}')
        print('-' * 55)
        
        for cat, throughput, improvement in comparisons:
            sign = '+' if improvement >= 0 else ''
            print(f'{cat:<20} {throughput:<20.2f} {sign}{improvement:<14.1f}')
    
    # Identificar configuração ótima
    print('\n=== CONFIGURAÇÃO ÓTIMA IDENTIFICADA ===\n')
    
    best_cat = max(summary.items(), key=lambda x: x[1]['avg'])
    print(f'Melhor configuração: {best_cat[0]}')
    print(f'Throughput médio: {best_cat[1]["avg"]:.2f} Gbps')
    print(f'Desvio padrão: {best_cat[1]["std"]:.2f} Gbps')
    print(f'Retransmissões médias: {best_cat[1]["retrans"]:.1f}')
    
    # Recomendações
    print('\n=== RECOMENDAÇÕES ===\n')
    
    if best_cat[0] == 'combined':
        print('1. A combinação de janela TCP otimizada com múltiplos fluxos oferece o melhor desempenho')
        print('2. Recomenda-se usar janela de 256KB com 4 fluxos paralelos')
    
    if 'window_64k' in summary and summary['window_64k']['avg'] < baseline_avg * 0.9:
        print('3. Evitar janelas TCP muito pequenas (64K) que limitam significativamente o throughput')
    
    if 'window_512k' not in summary or not categories['window_512k']:
        print('4. Testes com janelas maiores (512K) apresentaram erros - investigar limites do sistema')
    
    # Erros
    if errors:
        print(f'\n=== ERROS ENCONTRADOS ({len(errors)}) ===\n')
        for error in errors[:5]:  # Mostrar apenas primeiros 5
            print(f'  - {error}')

if __name__ == '__main__':
    analyze_final_results()