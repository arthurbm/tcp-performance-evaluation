# Módulo de Análise

Este diretório contém os scripts de análise de dados do projeto, gerenciados com UV.

## Scripts Disponíveis

- **analyze.py**: Script principal de análise e geração de visualizações
- **collect-results.sh**: Coleta e organiza resultados dos testes em formato CSV
- **run-analysis.sh**: Wrapper para executar análise completa

## Dependências

Gerenciadas via UV (pyproject.toml):
- pandas: Manipulação de dados
- matplotlib: Geração de gráficos
- seaborn: Visualizações estatísticas
- numpy: Cálculos numéricos
- scikit-learn: Normalização de dados
- tabulate: Formatação de tabelas

## Uso

Dentro do container analyzer:
```bash
cd /app
bash run-analysis.sh
```

Ou análise específica:
```bash
uv run python analyze.py [timestamp]
```
