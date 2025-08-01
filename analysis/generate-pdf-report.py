#!/usr/bin/env python3

"""
Script para gerar relatório PDF da Atividade 2
Converte o relatório Markdown para PDF com formatação acadêmica
"""

import subprocess
import sys
from pathlib import Path
import shutil
from datetime import datetime

def check_dependencies():
    """Verifica se as dependências necessárias estão instaladas"""
    dependencies = {
        'pandoc': 'pandoc --version',
        'pdflatex': 'pdflatex --version'
    }
    
    missing = []
    for dep, cmd in dependencies.items():
        try:
            subprocess.run(cmd.split(), capture_output=True, check=True)
        except:
            missing.append(dep)
    
    if missing:
        print(f"ERRO: Dependências faltando: {', '.join(missing)}")
        print("\nPara instalar no container:")
        print("apt-get update && apt-get install -y pandoc texlive-full")
        return False
    
    return True

def create_latex_template():
    """Cria template LaTeX customizado para o relatório"""
    template = r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[portuguese]{babel}
\usepackage{geometry}
\geometry{a4paper, margin=2.5cm}
\usepackage{graphicx}
\usepackage{float}
\usepackage{hyperref}
\usepackage{listings}
\usepackage{color}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{tocloft}
\usepackage{array}
\usepackage{booktabs}
\usepackage{longtable}

% Configurações de código
\definecolor{codegreen}{rgb}{0,0.6,0}
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{codepurple}{rgb}{0.58,0,0.82}
\definecolor{backcolour}{rgb}{0.95,0.95,0.92}

\lstdefinestyle{mystyle}{
    backgroundcolor=\color{backcolour},   
    commentstyle=\color{codegreen},
    keywordstyle=\color{magenta},
    numberstyle=\tiny\color{codegray},
    stringstyle=\color{codepurple},
    basicstyle=\ttfamily\footnotesize,
    breakatwhitespace=false,         
    breaklines=true,                 
    captionpos=b,                    
    keepspaces=true,                 
    numbers=left,                    
    numbersep=5pt,                  
    showspaces=false,                
    showstringspaces=false,
    showtabs=false,                  
    tabsize=2
}

\lstset{style=mystyle}

% Configuração de cabeçalho e rodapé
\pagestyle{fancy}
\fancyhf{}
\rhead{Análise Comparativa de Cenários de Rede TCP}
\lhead{Redes de Computadores}
\rfoot{Página \thepage}

% Configuração de títulos
\titleformat{\section}
  {\normalfont\Large\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}
  {\normalfont\large\bfseries}{\thesubsection}{1em}{}

% Metadados
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,      
    urlcolor=cyan,
    pdftitle={Análise Comparativa de Cenários de Rede TCP},
    pdfauthor={Arthur Brito Medeiros},
}

\title{$title$}
\author{$author$}
\date{$date$}

\begin{document}

\maketitle
\thispagestyle{empty}
\newpage

\tableofcontents
\newpage

$body$

\end{document}
"""
    
    return template

def process_markdown_file(input_file, output_file, template_file):
    """Processa arquivo Markdown e gera PDF"""
    
    # Criar comando pandoc
    cmd = [
        'pandoc',
        str(input_file),
        '-o', str(output_file),
        '--template', str(template_file),
        '--pdf-engine=pdflatex',
        '--highlight-style=tango',
        '--toc',
        '--toc-depth=3',
        '-V', 'documentclass=article',
        '-V', 'fontsize=12pt',
        '-V', 'geometry:margin=2.5cm',
        '-V', f'title=Análise Comparativa de Cenários de Rede TCP',
        '-V', f'author=Arthur Brito Medeiros',
        '-V', f'date={datetime.now().strftime("%d de %B de %Y")}',
        '--metadata', 'lang=pt-BR'
    ]
    
    print(f"Executando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✓ PDF gerado com sucesso: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro ao gerar PDF:")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False

def prepare_report_with_images(report_file, plots_dir):
    """Prepara o relatório incluindo referências às imagens"""
    
    # Ler conteúdo original
    with open(report_file, 'r') as f:
        content = f.read()
    
    # Adicionar seção de gráficos se não existir
    if "## Visualizações e Gráficos" not in content:
        graphs_section = """
## Visualizações e Gráficos

### Comparação Geral de Cenários

![Comparação de throughput entre todos os cenários testados](plots/atv2_scenario_comparison.png)

A figura acima apresenta a comparação de throughput médio entre todos os cenários, com barras de erro representando o desvio padrão. É possível observar claramente o impacto das diferentes configurações e condições de rede no desempenho.

### Métricas Detalhadas

![Análise detalhada de múltiplas métricas por cenário](plots/atv2_detailed_metrics.png)

Esta figura apresenta quatro análises complementares:
1. **Distribuição de Throughput**: Box plots mostrando a variabilidade em cada cenário
2. **Retransmissões TCP**: Indicador de confiabilidade da conexão
3. **Utilização de CPU**: Eficiência computacional de cada configuração
4. **Estabilidade**: Coeficiente de variação como medida de consistência

### Impacto das Condições de Rede

![Análise do impacto das condições de rede no desempenho](plots/atv2_network_conditions_impact.png)

Esta análise demonstra como diferentes condições de rede afetam o desempenho:
1. **Impacto da Latência**: Relação entre RTT e throughput
2. **Limitação de Banda**: Eficiência de utilização do enlace
3. **Algoritmos de Congestionamento**: Comparação de desempenho
4. **Correlações**: Matriz mostrando relações entre variáveis
"""
        
        # Inserir antes da conclusão
        if "## Conclusão" in content:
            content = content.replace("## Conclusão", graphs_section + "\n## Conclusão")
        else:
            content += "\n" + graphs_section
    
    # Criar arquivo temporário com conteúdo atualizado
    temp_file = report_file.parent / f"{report_file.stem}_with_images.md"
    with open(temp_file, 'w') as f:
        f.write(content)
    
    return temp_file

def main():
    """Função principal"""
    print("=== Gerador de Relatório PDF - Atividade 2 ===\n")
    
    # Verificar dependências
    print("Verificando dependências...")
    if not check_dependencies():
        print("\nINSTALAÇÃO NO CONTAINER ANALYZER:")
        print("docker exec -it tcp-analyzer bash")
        print("apt-get update && apt-get install -y pandoc texlive-xetex texlive-fonts-recommended")
        sys.exit(1)
    
    # Diretórios
    docs_dir = Path("/docs/atv2")
    report_file = docs_dir / "REPORT2.md"
    plots_dir = docs_dir / "results" / "plots"
    output_dir = docs_dir
    
    # Verificar se o relatório existe
    if not report_file.exists():
        print(f"ERRO: Relatório não encontrado: {report_file}")
        print("Execute primeiro a análise e escreva o relatório REPORT2.md")
        sys.exit(1)
    
    # Criar template LaTeX
    print("\nCriando template LaTeX...")
    template_content = create_latex_template()
    template_file = output_dir / "template.tex"
    with open(template_file, 'w') as f:
        f.write(template_content)
    
    # Preparar relatório com imagens
    print("Preparando relatório com imagens...")
    temp_report = prepare_report_with_images(report_file, plots_dir)
    
    # Gerar PDF
    output_pdf = output_dir / "REPORT2_Atividade2_TCP_Analysis.pdf"
    print(f"\nGerando PDF: {output_pdf}")
    
    if process_markdown_file(temp_report, output_pdf, template_file):
        print("\n✓ Relatório PDF gerado com sucesso!")
        print(f"Arquivo: {output_pdf}")
        
        # Limpar arquivos temporários
        temp_report.unlink()
        template_file.unlink()
        
        # Gerar também uma versão simples sem template
        simple_pdf = output_dir / "REPORT2_simple.pdf"
        simple_cmd = [
            'pandoc',
            str(report_file),
            '-o', str(simple_pdf),
            '--pdf-engine=pdflatex',
            '-V', 'geometry:margin=2.5cm',
            '-V', 'fontsize=12pt'
        ]
        
        try:
            subprocess.run(simple_cmd, capture_output=True, check=True)
            print(f"\nVersão simplificada também gerada: {simple_pdf}")
        except:
            pass
    else:
        print("\n✗ Falha ao gerar PDF")
        print("\nDica: Se pandoc não estiver instalado no container analyzer:")
        print("1. docker exec -it tcp-analyzer bash")
        print("2. apt-get update && apt-get install -y pandoc texlive-xetex")
        
        # Tentar gerar HTML como alternativa
        print("\nTentando gerar HTML como alternativa...")
        html_output = output_dir / "REPORT2.html"
        html_cmd = [
            'pandoc',
            str(report_file),
            '-o', str(html_output),
            '--standalone',
            '--toc',
            '--highlight-style=tango',
            '--css', 'https://cdn.jsdelivr.net/npm/github-markdown-css/github-markdown.min.css'
        ]
        
        try:
            subprocess.run(html_cmd, check=True)
            print(f"✓ HTML gerado: {html_output}")
        except:
            print("✗ Também não foi possível gerar HTML")

if __name__ == "__main__":
    main()