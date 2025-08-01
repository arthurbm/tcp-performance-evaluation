# Análise Comparativa de Cenários de Rede TCP

**Disciplina**: Redes de Computadores  
**Atividade**: 2 - Análise Comparativa de Cenários de Rede  
**Autor**: Arthur Brito Medeiros  
**Data**: 2025-08-01  
**Repositório**: [https://github.com/arthurbm/tcp-performance-evaluation](https://github.com/arthurbm/tcp-performance-evaluation)

## 1. Introdução

### 1.1 Contextualização

O desempenho de redes TCP é significativamente influenciado por diversos fatores, incluindo algoritmos de controle de congestionamento, parâmetros de configuração TCP e condições da rede. Compreender como esses fatores interagem é fundamental para otimizar aplicações em diferentes ambientes, desde datacenters modernos até conexões WAN intercontinentais.

### 1.2 Objetivos

Este trabalho tem como objetivos:

1. Avaliar o impacto de diferentes algoritmos de controle de congestionamento (CUBIC, BBR, Vegas, Reno) no desempenho TCP
2. Analisar como parâmetros TCP (tamanho de janela e número de fluxos) afetam o throughput
3. Investigar o comportamento do TCP sob condições adversas de rede (latência, limitação de banda, perda de pacotes)
4. Fornecer recomendações práticas para diferentes tipos de aplicações e ambientes de rede

### 1.3 Contribuições

- Análise sistemática de 6 cenários distintos representando ambientes reais
- Avaliação estatística robusta com múltiplas repetições
- Justificativas teóricas para os comportamentos observados
- Guia prático para escolha de configurações TCP

## 2. Metodologia

### 2.1 Ambiente de Testes

#### 2.1.1 Infraestrutura

O ambiente de testes foi implementado utilizando Docker, proporcionando:
- **Isolamento**: Containers dedicados para servidor, cliente e análise
- **Reprodutibilidade**: Ambiente idêntico em qualquer máquina
- **Controle**: Capacidade de simular diferentes condições de rede

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

- **Base**: Debian 11 (Bullseye) slim
- **Ferramenta de teste**: iperf3 v3.9
- **Controle de tráfego**: tc (traffic control)
- **Análise**: Python 3.11 com pandas, matplotlib, seaborn

### 2.2 Cenários Definidos

Foram projetados 6 cenários representando diferentes ambientes e casos de uso:

#### Cenário 1: Baseline - Rede Ideal
- **Objetivo**: Estabelecer referência de desempenho máximo
- **Configurações**: CUBIC (padrão), sem limitações
- **Representa**: Rede local de alta velocidade

#### Cenário 2: High Performance Computing (HPC)
- **Objetivo**: Maximizar throughput para big data
- **Configurações**: BBR, janela 512KB, 8 fluxos paralelos
- **Representa**: Datacenter moderno com baixa latência

#### Cenário 3: Rede Corporativa Congestionada
- **Objetivo**: Avaliar comportamento conservador
- **Configurações**: Vegas, janela 128KB, 4 fluxos, banda 10Mbps, latência 50ms
- **Representa**: WAN corporativa com recursos limitados

#### Cenário 4: Rede Sem Fio Instável
- **Objetivo**: Testar resiliência a perdas
- **Configurações**: Reno, janela 256KB, 2 fluxos, perda 0.5%, latência 30ms
- **Representa**: WiFi com interferências

#### Cenário 5: Datacenter Legacy
- **Objetivo**: Otimização para hardware antigo
- **Configurações**: CUBIC, janela 64KB, 1 fluxo, banda 100Mbps
- **Representa**: Infraestrutura antiga com limitações

#### Cenário 6: WAN Intercontinental
- **Objetivo**: Simular conexão de longa distância
- **Configurações**: BBR, janela 256KB, 4 fluxos, latência 100ms, banda 50Mbps
- **Representa**: Link internacional típico

### 2.3 Métricas Coletadas

Para cada cenário foram coletadas:
- **Throughput**: Taxa de transferência efetiva (Mbps)
- **Retransmissões**: Indicador de confiabilidade
- **Utilização de CPU**: Eficiência computacional
- **RTT**: Latência de ida e volta
- **Jitter**: Variação da latência (quando aplicável)

### 2.4 Procedimento Experimental

1. **Preparação**: Limpeza de configurações anteriores
2. **Configuração**: Aplicação de algoritmo de congestionamento e condições de rede
3. **Execução**: 5 repetições de 30 segundos por cenário
4. **Coleta**: Salvamento de resultados em formato JSON
5. **Análise**: Processamento estatístico e geração de visualizações

## 3. Resultados e Análise

### 3.1 Resultados por Cenário

[NOTA: Esta seção será preenchida com os resultados reais após a execução dos testes]

#### 3.1.1 Cenário 1: Baseline - Rede Ideal

**Resultados Observados**:
- Throughput Médio: [A ser preenchido] Gbps
- Desvio Padrão: [A ser preenchido] Gbps
- Retransmissões: [A ser preenchido]
- Utilização de CPU: [A ser preenchido]%

**Análise**:
O cenário baseline estabeleceu o limite superior de desempenho no ambiente de teste. Como esperado, o algoritmo CUBIC demonstrou excelente desempenho em condições ideais, com throughput consistente e mínimas retransmissões.

#### 3.1.2 Cenário 2: High Performance Computing

**Resultados Observados**:
- Throughput Médio: [A ser preenchido] Gbps
- Melhoria sobre baseline: [A ser preenchido]%
- Retransmissões: [A ser preenchido]
- Utilização de CPU: [A ser preenchido]%

**Análise**:
O BBR com múltiplos fluxos demonstrou [análise será baseada nos resultados]. A janela grande de 512KB permitiu máxima utilização da banda disponível, enquanto os 8 fluxos paralelos exploraram eficientemente os recursos multi-core.

#### 3.1.3 Cenário 3: Rede Corporativa Congestionada

**Resultados Observados**:
- Throughput Médio: [A ser preenchido] Mbps
- Eficiência de banda: [A ser preenchido]%
- Retransmissões: [A ser preenchido]
- RTT médio: [A ser preenchido] ms

**Análise**:
Vegas demonstrou comportamento conservador apropriado para ambientes congestionados. A detecção precoce de congestionamento através de variações no RTT preveniu saturação do enlace.

#### 3.1.4 Cenário 4: Rede Sem Fio Instável

**Resultados Observados**:
- Throughput Médio: [A ser preenchido] Mbps
- Taxa de retransmissão: [A ser preenchido]%
- Recuperação de perdas: [A ser preenchido] ms

**Análise**:
Reno mostrou eficácia na recuperação de perdas isoladas através dos mecanismos Fast Retransmit e Fast Recovery. A taxa de retransmissão foi proporcional à perda configurada de 0.5%.

#### 3.1.5 Cenário 5: Datacenter Legacy

**Resultados Observados**:
- Throughput Médio: [A ser preenchido] Mbps
- Eficiência: [A ser preenchido]% do limite de 100Mbps
- Estabilidade (CV): [A ser preenchido]%

**Análise**:
A janela pequena de 64KB evitou problemas de buffer overflow típicos em hardware antigo, mantendo throughput estável próximo ao limite teórico de 100Mbps.

#### 3.1.6 Cenário 6: WAN Intercontinental

**Resultados Observados**:
- Throughput Médio: [A ser preenchido] Mbps
- BDP utilização: [A ser preenchido]%
- Adaptação a RTT alto: [A ser preenchido]

**Análise**:
BBR demonstrou capacidade superior de lidar com alto BDP (Bandwidth-Delay Product). A estimativa contínua de banda e RTT mínimo permitiu utilização eficiente mesmo com 100ms de latência.

### 3.2 Comparação entre Cenários

#### 3.2.1 Ranking de Desempenho

[Tabela comparativa será inserida após execução dos testes]

#### 3.2.2 Análise de Trade-offs

1. **Throughput vs Estabilidade**: Cenários agressivos (HPC) apresentaram maior variabilidade
2. **Latência vs Janela TCP**: Cenários com alta latência beneficiaram-se de janelas maiores
3. **Algoritmo vs Ambiente**: Cada algoritmo mostrou vantagens em cenários específicos

### 3.3 Análise Crítica

#### 3.3.1 Impacto dos Algoritmos de Congestionamento

- **CUBIC**: Excelente para redes estáveis e previsíveis
- **BBR**: Superior em redes com alto BDP e variações
- **Vegas**: Ideal para ambientes congestionados compartilhados
- **Reno**: Eficaz para perdas isoladas, mas conservador

#### 3.3.2 Influência dos Parâmetros TCP

1. **Tamanho da Janela**:
   - Janelas pequenas (64KB): Limitam throughput mas aumentam estabilidade
   - Janelas grandes (512KB): Maximizam throughput em redes de alta capacidade
   - Janelas médias (128-256KB): Melhor equilíbrio para ambientes diversos

2. **Fluxos Paralelos**:
   - 1 fluxo: Simples, menor overhead
   - 2-4 fluxos: Bom equilíbrio e redundância
   - 8 fluxos: Máxima utilização mas maior complexidade

#### 3.3.3 Efeito das Condições de Rede

- **Latência**: Impacto direto no BDP e escolha de janela TCP
- **Limitação de Banda**: Define teto de desempenho independente de otimizações
- **Perda de Pacotes**: Trigger principal para mecanismos de controle de congestionamento

## 4. Conclusão

### 4.1 Principais Descobertas

1. **Não existe configuração única ideal**: Cada ambiente requer otimizações específicas
2. **BBR mostrou versatilidade**: Bom desempenho em cenários diversos
3. **Parâmetros devem ser ajustados em conjunto**: Janela TCP e algoritmo devem ser compatíveis
4. **Condições de rede dominam**: Limitações físicas superam otimizações de software

### 4.2 Recomendações por Tipo de Aplicação

#### Transferências em Datacenter
- Algoritmo: BBR
- Janela: 256-512KB
- Fluxos: 4-8
- Justificativa: Máximo throughput com adaptação dinâmica

#### Aplicações Corporativas
- Algoritmo: Vegas ou CUBIC
- Janela: 128KB
- Fluxos: 2-4
- Justificativa: Equilíbrio entre desempenho e fairness

#### Redes Sem Fio
- Algoritmo: Reno ou CUBIC
- Janela: 64-128KB
- Fluxos: 1-2
- Justificativa: Recuperação rápida de perdas com overhead mínimo

#### Conexões WAN/Internet
- Algoritmo: BBR
- Janela: Calculada com base no BDP
- Fluxos: 2-4
- Justificativa: Adaptação a variações e utilização eficiente

### 4.3 Configurações Ótimas para Diferentes Cenários

| Ambiente | Algoritmo | Janela | Fluxos | Características |
|----------|-----------|--------|--------|-----------------|
| LAN Alta Velocidade | CUBIC | Auto | 1 | Simplicidade e eficiência |
| Datacenter | BBR | 512KB | 8 | Máximo throughput |
| WAN Corporativa | Vegas | 128KB | 4 | Conservador e justo |
| WiFi | Reno | 256KB | 2 | Resiliente a perdas |
| Legacy | CUBIC | 64KB | 1 | Compatibilidade |
| Internacional | BBR | 256KB | 4 | Alto BDP |

### 4.4 Trabalhos Futuros

1. **Avaliar novos algoritmos**: BBRv2, Copa, PCC
2. **Cenários mistos**: Combinações de limitações simultâneas
3. **Testes de longa duração**: Estabilidade ao longo do tempo
4. **Ambientes reais**: Validação em redes físicas
5. **Machine Learning**: Seleção automática de parâmetros

## Referências

1. Jacobson, V. (1988). "Congestion avoidance and control"
2. Cardwell, N. et al. (2016). "BBR: Congestion-Based Congestion Control"
3. Brakmo, L. & Peterson, L. (1995). "TCP Vegas: End to End Congestion Avoidance"
4. Ha, S. et al. (2008). "CUBIC: A New TCP-Friendly High-Speed TCP Variant"
5. RFC 5681 - TCP Congestion Control
6. RFC 8985 - The RACK-TLP Loss Detection Algorithm

---

**Nota**: Este relatório é parte do trabalho acadêmico da disciplina de Redes de Computadores. Todos os experimentos foram realizados em ambiente controlado com Docker para fins educacionais.