# Plano de Avaliação de Desempenho TCP com Docker

## Objetivo
Configurar ambiente com Docker (servidor e cliente) para realizar testes de desempenho com iperf3, identificando experimentalmente a configuração ideal que maximize o throughput e minimize a latência.

## Metodologia: Docker vs KVM

### Justificativa para uso do Docker:
- **Portabilidade**: Containers são mais leves e portáveis que VMs
- **Reprodutibilidade**: Dockerfile garante ambiente idêntico em qualquer máquina
- **Eficiência**: Menor overhead comparado a virtualização completa
- **Automação**: Facilita scripts de automação e CI/CD
- **Isolamento de rede**: Docker networks providenciam isolamento adequado para os testes

### Adaptações necessárias:
- Substituir configuração de VMs por containers Docker
- Usar Docker Compose para orquestrar servidor e cliente
- Adaptar comandos de rede para ambiente containerizado
- Implementar tc (traffic control) dentro dos containers

## Checklist de Implementação

### Fase 1: Configuração do Ambiente Docker
- [x] Criar Dockerfile.test para servidor/cliente com Debian 11 e iperf3
- [x] Criar Dockerfile.analysis com UV para análise de dados
- [x] Configurar docker-compose.yml com 3 containers (servidor, cliente, analyzer)
- [x] Definir rede bridge customizada para isolamento
- [x] Testar comunicação básica entre containers

### Fase 2: Scripts de Automação
- [x] Criar script run-tests.sh para executar todos os cenários
- [x] Implementar collect-results.sh para organizar outputs
- [x] Desenvolver analyze.py para análise estatística
- [x] Criar entrypoints para servidor e cliente
- [x] Configurar projeto UV para gerenciamento de dependências Python

### Fase 3: Definição dos Cenários de Teste

#### Parâmetros Base:
- **Duração de cada teste**: 30 segundos
- **Intervalo entre testes**: 5 segundos
- **Repetições por cenário**: 3 (para média)

#### Matriz de Testes:
1. **Teste Baseline** (configurações padrão)
   - [x] Sem modificações
   - [x] Registrar valores de referência

2. **Variação de Janela TCP**:
   - [x] 64K
   - [ ] 128K
   - [x] 256K
   - [ ] 512K

3. **Variação de Fluxos Simultâneos**:
   - [ ] 1 fluxo
   - [ ] 2 fluxos
   - [x] 4 fluxos
   - [ ] 8 fluxos

4. **Algoritmos de Congestionamento**:
   - [ ] cubic (padrão)
   - [ ] reno
   - [ ] vegas
   - [ ] bbr (se disponível)

5. **Condições de Rede Simuladas** (com tc):
   - [ ] Latência: 0ms, 50ms, 100ms
   - [ ] Limitação de banda: sem limite, 10Mbps, 100Mbps
   - [ ] Perda de pacotes: 0%, 0.1%, 1%

### Fase 4: Execução dos Experimentos
- [x] Executar teste baseline
- [x] Executar testes com variação de janela TCP (parcial)
- [x] Executar testes com múltiplos fluxos (parcial)
- [ ] Executar testes com diferentes algoritmos
- [ ] Executar testes com condições de rede simuladas
- [x] Validar integridade dos dados coletados

### Fase 5: Análise dos Resultados
- [x] Processar outputs JSON do iperf3
- [ ] Calcular médias e desvios padrão
- [x] Gerar tabelas comparativas
- [ ] Criar gráficos de desempenho
- [x] Identificar configuração ótima (preliminar)
- [ ] Documentar justificativas técnicas

### Fase 6: Relatório Final
- [ ] Estruturar relatório conforme requisitos
- [ ] Incluir tabela com todos os resultados
- [ ] Adicionar comparação entre cenários
- [ ] Justificar configuração de melhor desempenho
- [ ] Descrever ambiente Docker utilizado
- [ ] Incluir comandos para reprodução

## Estrutura de Diretórios

```
tcp-performance-evaluation/
├── Dockerfile.test           # Imagem para servidor/cliente (Debian 11 + iperf3)
├── Dockerfile.analysis       # Imagem para análise (UV + Python + libs)
├── docker-compose.yml        # Orquestração de 3 containers
├── PLAN.md                   # Este arquivo
├── README.md                 # Instruções de uso
├── .dockerignore            # Arquivos ignorados no build
├── scripts/
│   ├── run-tests.sh         # Executa todos os cenários (no cliente)
│   └── test-scenarios.json  # Definição dos cenários
├── configs/
│   ├── server-entrypoint.sh # Script de inicialização do servidor
│   └── client-entrypoint.sh # Script de inicialização do cliente
├── analysis/                 # Projeto UV para análise
│   ├── pyproject.toml       # Configuração do projeto UV
│   ├── uv.lock             # Lock file das dependências
│   ├── analyze.py           # Análise e geração de gráficos
│   ├── collect-results.sh   # Coleta e organiza resultados
│   └── run-analysis.sh      # Wrapper para executar análises
├── results/
│   ├── raw/                 # Outputs brutos do iperf3 (JSON)
│   ├── processed/           # Dados processados (CSV)
│   └── plots/               # Gráficos gerados
└── report/
    ├── REPORT.md           # Relatório final
    ├── tables/             # Tabelas de resultados
    └── figures/            # Gráficos e diagramas
```

## Comandos Principais

### Construir e iniciar ambiente:
```bash
docker-compose build
docker-compose up -d
```

### Executar todos os testes:
```bash
docker-compose exec client /scripts/run-tests.sh
```

### Analisar resultados:
```bash
docker-compose exec analyzer /app/run-analysis.sh
```

### Acessar containers para debug:
```bash
docker exec -it tcp-server bash
docker exec -it tcp-client bash
docker exec -it tcp-analyzer bash
```

## Métricas a Coletar

1. **Throughput** (Mbps/Gbps)
2. **Latência/RTT** (ms)
3. **Jitter** (ms)
4. **Perda de pacotes** (%)
5. **Utilização de CPU** (%)
6. **Retransmissões TCP**
7. **Window size efetivo**

## Observações Importantes

1. **Módulos do kernel**: Alguns algoritmos de congestionamento podem requerer módulos específicos. Verificar disponibilidade no host Docker.

2. **Limites do Docker**: Containers compartilham o kernel do host, então algumas configurações TCP são globais.

3. **Precisão dos testes**: Executar múltiplas rodadas e calcular médias para maior confiabilidade estatística.

4. **Isolamento**: Garantir que não há outros processos consumindo recursos durante os testes.

5. **Documentação**: Registrar TODOS os comandos executados para garantir reprodutibilidade.

6. **Separação de responsabilidades**: 
   - Container de teste: Apenas ferramentas de rede (iperf3, tc, etc)
   - Container de análise: Ambiente Python com UV para processamento de dados
   - Benefício: Containers menores, mais seguros e com versões fixadas

## Status: Testes em Execução e Análise Preliminar
Última atualização: 2025-07-26

### Resultados Preliminares:
- **Melhor configuração identificada**: Janela 256K + 4 streams paralelos
- **Throughput máximo**: 60.85 Gbps
- **Baseline**: ~50 Gbps
- **Melhoria**: ~21% sobre baseline

### Próximos Passos:
1. Executar bateria completa de testes com `docker compose exec client /scripts/run-tests.sh`
2. Analisar resultados com `docker compose exec analyzer /app/run-analysis.sh`
3. Gerar relatório final com base nos resultados