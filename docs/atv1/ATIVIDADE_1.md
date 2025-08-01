Atividade 1: Desafio de Avaliação de Desempenho
Pedro R. Ximenes do Carmo
•
8 de jul. (editado: 24 de jul.)
100 pontos
Data de entrega: 24 de jul., 23:59
Objetivo
Cada aluno deverá configurar duas máquinas virtuais, denominadas "Servidor" e "Cliente", para realizar testes de desempenho com o iperf3. O objetivo é identificar, de forma experimental, a configuração ideal que maximize o throughput e minimize a latência da conexão entre as VMs. Os testes devem considerar variações no tamanho da janela TCP e no número de fluxos simultâneos.

Tutorial de Apoio

Está disponível em anexo o tutorial "Importação de Imagem Debian no KVM e Avaliação de Desempenho com iperf3, tc e Algoritmos de Congestionamento".
Esse material foi incluído como apoio para:
Facilitar a configuração do ambiente com KVM e Debian;
Incluir os comandos de configuração de rede, geração de tráfego com iperf3, e uso do tc para controle de banda e latência;
Disponibilizar o link para download da imagem Debian já preparada para o KVM.
O uso dessa plataforma (Debian com KVM) é sugerido, mas não obrigatório. Caso o aluno prefira utilizar outra solução de virtualização (como Docker, VirtualBox, VMware, entre outras), pode fazê-lo, desde que descreva claramente o ambiente no relatório.

Cenários de Experimentos

Os testes deverão contemplar pelo menos quatro cenários diferentes, combinando:
Tamanhos de janela TCP: exemplos — 64K, 128K, 256K, 512K;
Número de fluxos simultâneos: exemplos — 1, 2, 4, 8 fluxos.
Obs: Outros valores podem ser usados a seu critério.

Procedimento sugerido
Executar um teste base com os parâmetros padrão do iperf3 para comparação;
Variar o tamanho da janela TCP e observar o impacto no throughput;
Aumentar o número de fluxos simultâneos e registrar os resultados;
Comparar os resultados e justificar qual configuração apresentou o melhor desempenho com base em conceitos de redes (como congestionamento, largura de banda e RTT).
Requisitos para a entrega (Relatório)
O relatório deverá conter:
Tabela com os resultados dos testes (throughput, latência, parâmetros utilizados);
Comparação entre os diferentes cenários experimentais;
Justificativa para a configuração com melhor desempenho;
Descrição clara do ambiente utilizado (tipo de virtualização, sistema operacional, ferramentas, etc.).
O relatório deve ser entregue individualmente.