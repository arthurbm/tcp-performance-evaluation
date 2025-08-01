# Recomendações e Descobertas Adicionais

## Análise Executada em 26/07/2025

### 1. Descobertas Principais

#### ✅ Confirmações do REPORT.md
- A configuração ótima (256KB + 4 fluxos) realmente entrega 60.85 Gbps (+20.6%)
- Janelas pequenas (64K) degradam significativamente o desempenho (-15.3%)
- Janelas de 512K causam erro de buffer de socket consistentemente
- A escolha do Docker foi acertada para automação e reprodutibilidade

#### 🔍 Descobertas Adicionais

1. **Alta Variabilidade nas Retransmissões**
   - Baseline: 77.4 retransmissões médias (alta variabilidade)
   - Window 256K sozinha: 31.8 retransmissões
   - Combined (256K + 4 fluxos): 0 retransmissões
   - Isso sugere que a combinação de parâmetros não só melhora throughput mas também estabilidade

2. **Confiabilidade Estatística Variável**
   - Alguns testes têm muitas amostras (baseline: 7)
   - Outros têm poucas (combined: 1)
   - Recomenda-se padronizar em 3+ amostras para todos os cenários

3. **Padrão de Degradação com Janelas Pequenas**
   - 64K: -15.3% (degradação severa)
   - 128K: -2.9% (degradação leve)
   - 256K: -1.1% (praticamente igual ao baseline)
   - Sugere que 256K é o ponto ótimo antes dos problemas de buffer

### 2. Melhorias Implementadas

#### 📊 Visualização de Dados
- Criado script `generate-report-tables.py` para gerar tabelas formatadas
- Adicionados gráficos ASCII para melhor visualização
- Incluída análise de confiabilidade estatística

#### 📈 Análise Estatística Aprimorada
- Identificação clara de amostras insuficientes
- Cálculo de desvio padrão para avaliar consistência
- Recomendações baseadas em confiabilidade dos dados

### 3. Recomendações para Trabalhos Futuros

#### 🔧 Melhorias Técnicas

1. **Completar Testes Faltantes**
   ```bash
   # Algoritmos de congestionamento
   for algo in reno vegas bbr; do
     docker exec tcp-client bash -c "sysctl -w net.ipv4.tcp_congestion_control=$algo"
     docker exec tcp-client iperf3 -c 10.5.0.10 -t 30 -J
   done
   
   # Condições de rede
   docker exec tcp-client tc qdisc add dev eth0 root netem delay 100ms
   docker exec tcp-client iperf3 -c 10.5.0.10 -t 30 -J
   ```

2. **Análise de CPU e Memória**
   - Monitorar uso de recursos durante os testes
   - Correlacionar com throughput para identificar gargalos

3. **Testes de Longa Duração**
   - Executar testes de 5-10 minutos para avaliar estabilidade
   - Verificar se o desempenho se mantém consistente

#### 📝 Melhorias no Relatório

1. **Adicionar Seção de Limitações**
   - Throughput elevado devido a comunicação local
   - Falta de testes com alguns algoritmos de congestionamento
   - Variabilidade no número de amostras

2. **Incluir Análise de Custo-Benefício**
   - 4 fluxos usam mais recursos mas entregam +20% de throughput
   - Trade-off entre complexidade e desempenho

3. **Documentar Problemas Encontrados**
   - Erro de buffer com 512K (investigar limites do sistema)
   - Timeout em alguns testes combinados

### 4. Scripts de Automação Adicionais

#### Monitor de Desempenho em Tempo Real
```bash
#!/bin/bash
# monitor-performance.sh
while true; do
  echo "=== $(date) ==="
  docker exec tcp-client ss -i | grep tcp
  docker stats --no-stream tcp-server tcp-client
  sleep 5
done
```

#### Validador de Resultados
```python
# validate-results.py
import json
import glob

def validate_results():
    errors = []
    warnings = []
    
    for file in glob.glob("results/raw/*.json"):
        try:
            with open(file) as f:
                data = json.load(f)
                
            # Validações
            if "end" not in data or "sum_sent" not in data["end"]:
                warnings.append(f"{file}: Resultado incompleto")
                
            if data["end"]["sum_sent"]["retransmits"] > 1000:
                warnings.append(f"{file}: Alto número de retransmissões")
                
        except Exception as e:
            errors.append(f"{file}: {str(e)}")
    
    return errors, warnings
```

### 5. Conclusão

O projeto está muito bem estruturado e atende plenamente aos requisitos da atividade. As melhorias sugeridas são para:

1. **Aumentar a confiabilidade estatística** dos resultados
2. **Completar cenários de teste** não executados
3. **Melhorar a visualização** dos dados
4. **Documentar limitações** de forma transparente

O uso do Docker foi uma escolha excelente que demonstra maturidade técnica e visão de automação. O projeto serve como um ótimo exemplo de como realizar avaliações de desempenho de forma sistemática e reproduzível.

### 6. Comandos Úteis para Debugging

```bash
# Ver configurações TCP atuais
docker exec tcp-client sysctl net.ipv4.tcp_* | grep -E "(window|congestion|buffer)"

# Monitorar tráfego em tempo real
docker exec tcp-server tcpdump -i eth0 -n port 5201 -c 100

# Verificar estatísticas de rede
docker exec tcp-client netstat -s | grep -i tcp

# Analisar latência entre containers
docker exec tcp-client ping -c 100 -i 0.2 10.5.0.10 | tail -3
```

---

**Nota**: Este documento complementa o REPORT.md com descobertas da execução real e sugestões de melhoria contínua.