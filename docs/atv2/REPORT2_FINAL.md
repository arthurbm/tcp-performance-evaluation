# Análise Comparativa de Cenários de Rede TCP

**Disciplina**: Redes de Computadores  
**Atividade**: 2 - Análise Comparativa de Cenários de Rede  
**Autor**: Arthur Brito Medeiros  
**Data**: 2025-08-01  
**Repositório**: [https://github.com/arthurbm/tcp-performance-evaluation](https://github.com/arthurbm/tcp-performance-evaluation)

## 1. Introdução

### 1.1 Contextualização

O desempenho de redes TCP é significativamente influenciado por diversos fatores, incluindo parâmetros de configuração TCP e condições da rede. Compreender como esses fatores interagem é fundamental para otimizar aplicações em diferentes ambientes, desde datacenters locais até conexões com limitações de banda e alta latência.

### 1.2 Objetivos

Este trabalho tem como objetivos:

1. Analisar como parâmetros TCP (tamanho de janela e número de fluxos) afetam o throughput
2. Investigar o comportamento do TCP sob condições adversas de rede (latência, limitação de banda, perda de pacotes)
3. Fornecer recomendações práticas para diferentes tipos de aplicações e ambientes de rede
4. Demonstrar o impacto significativo das condições de rede no desempenho TCP

### 1.3 Contribuições

- Análise sistemática de 6 cenários distintos representando ambientes reais
- Avaliação estatística com múltiplas repetições para confiabilidade
- Quantificação do impacto de cada condição de rede
- Guia prático para escolha de configurações TCP

## 2. Metodologia

### 2.1 Ambiente de Testes

#### 2.1.1 Infraestrutura

O ambiente de testes foi implementado utilizando Docker, proporcionando:
- **Isolamento**: Containers dedicados para servidor, cliente e análise
- **Reprodutibilidade**: Ambiente idêntico em qualquer máquina
- **Controle**: Capacidade de simular diferentes condições de rede via tc

**Arquitetura**:
```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│ tcp-server  │────▶│  testnet    │◀────│  tcp-client  │
│ (10.5.0.10) │     │ (10.5.0.0/24)│     │ (10.5.0.20)  │
└─────────────┘     └─────────────┘     └──────────────┘
                           │
                    ┌──────────────┐
                    │ tcp-analyzer │
                    │   (análise)  │
                    └──────────────┘
```

#### 2.1.2 Especificações Técnicas

- **Sistema Base**: Debian 11 (Bullseye) slim
- **Ferramenta de teste**: iperf3 v3.9
- **Controle de tráfego**: tc (traffic control)
- **Análise**: Python 3.11 com pandas, matplotlib, seaborn
- **Kernel**: Linux com suporte a CUBIC (padrão)

### 2.2 Cenários Testados

Foram executados 6 cenários representando diferentes condições de rede:

#### Cenário 1: Baseline
- **Objetivo**: Estabelecer referência de desempenho máximo
- **Configurações**: Padrões do sistema, sem limitações
- **Representa**: Rede local ideal de alta velocidade

#### Cenário 2: Janela TCP 256KB
- **Objetivo**: Avaliar impacto do tamanho da janela TCP
- **Configurações**: Window size = 256KB
- **Representa**: Otimização para redes de alta capacidade

#### Cenário 3: Múltiplos Fluxos Paralelos
- **Objetivo**: Testar paralelismo TCP
- **Configurações**: 4 fluxos simultâneos
- **Representa**: Aplicações que usam múltiplas conexões

#### Cenário 4: Alta Latência
- **Objetivo**: Simular conexões de longa distância
- **Configurações**: Latência artificial de 50ms
- **Representa**: Conexões WAN ou intercontinentais

#### Cenário 5: Banda Limitada
- **Objetivo**: Avaliar comportamento com recursos limitados
- **Configurações**: Banda limitada a 10Mbps
- **Representa**: Redes corporativas antigas ou sobrecarregadas

#### Cenário 6: Perda de Pacotes
- **Objetivo**: Testar resiliência a perdas
- **Configurações**: Perda artificial de 0.5%
- **Representa**: Redes sem fio ou links instáveis

### 2.3 Procedimento Experimental

1. **Preparação**: Inicialização dos containers Docker
2. **Execução**: 3 repetições de 10 segundos por cenário
3. **Coleta**: Salvamento de resultados em formato JSON
4. **Análise**: Processamento estatístico dos dados

## 3. Resultados e Análise

### 3.1 Resumo dos Resultados

| Cenário | Throughput Médio (Mbps) | Desvio Padrão | Retransmissões | Impacto vs Baseline |
|---------|-------------------------|---------------|----------------|---------------------|
| Baseline | 48,464.4 | 992.0 | 76 | - |
| Janela 256KB | 47,021.6 | 32.4 | 0 | -3.0% |
| 4 Fluxos Paralelos | 48,137.7 | 943.5 | 1 | -0.7% |
| Latência 50ms | 583.3 | 3.9 | 15 | -98.8% |
| Banda 10Mbps | 10.3 | 0.1 | 0 | -100.0%* |
| Perda 0.5% | 21,147.1 | 1,818.9 | 91,269 | -56.4% |

*Limitado pelo próprio teste

### 3.2 Análise Detalhada por Cenário

#### 3.2.1 Cenário Baseline

**Resultados**:
- Throughput: 48.5 Gbps (média)
- Variabilidade: 2% (coeficiente de variação)
- Retransmissões: 76 (aceitável para alto throughput)

**Análise**:
O baseline demonstrou o desempenho máximo possível no ambiente Docker local. O throughput extremamente alto (~48 Gbps) é resultado da comunicação via memória compartilhada do kernel, não representando limitações de rede física. Este valor serve como referência para comparar o impacto relativo das diferentes condições.

#### 3.2.2 Janela TCP 256KB

**Resultados**:
- Throughput: 47.0 Gbps
- Impacto: -3% vs baseline
- Retransmissões: 0 (perfeito)

**Análise**:
A janela de 256KB apresentou desempenho ligeiramente inferior ao baseline, mas com a vantagem significativa de eliminar completamente as retransmissões. Isso sugere que, para redes de alta velocidade e baixa latência, uma janela bem dimensionada pode melhorar a confiabilidade sem sacrificar significativamente o throughput.

#### 3.2.3 Múltiplos Fluxos (4 Streams)

**Resultados**:
- Throughput: 48.1 Gbps
- Impacto: -0.7% vs baseline
- Retransmissões: 1 (excelente)

**Análise**:
Os 4 fluxos paralelos mantiveram throughput praticamente idêntico ao baseline com mínimas retransmissões. Em ambiente local, o paralelismo não trouxe ganhos significativos devido à ausência de gargalos reais, mas demonstrou estabilidade e baixa contenção entre fluxos.

#### 3.2.4 Alta Latência (50ms)

**Resultados**:
- Throughput: 583.3 Mbps
- Impacto: -98.8% vs baseline
- Retransmissões: 15

**Análise**:
A latência de 50ms causou o impacto mais dramático no desempenho. A redução de ~48 Gbps para ~583 Mbps demonstra a sensibilidade do TCP ao RTT elevado. Com a janela padrão do sistema, o BDP (Bandwidth-Delay Product) não foi adequadamente preenchido, resultando em subutilização severa da capacidade disponível.

**Cálculo do BDP**:
- BDP teórico = 48 Gbps × 50ms = 300 MB
- Janela necessária seria muito maior que o padrão

#### 3.2.5 Banda Limitada (10Mbps)

**Resultados**:
- Throughput: 10.3 Mbps
- Eficiência: 103% (ligeiramente acima do limite)
- Retransmissões: 0

**Análise**:
O TCP adaptou-se perfeitamente ao limite de banda imposto, atingindo 100% de utilização sem retransmissões. O throughput ligeiramente acima de 10 Mbps pode ser atribuído a overhead de medição ou burst inicial. Este cenário demonstra a capacidade do TCP de se adaptar a limitações explícitas de banda.

#### 3.2.6 Perda de Pacotes (0.5%)

**Resultados**:
- Throughput: 21.1 Gbps
- Impacto: -56.4% vs baseline
- Retransmissões: 91,269 (muito alto)

**Análise**:
Uma perda de apenas 0.5% reduziu o throughput pela metade e gerou número extremamente alto de retransmissões. Isso demonstra o impacto desproporcional que pequenas taxas de perda têm no desempenho TCP, especialmente em redes de alta velocidade onde o algoritmo de controle de congestionamento reage agressivamente às perdas.

### 3.3 Análise Comparativa

#### 3.3.1 Impacto Relativo das Condições

1. **Latência**: Impacto mais severo (-98.8%)
2. **Perda de Pacotes**: Impacto significativo (-56.4%)
3. **Limitação de Banda**: Impacto previsível (limitado ao valor configurado)
4. **Parâmetros TCP**: Impacto mínimo em rede local (-3% a -0.7%)

#### 3.3.2 Trade-offs Observados

- **Throughput vs Confiabilidade**: Janela 256KB reduziu throughput em 3% mas eliminou retransmissões
- **Paralelismo vs Complexidade**: 4 fluxos não melhoraram desempenho em rede local
- **Sensibilidade a RTT**: TCP padrão é extremamente sensível a latência sem ajustes de janela

### 3.4 Visualização dos Resultados

![Comparação de Throughput](../results/atv2/results/plots/atv2_throughput_comparison.png)

*Nota: O gráfico mostra claramente a hierarquia de impacto das diferentes condições de rede*

## 4. Conclusões

### 4.1 Principais Descobertas

1. **Latência domina o desempenho**: RTT elevado tem impacto desproporcional sem ajustes adequados
2. **Perdas degradam significativamente**: Mesmo 0.5% de perda reduz throughput pela metade
3. **Janela TCP bem dimensionada melhora confiabilidade**: Eliminação de retransmissões com impacto mínimo
4. **Limitações físicas são absolutas**: Banda limitada define teto intransponível

### 4.2 Recomendações Práticas

#### Para Redes Locais (RTT < 1ms)
- Usar configurações padrão do sistema
- Janela de 256KB para máxima confiabilidade
- Evitar paralelismo desnecessário

#### Para Redes WAN (RTT > 50ms)
- Calcular e configurar janela TCP baseada no BDP
- Janela mínima = Banda × RTT
- Considerar múltiplos fluxos para mitigar impacto de perdas

#### Para Redes com Perdas
- Implementar FEC (Forward Error Correction) na aplicação
- Usar protocolos mais resilientes (ex: QUIC)
- Múltiplos fluxos para diversificar risco

#### Para Redes com Banda Limitada
- Otimizar uso com compressão
- Implementar QoS apropriado
- Priorizar tráfego crítico

### 4.3 Limitações do Estudo

1. **Ambiente Docker**: Throughput irrealisticamente alto em testes locais
2. **Algoritmos de Congestionamento**: Apenas CUBIC foi testado
3. **Duração dos Testes**: 10 segundos podem não capturar comportamento de longo prazo
4. **Combinações**: Cenários testados individualmente, não em combinação

### 4.4 Trabalhos Futuros

1. **Testar BBR e outros algoritmos modernos**
2. **Avaliar cenários combinados** (ex: latência + perda)
3. **Testes em rede física** para validação
4. **Análise de fairness** entre fluxos competindo
5. **Impacto de buffer bloat** em redes reais

## 5. Referências

1. Jacobson, V. (1988). "Congestion avoidance and control"
2. Mathis, M. et al. (1997). "The macroscopic behavior of the TCP congestion avoidance algorithm"
3. Ha, S. et al. (2008). "CUBIC: A New TCP-Friendly High-Speed TCP Variant"
4. Docker Documentation. "Network drivers"
5. Linux TC Manual. "Traffic Control in Linux"

---

**Nota**: Este trabalho demonstrou quantitativamente como diferentes condições de rede impactam o desempenho TCP. Os resultados enfatizam a importância de compreender e configurar adequadamente os parâmetros TCP para cada ambiente específico de implantação.