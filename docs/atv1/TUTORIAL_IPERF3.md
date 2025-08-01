Tutorial Completo: Importação
de Imagem Debian no KVM e
Avaliação de Desempenho
com iperf3, tc e Algoritmos de

Congestionamento
1. Preparação do Ambiente
1.1. Ativar Virtualização na BIOS

1. Reinicie o computador e entre na BIOS/UEFI (normalmente pressionando F2, Del ou a tecla indicada pelo fabricante).
2. Localize a opção de virtualização (geralmente em "Advanced", "CPU Configuration" ou "Security") e ative Intel VT-x ou
AMD-V.
3. Salve e saia da BIOS.
1.2. Instalar KVM, Libvirt e virt-manager no Host

Abra o terminal e execute:

sudo apt update
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager -y

1.3. Verificar Suporte à Virtualização e Serviço libvirt

Verifique se o processador suporta virtualização:

egrep -c '(vmx|svm)' /proc/cpuinfo

Verifique o status do libvirt:

sudo systemctl status libvirtd

2. Importando a Imagem Debian Pré-
instalada

2.1. Baixando a Imagem

Acesse Debian Cloud Images (https://cdimage.debian.org/cdimage/cloud/) e baixe a imagem QCOW2 da versão
desejada (ex.: Debian 11 "Bullseye").
De preferência, baixe a versão no-cloud. Nessa imagem você faz login como root e sem senha. Uma imagem
recomendada: https://cdimage.debian.org/cdimage/cloud/bullseye/latest/debian-11-nocloud-amd64.qcow2
(https://cdimage.debian.org/cdimage/cloud/bullseye/latest/debian-11-nocloud-amd64.qcow2)
2.2. Importando no virt-manager

1. Abra o Virtual Machine Manager (virt-manager) via menu ou com virt-manager no terminal. Se seu usuário nao
tiver permissões, abra com sudo virt-manager
2. Selecione "File" → "Import Existing Disk Image...".
3. Escolha a imagem QCOW2 baixada.
4. Configure:
Sistema Operacional: Debian.
Memória e CPUs: Exemplo, 1024 MB e 1 CPU.
Rede: Configure para "NAT", garantindo comunicação entre VMs.
5. Finalize e inicie a VM.

2.3. Criando Duas VMs: Servidor e Cliente

Crie duas VMs a partir da mesma imagem, copiando a mesma:
Renomeie uma para Debian_Servidor.qcow2.
Renomeie a outra para Debian_Cliente.qcow2.

3. Configurando as VMs e Instalando o

iperf3

3.1. Acessar as VMs e Realizar Login
Inicie ambas as VMs e faça login com o usuário padrão (ex.: "root", debian" ou "cloud-user").
3.2. Atualizar o Sistema
Em cada VM, execute:

sudo apt update

3.3. Instalar o iperf3

Em cada VM:

sudo apt install iperf3 -y

Verifique a instalação:

iperf3 --version

3.4. Instale o procps

Esse pacote serve pra usar o comando sysctl, que pode ser usado para alterar o algoritmo de controle de congestionamento.

sudo apt install procps -y

4. Configurando a Comunicação entre as

VMs

4.1. Verificar Endereços IP

Em cada VM, execute:

ip a
Anote o IP e o nome da interface (ex.: 192.168.0.110 e eth0 ou enp1s0).
4.2. Testar Conectividade
Na Debian_Cliente, execute:

ping <IP_da_VM_Servidor>

Deve haver respostas.

5. Testando Desempenho com iperf3 –

Testes Base e Modificações
5.1. Teste Base – Sem Modificações

1. Servidor: Na Debian_Servidor, inicie o iperf3:

iperf3 -s
2. Cliente: Na Debian_Cliente, execute:
iperf3 -c <IP_da_VM_Servidor> > output_base.txt
3. Análise:
Observe o throughput, tamanho da janela TCP (valor padrão) e outros parâmetros.
Esse será o teste de referência.
5.2. Modificando o Tamanho da Janela TCP
1. Cliente: Execute o teste com um tamanho de janela ajustado (por exemplo, 130K ou 256K):
iperf3 -c <IP_da_VM_Servidor> -w 256K > output_256K.txt
2. Análise:
Compare o throughput do output com o teste base.
Registre as diferenças e discuta se a alteração foi positiva ou não.
5.3. Alterando o Algoritmo de Controle de Congestionamento
1. Verificar Algoritmo Atual:
sysctl net.ipv4.tcp_congestion_control
2. Listar Algoritmos Disponíveis:

sysctl net.ipv4.tcp_available_congestion_control
3. Alterar o Algoritmo (ex.: para reno):

sudo sysctl -w net.ipv4.tcp_congestion_control=reno
4. Ativar outros algoritmos que estão disponíveis:
Caso um protocolo não esteja listado em /proc/sys/net/ipv4/tcp_available_congestion_control, tente
carregá-lo com:
sudo modprobe tcp_vegas # Para Vegas
sudo modprobe tcp_bbr # Para BBR
sudo modprobe tcp_westwood # Para Westwood
sudo modprobe tcp_htcp # Para HTCP
Depois, verifique se ele apareceu na lista:

cat /proc/sys/net/ipv4/tcp_available_congestion_control
Se aparecer, ative-o temporariamente:

sudo sysctl -w net.ipv4.tcp_congestion_control=vegas # Exemplo com vegas
5. Tornar a configuração permanente
Para manter o protocolo ativado após reinicialização:

echo "net.ipv4.tcp_congestion_control = bbr" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
6. Repetir o Teste:
Na Debian_Cliente, execute:

iperf3 -c <IP_da_VM_Servidor> > output_vegas.txt
7. Análise:
Compare os resultados com o teste base (com o algoritmo padrão, geralmente "cubic").
Discuta se a mudança no algoritmo de congestionamento influenciou o desempenho.
8. Observação:
Em testes entre VMs, ambos os lados podem influenciar, mas geralmente o algoritmo do lado do remetente
(cliente) tem impacto direto na taxa de envio.
5.4. Utilizando o tc para Simular Condições de Rede

1. Simular Atraso (Latência):
No Host ou na VM (se aplicável):
Para simular 100ms de atraso na interface (substitua eth0 pela interface correta):

sudo tc qdisc add dev eth0 root netem delay 100ms
2. Testar com Atraso:
Na Debian_Cliente, execute:

iperf3 -c <IP_da_VM_Servidor> > output_tc_delay.txt
3. Limitar a Banda de Transmissão:
Aplique a regra para limitar a banda a 1 Mbit/s:

sudo tc qdisc add dev eth0 root tbf rate 1mbit burst 32kbit latency 400ms
4. Testar com Limitação de Banda:
Execute o teste e salve o output:

iperf3 -c <IP_da_VM_Servidor> > output_tc_band.txt
5. Remover Configurações do tc:

sudo tc qdisc del dev eth0 root

6. Configurar SSH no Debian NoCloud e

Transferir Arquivos via SCP
Essa etapa é necessária para copiar os logs do iperf3 das VMs para o host.

1. Instalar e Ativar o SSH na VM

sudo apt update && sudo apt install ssh
sudo systemctl enable --now ssh
2. Configurar Senha para o Usuário Root

sudo passwd root

Defina uma senha para o root.
3. Modificar Configuração do SSH Edite o arquivo de configuração do SSH:

sudo nano /etc/ssh/sshd_config
Altere ou adicione as seguintes linhas:

PermitRootLogin yes
Salve e saia (CTRL+X, Y, Enter).
4. Reiniciar o Serviço SSH

sudo systemctl restart ssh
5. Obter o IP da VM

ip a

Anote o IP da interface de rede.

6. Conectar via SSH do Host

ssh root@IP_DA_VM

6.1. Transferir Arquivos com SCP

1. Copiar Arquivo da VM para o Host
scp root@IP_DA_VM:/caminho/do/arquivo /caminho/no/host
2. Copiar Arquivo do Host para a VM

scp /caminho/no/host root@IP_DA_VM:/caminho/de/destino

Agora, o SSH está configurado e os arquivos podem ser transferidos via SCP.