# 🤖 Controle de Garra Robótica com Raspberry Pi 4 + ROS 2 + UR7e

> Tutorial completo para acionar um servomotor (garra robótica) a partir de um cobot **Universal Robots UR7e** (PolyScope X), usando uma **Raspberry Pi 4** rodando **ROS 2 Humble** e uma placa **PCA9685** para gerar o sinal PWM.

**Por [Dr. da Robótica](https://www.youtube.com/@DrdaRobotica)** · `#DaEscolaAIndustria`

---

## 📋 Sumário

- [Visão Geral](#-visão-geral)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Lista de Materiais](#-lista-de-materiais)
- [Parte 1 — Instalar o Ubuntu na Raspberry Pi 4](#parte-1--instalar-o-ubuntu-na-raspberry-pi-4)
- [Parte 2 — Instalar o ROS 2 Humble](#parte-2--instalar-o-ros-2-humble)
- [Parte 3 — Conexão e Acesso Remoto](#parte-3--conexão-e-acesso-remoto)
- [Parte 4 — Ligar a PCA9685 e o Servo](#parte-4--ligar-a-pca9685-e-o-servo)
- [Parte 5 — Testar o Servo Isolado](#parte-5--testar-o-servo-isolado)
- [Parte 6 — Criar o Pacote ROS 2](#parte-6--criar-o-pacote-ros-2)
- [Parte 7 — Servidor TCP para o UR7e](#parte-7--servidor-tcp-para-o-ur7e)
- [Parte 8 — Programar o UR7e (PolyScope X)](#parte-8--programar-o-ur7e-polyscope-x)
- [Parte 9 — Rede com Switch](#parte-9--rede-com-switch)
- [Solução de Problemas](#-solução-de-problemas)
- [Licença](#-licença)

---

## 🎯 Visão Geral

Este projeto demonstra como um cobot UR7e pode acionar uma garra robótica baseada em servomotor, enviando comandos de ângulo via socket TCP para uma Raspberry Pi. A Pi recebe o comando, publica em um tópico ROS 2 e move o servo através da placa PCA9685.

O resultado é uma garra de baixo custo, **open-source**, integrável ao end effector do robô.

---

## 🏗 Arquitetura do Sistema

```
┌─────────────────┐   socket TCP    ┌──────────────────────┐
│  UR7e           │   porta 5000    │  Raspberry Pi 4      │
│  (PolyScope X)  │ ──────────────► │  tcp_server (ROS 2)  │
│  192.168.2.21   │                 │  192.168.2.20        │
└─────────────────┘                 └──────────┬───────────┘
                                                │ tópico /servo_angle
                                                ▼
                                     ┌──────────────────────┐
                                     │  servo_node (ROS 2)  │
                                     └──────────┬───────────┘
                                                │ I2C
                                                ▼
                                     ┌──────────────────────┐
                                     │  PCA9685             │
                                     └──────────┬───────────┘
                                                │ PWM
                                                ▼
                                     ┌──────────────────────┐
                                     │  Servo MG995 (garra) │
                                     └──────────────────────┘
```

---

## 🛒 Lista de Materiais

| Item | Especificação | Observação |
|------|---------------|------------|
| Raspberry Pi 4 | Qualquer versão de RAM | 64-bit obrigatório p/ ROS 2 |
| Cartão microSD | 32 GB, Classe 10 / A1 | Endurance recomendado |
| Fonte da Pi | 5V / 3A USB-C | Oficial recomendada |
| Placa PWM | PCA9685 (16 canais, I2C) | |
| Servomotor | MG995 | Largura de pulso 500–2500 µs |
| Fonte externa | 5V | Para alimentar o servo (V+) |
| Switch de rede | TP-Link TL-SG1008P (ou similar) | Gigabit |
| Cabos RJ45 | — | Para Pi, UR7e e PC |
| Cobot | Universal Robots UR7e | PolyScope X |

> ⚠️ **Atenção ao GND comum:** o GND da fonte externa do servo **deve** estar ligado ao GND da Raspberry Pi. Sem essa referência comum, o sinal PWM não funciona.

---

## Parte 1 — Instalar o Ubuntu na Raspberry Pi 4

### 1.1 Gravar o cartão SD

1. Baixe o **Raspberry Pi Imager** em [raspberrypi.com/software](https://www.raspberrypi.com/software/)
2. **Choose Device** → Raspberry Pi 4
3. **Choose OS** → *Other general-purpose OS* → *Ubuntu* → **Ubuntu Server 22.04.x LTS (64-bit)**
4. **Choose Storage** → selecione o cartão SD

> 📌 **Versão obrigatória:** Ubuntu **22.04 LTS (64-bit)**. Outras versões (24.04, 25.10) **não** são compatíveis com ROS 2 Humble.

### 1.2 Configurações (engrenagem ⚙️)

| Configuração | Valor |
|--------------|-------|
| Hostname | `UNIFEBE` (ou o que preferir) |
| Username | `unifebe` |
| Password | mínimo 8 caracteres, 1 maiúscula, 1 número (ex.: `Ubuntu1234`) |
| Wi-Fi | SSID + senha da rede |
| Country | `BR` |
| Enable SSH | ✅ Ativado — *Use password authentication* |

> ⚠️ A senha **não pode** ser igual ao username (ex.: `admin/admin` é rejeitado).

### 1.3 Sistema de arquivos

O Imager formata automaticamente: partição `/boot` em **FAT32** e raiz `/` em **ext4**. Não é necessário formatar o cartão antes.

### 1.4 Primeiro boot

Insira o SD, ligue a Pi e aguarde ~60 segundos. No login use o usuário e senha configurados.

---

## Parte 2 — Instalar o ROS 2 Humble

Após o primeiro login, atualize o sistema:

```bash
sudo apt update && sudo apt upgrade -y
```

> Durante o `upgrade`, pode aparecer a tela *"Daemons using outdated libraries"*. Apenas pressione **Enter** em `<Ok>` mantendo as opções como estão.

### 2.1 Configurar locale

```bash
sudo apt install locales -y
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### 2.2 Adicionar o repositório do ROS 2

```bash
sudo apt install software-properties-common curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
```

### 2.3 Instalar o ROS 2 Humble (Bare Bones)

```bash
sudo apt install ros-humble-ros-base -y
```

> A versão `ros-base` (Bare Bones) é mais leve e ideal para a Raspberry Pi. A instalação pode levar 10–15 minutos.

### 2.4 Configurar o `.bashrc`

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=1" >> ~/.bashrc
source ~/.bashrc
```

### 2.5 Verificar a instalação

```bash
ros2 --help
```

Se aparecer a lista de comandos (`launch`, `node`, `topic`, `run`...), o ROS 2 está instalado corretamente.

---

## Parte 3 — Conexão e Acesso Remoto

### 3.1 Descobrir o IP da Pi

```bash
ip addr show wlan0   # via Wi-Fi
ip addr show eth0    # via cabo
```

### 3.2 Acessar via SSH (do seu computador)

```bash
ssh unifebe@<IP_DA_PI>
```

> 💡 A senha não aparece na tela enquanto digita — é comportamento normal do terminal.

### 3.3 Habilitar o I2C

```bash
sudo nano /boot/firmware/config.txt
```

Verifique se a linha abaixo existe (geralmente já vem habilitada no Ubuntu para Pi):

```
dtparam=i2c_arm=on
```

Se não existir, adicione, salve (**Ctrl+X → Y → Enter**) e reinicie com `sudo reboot`.

---

## Parte 4 — Ligar a PCA9685 e o Servo

### 4.1 PCA9685 → Raspberry Pi 4

| PCA9685 | Raspberry Pi 4 (pino físico) |
|---------|------------------------------|
| VCC | Pino 1 (3.3V) — alimenta o chip I2C |
| GND | Pino 6 (GND) |
| SDA | Pino 3 (SDA) |
| SCL | Pino 5 (SCL) |

### 4.2 Alimentação do servo

| PCA9685 | Fonte externa 5V |
|---------|------------------|
| V+ (terminal verde) | +5V |
| GND (terminal verde) | GND |

> 🔴 **CRÍTICO:** ligue também um fio do **GND da fonte externa ao GND da Raspberry Pi**. Sem esse GND comum, o servo não responde mesmo com tudo aparentemente correto.

### 4.3 Servo MG995 → canal 0 da PCA9685

| Fio do servo | Pino da PCA9685 (canal 0) |
|--------------|---------------------------|
| Laranja/Amarelo (sinal) | PWM (S) |
| Vermelho (+) | V+ |
| Marrom/Preto (−) | GND |

### 4.4 Verificar a detecção I2C

```bash
sudo apt install i2c-tools -y
sudo i2cdetect -y 1
```

Deve aparecer os endereços `40` e `70` na tabela — confirmando que a PCA9685 foi detectada.

---

## Parte 5 — Testar o Servo Isolado

Instale as bibliotecas necessárias:

```bash
sudo apt install python3-pip -y
pip3 install adafruit-circuitpython-servokit
sudo apt install python3-rpi.gpio -y
```

> Se o `pip3` der `ModuleNotFoundError: No module named 'RPi'`, instale via apt: `sudo apt install python3-rpi.gpio -y`.

Crie o script de teste `teste_servo.py` (ver pasta [`scripts/`](scripts/)) e rode:

```bash
python3 ~/teste_servo.py
```

O servo deve alternar entre 0°, 90° e 180°.

---

## Parte 6 — Criar o Pacote ROS 2

### 6.1 Criar o workspace e o pacote

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
ros2 pkg create servo_control --build-type ament_python --dependencies rclpy std_msgs
```

### 6.2 Criar o nó do servo

Copie o arquivo [`servo_node.py`](ros2_ws/src/servo_control/servo_control/servo_node.py) para:
`~/ros2_ws/src/servo_control/servo_control/servo_node.py`

### 6.3 Registrar o nó no `setup.py`

Na seção `entry_points`:

```python
entry_points={
    'console_scripts': [
        'servo_node = servo_control.servo_node:main',
        'tcp_server = servo_control.tcp_server:main',
    ],
},
```

### 6.4 Compilar

```bash
sudo apt install python3-colcon-common-extensions -y
cd ~/ros2_ws
colcon build --packages-select servo_control
```

### 6.5 Testar o nó

**Terminal 1:**
```bash
source ~/ros2_ws/install/setup.bash
ros2 run servo_control servo_node
```

**Terminal 2:**
```bash
source ~/ros2_ws/install/setup.bash
ros2 topic pub /servo_angle std_msgs/msg/Float32 "data: 90.0" --once
```

O servo deve mover para 90°.

---

## Parte 7 — Servidor TCP para o UR7e

Copie o arquivo [`tcp_server.py`](ros2_ws/src/servo_control/servo_control/tcp_server.py) para:
`~/ros2_ws/src/servo_control/servo_control/tcp_server.py`

Recompile:

```bash
cd ~/ros2_ws
colcon build --packages-select servo_control
```

Rode os dois nós em terminais separados:

**Terminal 1 — controla o servo:**
```bash
source ~/ros2_ws/install/setup.bash
ros2 run servo_control servo_node
```

**Terminal 2 — recebe comandos do UR7e:**
```bash
source ~/ros2_ws/install/setup.bash
ros2 run servo_control tcp_server
```

### Teste manual (simulando o UR7e)

De outro computador na rede:

```bash
nc 192.168.2.20 5000
```

Digite `90` e pressione Enter — o servo deve se mover.

---

## Parte 8 — Programar o UR7e (PolyScope X)

O script [`garra_control.script`](ur_script/garra_control.script) usa as funções de socket documentadas no *Script Directory* do PolyScope X:

```
def controla_garra(angulo):
  local connected = socket_open("192.168.2.20", 5000, "socket_garra")
  if connected:
    socket_send_line(to_str(angulo), "socket_garra")
    sleep(0.5)
    socket_close("socket_garra")
  else:
    popup("Erro: nao foi possivel conectar na Raspberry Pi", "Erro Garra", error=True, blocking=False)
  end
end

# Abre garra
controla_garra(90)
sleep(1.0)

# Fecha garra
controla_garra(0)
sleep(1.0)
```

### Como carregar no robô

1. Copie o arquivo `.script` para um pendrive (formato FAT32)
2. No PolyScope X, vá em **Ficheiros Script** (não em "Programa")
3. Selecione o pendrive e carregue o arquivo

> 💡 As funções `socket_open`, `socket_send_line` (adiciona `\n` automaticamente) e `socket_close` seguem o manual oficial da UR. O `to_str()` converte o número para string.

> ℹ️ É **normal** o log do servidor mostrar `Connection reset by peer` após cada comando — o script fecha a conexão a cada envio (`socket_close`).

---

## Parte 9 — Rede com Switch

Como o switch não distribui IP automaticamente (sem DHCP), use IPs fixos na mesma faixa:

| Dispositivo | IP fixo |
|-------------|---------|
| Raspberry Pi (eth0) | `192.168.2.20` |
| UR7e | `192.168.2.21` |
| Computador | `192.168.2.30` |

### IP fixo na Raspberry Pi (Netplan)

```bash
sudo nano /etc/netplan/50-cloud-init.yaml
```

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      dhcp6: false
      optional: true
      addresses: [192.168.2.20/24]
  wifis:
    wlan0:
      dhcp4: true
      optional: true
      access-points:
        "NOME_DA_REDE":
          auth:
            key-management: none
      regulatory-domain: BR
```

```bash
sudo netplan apply
```

### IP fixo no UR7e

No PolyScope X: **Configurações → Sistema → Rede → Estático**

| Campo | Valor |
|-------|-------|
| IP | `192.168.2.21` |
| Máscara | `255.255.255.0` |
| Gateway | `192.168.2.1` |

### Testar comunicação

```bash
ping 192.168.2.20   # Pi
ping 192.168.2.21   # UR7e
```

---

## 🔧 Solução de Problemas

| Problema | Causa | Solução |
|----------|-------|---------|
| `raspi-config: command not found` | É comando do Raspberry Pi OS | Edite `/boot/firmware/config.txt` manualmente |
| Senha rejeitada no Imager | Senha igual ao usuário | Use senha forte e diferente |
| Servo não responde | Falta GND comum | Ligue GND da fonte externa ao GND da Pi |
| `No module named 'RPi'` | Lib ausente | `sudo apt install python3-rpi.gpio -y` |
| `pip3` timeout | Pi sem internet | Verifique DNS / Wi-Fi |
| `Temporary failure in name resolution` | DNS quebrado | `sudo bash -c 'echo "nameserver 8.8.8.8" > /etc/resolv.conf'` |
| `ssh: Operation timed out` | IP mudou (DHCP) ou rede isolada | Verifique IP atual; use switch/IP fixo |
| UR7e não conecta | `tcp_server` não está rodando | Inicie os dois nós na Pi |
| `Connection reset by peer` | Normal | O script fecha a conexão após cada envio |

---

## 📁 Estrutura do Repositório

```
teleop-garra-ur7e/
├── README.md
├── LICENSE
├── scripts/
│   └── teste_servo.py
├── ros2_ws/
│   └── src/
│       └── servo_control/
│           └── servo_control/
│               ├── servo_node.py
│               └── tcp_server.py
└── ur_script/
    └── garra_control.script
```

---

## 📄 Licença

Este projeto é **open-source** sob a licença [MIT](LICENSE).

---

**Dr. da Robótica** · `#DaEscolaAIndustria`
Desenvolvido para fins educacionais em robótica colaborativa e automação industrial.
