# Avaliação de Desempenho TCP com Docker

Este projeto implementa um ambiente automatizado para avaliação de desempenho TCP usando Docker, iperf3 e análise de dados com Python/UV.

## Visão Geral

O projeto utiliza 3 containers Docker:
- **tcp-server**: Servidor iperf3 (Debian 11)
- **tcp-client**: Cliente iperf3 com scripts de automação (Debian 11)
- **tcp-analyzer**: Container de análise com Python e UV

## Pré-requisitos

- Docker e Docker Compose instalados
- Módulos de kernel para algoritmos de congestionamento TCP (cubic, reno, vegas, bbr)
- Pelo menos 4GB de RAM disponível

## Instalação e Configuração

1. Clone o repositório:
```bash
git clone <repo-url>
cd tcp-performance-evaluation
```

2. Construa as imagens Docker:
```bash
docker compose build
```

3. Inicie os containers:
```bash
docker compose up -d
```

4. Verifique se todos estão rodando:
```bash
docker compose ps
```

## Execução dos Testes

### Teste Rápido de Conectividade
```bash
docker exec tcp-client iperf3 -c 10.5.0.10 -t 5
```

### Executar Bateria Completa de Testes
```bash
docker compose exec client /scripts/run-tests.sh
```

Este comando executará automaticamente:
- Testes baseline
- Variações de janela TCP (64K, 128K, 256K, 512K)
- Múltiplos fluxos paralelos (1, 2, 4, 8)
- Diferentes algoritmos de congestionamento
- Simulações de condições de rede (latência, banda limitada, perda de pacotes)

### Análise dos Resultados

#### Opção 1: Análise Completa com UV (recomendado)
```bash
docker compose exec analyzer /app/run-analysis.sh
```

#### Opção 2: Análise Estatística Simplificada
```bash
docker cp scripts/analyze-results.py tcp-analyzer:/tmp/
docker compose exec analyzer python3 /tmp/analyze-results.py
```

A análise irá:
- Processar todos os arquivos JSON do iperf3
- Calcular médias e desvios padrão por categoria
- Comparar desempenho relativo ao baseline
- Identificar a configuração ótima
- Gerar recomendações baseadas nos resultados

## Estrutura do Projeto

```
tcp-performance-evaluation/
├── Dockerfile.test           # Imagem para servidor/cliente
├── Dockerfile.analysis       # Imagem para análise com UV
├── docker-compose.yml        # Orquestração dos containers
├── PLAN.md                  # Plano detalhado e metodologia
├── REPORT.md                # Relatório final com resultados
├── README.md                # Este arquivo
├── .dockerignore            # Arquivos ignorados no build
├── scripts/
│   ├── run-tests.sh        # Script principal de testes
│   ├── analyze-results.py  # Análise estatística dos resultados
│   └── test-scenarios.json # Definição dos cenários
├── configs/
│   ├── server-entrypoint.sh # Inicialização do servidor
│   └── client-entrypoint.sh # Inicialização do cliente
├── analysis/                # Projeto UV para análise
│   ├── analyze.py          # Script de análise e visualização
│   ├── collect-results.sh  # Coleta de resultados
│   ├── run-analysis.sh     # Wrapper para execução
│   ├── pyproject.toml      # Configuração do projeto UV
│   ├── uv.lock            # Lock file das dependências
│   └── README.md           # Documentação do módulo de análise
├── results/
│   ├── raw/                # Outputs JSON do iperf3
│   ├── processed/          # Dados processados (CSV)
│   └── plots/              # Gráficos gerados
└── report/
    ├── tables/             # Tabelas de resultados
    └── figures/            # Gráficos e diagramas
```

## Cenários de Teste

### 1. Baseline
- Configurações padrão do iperf3

### 2. Tamanho da Janela TCP
- 64KB, 128KB, 256KB, 512KB

### 3. Fluxos Paralelos
- 1, 2, 4, 8 fluxos simultâneos

### 4. Algoritmos de Congestionamento
- CUBIC (padrão), Reno, Vegas, BBR

### 5. Condições de Rede
- Latência: 50ms, 100ms
- Banda limitada: 10Mbps, 100Mbps
- Perda de pacotes: 0.1%, 1%

## Comandos Úteis

### Acessar containers individualmente:
```bash
docker exec -it tcp-server bash
docker exec -it tcp-client bash
docker exec -it tcp-analyzer bash
```

### Ver logs:
```bash
docker logs tcp-server
docker logs tcp-client
docker logs tcp-analyzer
```

### Parar containers:
```bash
docker compose down
```

### Limpar volumes e redes:
```bash
docker compose down -v
```

## Análise Manual

Para executar análises específicas dentro do container analyzer:

```bash
docker compose exec analyzer bash
cd /app
uv run python analyze.py [timestamp]
```

## Troubleshooting

### Erro de rede ao iniciar containers
Se houver conflito de IPs, edite o `docker-compose.yml` e mude o range da subnet.

### Algoritmos de congestionamento não disponíveis
Verifique no host se os módulos estão carregados:
```bash
lsmod | grep tcp_
sudo modprobe tcp_bbr  # Exemplo para carregar BBR
```

### Containers não conseguem se comunicar
Verifique as configurações de firewall e se o Docker tem permissões adequadas.

## Resultados Obtidos

### Configuração Ótima Identificada
- **Janela TCP**: 256KB + **Fluxos Paralelos**: 4
- **Throughput**: 60.85 Gbps (melhoria de +20.5% sobre baseline)
- **Retransmissões**: 0 (máxima estabilidade)

### Principais Descobertas
1. Janelas TCP pequenas (64K) degradam o desempenho em ~14.5%
2. Janelas muito grandes (512K) causam erro de buffer de socket
3. A combinação de parâmetros otimizados supera ganhos individuais
4. Configurações otimizadas eliminam retransmissões TCP

## Notas Importantes

1. Os testes são executados com 3 repetições por cenário para confiabilidade estatística
2. Cada teste dura 30 segundos por padrão (configurável)
3. Os resultados são salvos com timestamp para rastreabilidade
4. O container de análise usa UV para gerenciamento de dependências Python
5. Todos os IPs são fixos para reprodutibilidade:
   - Servidor: 10.5.0.10
   - Cliente: 10.5.0.20
6. Valores de throughput elevados (~50 Gbps) são devido à comunicação local entre containers

## Contribuições

Para contribuir com o projeto:
1. Faça um fork
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

Este projeto é para fins educacionais.