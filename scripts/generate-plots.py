#!/usr/bin/env python3
"""
Script simplificado para gerar gráficos dos resultados
Usa apenas bibliotecas padrão do Python para máxima compatibilidade
"""

import json
import glob
import os
from pathlib import Path
import statistics

def load_test_results():
    """Carrega todos os resultados JSON"""
    results = []
    json_files = glob.glob("results/raw/*.json")
    
    for file in json_files:
        try:
            with open(file) as f:
                content = f.read()
                if content.strip():  # Verificar se não está vazio
                    data = json.loads(content)
                    if "end" in data and "sum_sent" in data["end"]:
                        result = {
                            "file": os.path.basename(file),
                            "test_name": os.path.basename(file).split("_", 2)[2].replace(".json", ""),
                            "throughput_mbps": data["end"]["sum_sent"]["bits_per_second"] / 1e6,
                            "retransmits": data["end"]["sum_sent"].get("retransmits", 0)
                        }
                        results.append(result)
        except:
            continue
    
    return results

def categorize_results(results):
    """Organiza resultados por categoria"""
    categories = {
        "baseline": [],
        "window": {},
        "streams": {},
        "combined": []
    }
    
    for r in results:
        name = r["test_name"]
        if "baseline" in name:
            categories["baseline"].append(r)
        elif "window" in name:
            size = name.split("_")[1]
            if size not in categories["window"]:
                categories["window"][size] = []
            categories["window"][size].append(r)
        elif "streams" in name:
            num = name.split("_")[1]
            if num not in categories["streams"]:
                categories["streams"][num] = []
            categories["streams"][num].append(r)
        elif "combined" in name:
            categories["combined"].append(r)
    
    return categories

def create_svg_chart(data, title, output_file):
    """Cria um gráfico de barras em SVG"""
    # Configurações
    width = 800
    height = 600
    margin = {"top": 80, "right": 50, "bottom": 100, "left": 100}
    chart_width = width - margin["left"] - margin["right"]
    chart_height = height - margin["top"] - margin["bottom"]
    
    # Encontrar valores máximos
    max_value = max([d["value"] for d in data])
    
    # Calcular largura das barras
    bar_width = chart_width / len(data) * 0.8
    spacing = chart_width / len(data) * 0.2
    
    # Criar SVG
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .title {{ font: bold 24px sans-serif; }}
    .label {{ font: 14px sans-serif; }}
    .axis {{ font: 12px sans-serif; }}
    .bar {{ fill: #4CAF50; opacity: 0.8; }}
    .bar:hover {{ opacity: 1; }}
    .error-bar {{ stroke: #333; stroke-width: 2; }}
    .grid {{ stroke: #ddd; stroke-width: 1; opacity: 0.5; }}
  </style>
  
  <!-- Título -->
  <text x="{width/2}" y="40" text-anchor="middle" class="title">{title}</text>
  
  <!-- Grid -->
"""
    
    # Adicionar linhas de grade
    for i in range(0, 6):
        y_pos = margin["top"] + chart_height - (i * chart_height / 5)
        value = (max_value / 5) * i
        svg += f'  <line x1="{margin["left"]}" y1="{y_pos}" x2="{margin["left"] + chart_width}" y2="{y_pos}" class="grid"/>\n'
        svg += f'  <text x="{margin["left"] - 10}" y="{y_pos + 5}" text-anchor="end" class="axis">{value:.0f}</text>\n'
    
    svg += "\n  <!-- Barras -->\n"
    
    # Desenhar barras
    for i, item in enumerate(data):
        x = margin["left"] + i * (bar_width + spacing) + spacing/2
        bar_height = (item["value"] / max_value) * chart_height
        y = margin["top"] + chart_height - bar_height
        
        # Barra
        svg += f'  <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" class="bar">\n'
        svg += f'    <title>{item["label"]}: {item["value"]:.1f} Gbps</title>\n'
        svg += f'  </rect>\n'
        
        # Barra de erro se existir
        if "std" in item and item["std"] > 0:
            error_height = (item["std"] / max_value) * chart_height
            svg += f'  <line x1="{x + bar_width/2}" y1="{y - error_height}" x2="{x + bar_width/2}" y2="{y + error_height}" class="error-bar"/>\n'
            svg += f'  <line x1="{x + bar_width/2 - 5}" y1="{y - error_height}" x2="{x + bar_width/2 + 5}" y2="{y - error_height}" class="error-bar"/>\n'
            svg += f'  <line x1="{x + bar_width/2 - 5}" y1="{y + error_height}" x2="{x + bar_width/2 + 5}" y2="{y + error_height}" class="error-bar"/>\n'
        
        # Rótulo
        label_y = margin["top"] + chart_height + 20
        svg += f'  <text x="{x + bar_width/2}" y="{label_y}" text-anchor="middle" class="label" transform="rotate(-45 {x + bar_width/2} {label_y})">{item["label"]}</text>\n'
    
    # Eixos
    svg += f"""
  <!-- Eixos -->
  <line x1="{margin["left"]}" y1="{margin["top"]}" x2="{margin["left"]}" y2="{margin["top"] + chart_height}" stroke="#333" stroke-width="2"/>
  <line x1="{margin["left"]}" y1="{margin["top"] + chart_height}" x2="{margin["left"] + chart_width}" y2="{margin["top"] + chart_height}" stroke="#333" stroke-width="2"/>
  
  <!-- Labels dos eixos -->
  <text x="{width/2}" y="{height - 20}" text-anchor="middle" class="label">Configuração</text>
  <text x="40" y="{height/2}" text-anchor="middle" class="label" transform="rotate(-90 40 {height/2})">Throughput (Gbps)</text>
</svg>"""
    
    with open(output_file, "w") as f:
        f.write(svg)
    print(f"Gráfico salvo em: {output_file}")

def generate_comparison_chart():
    """Gera gráfico comparativo principal"""
    results = load_test_results()
    categories = categorize_results(results)
    
    # Preparar dados para o gráfico
    chart_data = []
    
    # Baseline
    if categories["baseline"]:
        values = [r["throughput_mbps"] for r in categories["baseline"]]
        chart_data.append({
            "label": "Baseline",
            "value": statistics.mean(values) / 1000,  # Converter para Gbps
            "std": statistics.stdev(values) / 1000 if len(values) > 1 else 0
        })
    
    # Window sizes
    for size in ["64K", "128K", "256K"]:
        if size in categories["window"]:
            values = [r["throughput_mbps"] for r in categories["window"][size]]
            chart_data.append({
                "label": f"Window {size}",
                "value": statistics.mean(values) / 1000,
                "std": statistics.stdev(values) / 1000 if len(values) > 1 else 0
            })
    
    # Streams
    for num in ["4"]:
        if num in categories["streams"]:
            values = [r["throughput_mbps"] for r in categories["streams"][num]]
            chart_data.append({
                "label": f"{num} Streams",
                "value": statistics.mean(values) / 1000,
                "std": statistics.stdev(values) / 1000 if len(values) > 1 else 0
            })
    
    # Combined
    if categories["combined"]:
        values = [r["throughput_mbps"] for r in categories["combined"]]
        chart_data.append({
            "label": "Combined",
            "value": statistics.mean(values) / 1000,
            "std": statistics.stdev(values) / 1000 if len(values) > 1 else 0
        })
    
    create_svg_chart(chart_data, "Comparação de Throughput por Configuração", "results/plots/throughput_comparison.svg")

def generate_retransmission_chart():
    """Gera gráfico de retransmissões"""
    results = load_test_results()
    categories = categorize_results(results)
    
    chart_data = []
    
    # Processar cada categoria
    for cat_name, cat_data in [("baseline", categories["baseline"])]:
        if cat_data:
            values = [r["retransmits"] for r in cat_data]
            chart_data.append({
                "label": "Baseline",
                "value": statistics.mean(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0
            })
    
    for size in ["64K", "128K", "256K"]:
        if size in categories["window"]:
            values = [r["retransmits"] for r in categories["window"][size]]
            chart_data.append({
                "label": f"Window {size}",
                "value": statistics.mean(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0
            })
    
    # Ajustar escala para retransmissões
    max_retrans = max([d["value"] for d in chart_data]) if chart_data else 100
    
    # Criar gráfico específico para retransmissões
    create_retransmission_svg(chart_data, "Retransmissões TCP por Configuração", "results/plots/retransmissions.svg", max_retrans)

def create_retransmission_svg(data, title, output_file, max_value):
    """Cria gráfico de barras para retransmissões (escala diferente)"""
    width = 800
    height = 600
    margin = {"top": 80, "right": 50, "bottom": 100, "left": 100}
    chart_width = width - margin["left"] - margin["right"]
    chart_height = height - margin["top"] - margin["bottom"]
    
    bar_width = chart_width / len(data) * 0.8
    spacing = chart_width / len(data) * 0.2
    
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .title {{ font: bold 24px sans-serif; }}
    .label {{ font: 14px sans-serif; }}
    .axis {{ font: 12px sans-serif; }}
    .bar {{ fill: #FF5722; opacity: 0.8; }}
    .bar:hover {{ opacity: 1; }}
    .grid {{ stroke: #ddd; stroke-width: 1; opacity: 0.5; }}
  </style>
  
  <text x="{width/2}" y="40" text-anchor="middle" class="title">{title}</text>
"""
    
    # Grid e eixo Y
    for i in range(0, 6):
        y_pos = margin["top"] + chart_height - (i * chart_height / 5)
        value = (max_value / 5) * i
        svg += f'  <line x1="{margin["left"]}" y1="{y_pos}" x2="{margin["left"] + chart_width}" y2="{y_pos}" class="grid"/>\n'
        svg += f'  <text x="{margin["left"] - 10}" y="{y_pos + 5}" text-anchor="end" class="axis">{value:.0f}</text>\n'
    
    # Barras
    for i, item in enumerate(data):
        x = margin["left"] + i * (bar_width + spacing) + spacing/2
        bar_height = (item["value"] / max_value) * chart_height if max_value > 0 else 0
        y = margin["top"] + chart_height - bar_height
        
        svg += f'  <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" class="bar">\n'
        svg += f'    <title>{item["label"]}: {item["value"]:.0f} retransmissões</title>\n'
        svg += f'  </rect>\n'
        
        # Valor acima da barra
        svg += f'  <text x="{x + bar_width/2}" y="{y - 5}" text-anchor="middle" class="axis">{item["value"]:.0f}</text>\n'
        
        # Rótulo
        label_y = margin["top"] + chart_height + 20
        svg += f'  <text x="{x + bar_width/2}" y="{label_y}" text-anchor="middle" class="label" transform="rotate(-45 {x + bar_width/2} {label_y})">{item["label"]}</text>\n'
    
    # Eixos
    svg += f"""
  <line x1="{margin["left"]}" y1="{margin["top"]}" x2="{margin["left"]}" y2="{margin["top"] + chart_height}" stroke="#333" stroke-width="2"/>
  <line x1="{margin["left"]}" y1="{margin["top"] + chart_height}" x2="{margin["left"] + chart_width}" y2="{margin["top"] + chart_height}" stroke="#333" stroke-width="2"/>
  
  <text x="{width/2}" y="{height - 20}" text-anchor="middle" class="label">Configuração</text>
  <text x="40" y="{height/2}" text-anchor="middle" class="label" transform="rotate(-90 40 {height/2})">Retransmissões</text>
</svg>"""
    
    with open(output_file, "w") as f:
        f.write(svg)
    print(f"Gráfico salvo em: {output_file}")

def main():
    """Função principal"""
    print("Gerando gráficos dos resultados...")
    
    # Criar diretório de saída
    os.makedirs("results/plots", exist_ok=True)
    
    # Gerar gráficos
    generate_comparison_chart()
    generate_retransmission_chart()
    
    print("\nGráficos gerados com sucesso!")
    print("Visualize os arquivos SVG em qualquer navegador web.")

if __name__ == "__main__":
    main()