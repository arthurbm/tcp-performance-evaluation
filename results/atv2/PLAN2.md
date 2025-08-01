# Plano de Implementação - Atividade 2: Análise Comparativa de Cenários de Rede

**Disciplina**: Redes de Computadores  
**Atividade**: Análise Comparativa de Cenários de Rede  
**Data**: 2025-08-01

## 1. Objetivo

Projetar e executar um conjunto abrangente de cenários de teste TCP, incluindo:
- Alteração de algoritmos de controle de congestionamento (mínimo 3)
- Variação de parâmetros TCP (janela e fluxos simultâneos)
- Simulação de condições adversas de rede (latência, banda limitada, perda de pacotes)
- Análise crítica e comparativa de pelo menos 6 cenários distintos

## 2. Metodologia

### 2.1 Infraestrutura Existente
- **Ambiente**: Docker com 3 containers (servidor, cliente, analyzer)
- **Rede**: Bridge isolada (10.5.0.0/24)
- **Ferramentas**: iperf3, tc (traffic control), Python com UV
- **Automação**: Scripts bash para execução e análise

### 2.2 Adaptações Necessárias
- Criar cenários específicos e bem justificados teoricamente
- Aumentar repetições para confiabilidade estatística (5 por cenário)
- Implementar análise avançada com justificativas teóricas
- Gerar relatório estruturado em formato acadêmico

## 3. Definição dos 6 Cenários de Teste

### Cenário 1: "Baseline - Rede Ideal"
**Objetivo**: Estabelecer referência em condições ideais

**Configurações**:
- Algoritmo de congestionamento: CUBIC (padrão Linux)
- Tamanho da janela TCP: Auto (sistema define)
- Número de fluxos: 1
- Condições de rede: Sem limitações artificiais

**Justificativa Teórica**: 
- CUBIC é o algoritmo padrão por sua eficiência em redes modernas
- Configurações automáticas permitem ao sistema otimizar dinamicamente
- Fornece baseline para comparação com outros cenários

**Métricas Esperadas**:
- Throughput máximo possível no ambiente
- Latência mínima (< 1ms em rede local)
- Zero perda de pacotes

### Cenário 2: "High Performance Computing (HPC)"
**Objetivo**: Maximizar throughput para transferências massivas de dados

**Configurações**:
- Algoritmo de congestionamento: BBR
- Tamanho da janela TCP: 512KB
- Número de fluxos: 8 paralelos
- Condições de rede: Latência baixa artificial (1ms)

**Justificativa Teórica**:
- BBR mantém alta utilização sem causar congestionamento
- Janela grande permite máximo throughput em redes de baixa latência
- Múltiplos fluxos exploram paralelismo e CPUs multi-core
- Simula ambiente de datacenter moderno

**Métricas Esperadas**:
- Throughput 20-30% superior ao baseline
- Utilização de CPU mais alta
- Possíveis retransmissões devido ao comportamento agressivo

### Cenário 3: "Rede Corporativa Congestionada"
**Objetivo**: Avaliar comportamento sob congestionamento típico

**Configurações**:
- Algoritmo de congestionamento: Vegas
- Tamanho da janela TCP: 128KB
- Número de fluxos: 4
- Condições de rede: 
  - Banda limitada: 10Mbps
  - Latência: 50ms

**Justificativa Teórica**:
- Vegas é conservador, ideal para redes congestionadas
- Janela moderada evita overflow em enlaces limitados
- 4 fluxos balanceiam throughput e fairness
- Simula WAN corporativa típica

**Métricas Esperadas**:
- Throughput próximo ao limite de 10Mbps
- Baixas retransmissões
- RTT estável em torno de 50ms

### Cenário 4: "Rede Sem Fio Instável"
**Objetivo**: Testar resiliência a perdas de pacotes

**Configurações**:
- Algoritmo de congestionamento: Reno
- Tamanho da janela TCP: 256KB
- Número de fluxos: 2
- Condições de rede:
  - Perda de pacotes: 0.5%
  - Latência: 30ms
  - Jitter: 10ms

**Justificativa Teórica**:
- Reno tem recuperação rápida de perdas isoladas
- Janela média balanceia throughput e recuperação
- 2 fluxos providenciam redundância sem saturar
- Simula WiFi com interferências

**Métricas Esperadas**:
- Throughput 70-80% do baseline
- Retransmissões proporcionais à perda
- Variação no RTT devido ao jitter

### Cenário 5: "Datacenter Legacy"
**Objetivo**: Otimização para infraestrutura antiga

**Configurações**:
- Algoritmo de congestionamento: CUBIC
- Tamanho da janela TCP: 64KB
- Número de fluxos: 1
- Condições de rede:
  - Banda: 100Mbps
  - Latência: 5ms

**Justificativa Teórica**:
- CUBIC funciona bem em ambientes previsíveis
- Janela pequena adequada para buffers limitados
- Fluxo único evita contenção em hardware antigo
- Simula switches/roteadores de geração anterior

**Métricas Esperadas**:
- Throughput próximo a 100Mbps
- Latência estável
- Mínimas retransmissões

### Cenário 6: "WAN Intercontinental"
**Objetivo**: Simular conexão de longa distância

**Configurações**:
- Algoritmo de congestionamento: BBR
- Tamanho da janela TCP: 256KB
- Número de fluxos: 4
- Condições de rede:
  - Latência: 100ms
  - Perda de pacotes: 0.1%
  - Banda: 50Mbps

**Justificativa Teórica**:
- BBR lida bem com alto BDP (Bandwidth-Delay Product)
- Janela adequada para RTT alto
- Múltiplos fluxos compensam perdas isoladas
- Simula link intercontinental real

**Métricas Esperadas**:
- Throughput 40-45Mbps
- RTT base de 100ms + variações
- Recuperação eficiente de perdas

## 4. Matriz de Testes

| Cenário | Algoritmo | Janela | Fluxos | Latência | Banda | Perda | Repetições |
|---------|-----------|--------|--------|----------|-------|-------|------------|
| 1. Baseline | CUBIC | Auto | 1 | 0ms | ∞ | 0% | 5 |
| 2. HPC | BBR | 512KB | 8 | 1ms | ∞ | 0% | 5 |
| 3. Corp | Vegas | 128KB | 4 | 50ms | 10Mbps | 0% | 5 |
| 4. WiFi | Reno | 256KB | 2 | 30ms | ∞ | 0.5% | 5 |
| 5. Legacy | CUBIC | 64KB | 1 | 5ms | 100Mbps | 0% | 5 |
| 6. WAN | BBR | 256KB | 4 | 100ms | 50Mbps | 0.1% | 5 |

**Total**: 30 execuções de teste

## 5. Estrutura de Implementação

### 5.1 Scripts Principais

1. **run-atv2-tests.sh**
   - Executa apenas os 6 cenários definidos
   - 5 repetições por cenário
   - Salva resultados em diretório específico
   - Tempo estimado: 30 min

2. **analyze-atv2.py**
   - Análise estatística avançada (média, desvio, percentis)
   - Comparações entre cenários
   - Geração de tabelas formatadas
   - Criação de gráficos específicos

3. **generate-pdf-report.py**
   - Conversão Markdown → PDF
   - Template LaTeX acadêmico
   - Inclusão automática de gráficos

### 5.2 Arquivos de Configuração

Cada cenário terá um arquivo JSON em `scenarios/`:
```json
{
  "name": "scenario_1_baseline",
  "description": "Baseline - Rede Ideal",
  "iperf_params": "",
  "tcp_settings": {
    "congestion_control": "cubic",
    "window_size": null
  },
  "network_conditions": {
    "latency": null,
    "bandwidth": null,
    "packet_loss": null
  },
  "repetitions": 5
}
```

## 6. Análises a Realizar

### 6.1 Por Cenário
- Estatísticas descritivas (média, mediana, desvio padrão)
- Distribuição de throughput (histograma)
- Análise temporal (throughput ao longo do tempo)
- Correlação entre métricas

### 6.2 Comparativa
- Tabela comparativa geral
- Gráficos de barras com intervalos de confiança
- Heat map de desempenho
- Análise de trade-offs

### 6.3 Interpretação Teórica
- Explicação do comportamento observado
- Relação com teoria de controle de congestionamento
- Impacto de cada parâmetro
- Recomendações práticas

## 7. Estrutura do Relatório Final

1. **Introdução** (1 página)
   - Contextualização
   - Objetivos
   - Contribuições

2. **Metodologia** (2-3 páginas)
   - Ambiente de testes
   - Cenários detalhados
   - Métricas e ferramentas

3. **Resultados e Análise** (4-5 páginas)
   - Resultados por cenário
   - Comparações
   - Discussão crítica

4. **Conclusão** (1-2 páginas)
   - Principais descobertas
   - Recomendações
   - Trabalhos futuros

## 8. Cronograma de Execução

1. **Preparação** (30 min)
   - Criar scripts e configurações
   - Validar ambiente

2. **Execução** (30 min)
   - Rodar todos os testes
   - Monitorar progresso

3. **Análise** (1 hora)
   - Processar resultados
   - Gerar visualizações

4. **Relatório** (2 horas)
   - Escrever análise
   - Revisar e formatar

## 9. Checklist de Implementação

- [ ] Criar arquivos de cenários JSON
- [ ] Implementar run-atv2-tests.sh
- [ ] Adaptar analyze-atv2.py
- [ ] Criar generate-pdf-report.py
- [ ] Executar bateria de testes
- [ ] Analisar resultados
- [ ] Escrever relatório
- [ ] Gerar PDF final

## 10. Considerações Técnicas

### 10.1 Limitações
- Testes em containers compartilham kernel do host
- Alguns algoritmos podem não estar disponíveis
- Throughput muito alto devido à comunicação local

### 10.2 Validações
- Verificar disponibilidade de algoritmos antes dos testes
- Confirmar aplicação correta das condições de rede
- Validar integridade dos dados coletados

### 10.3 Reprodutibilidade
- Todos os parâmetros documentados
- Seeds fixas para componentes aleatórios
- Ambiente completamente containerizado

---

**Status**: Planejamento Completo  
**Próximo Passo**: Implementar arquivos de configuração dos cenários