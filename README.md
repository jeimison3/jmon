# JMON - Sistema de Monitoramento Avançado

Sistema de monitoramento distribuído usando AMQP/RabbitMQ para comunicação entre clientes e servidor, com suporte a alertas por e-mail e monitoramento de arquivos de log.

## 🚀 Funcionalidades

### Monitoramento de Serviços
- ✅ **Conectividade (ICMP/Ping)** - Monitora disponibilidade de hosts
- ✅ **Portas TCP/UDP** - Verifica se serviços estão escutando
- ✅ **Serviços HTTP** - Testa conectividade HTTP/HTTPS
- ✅ **Serviços Locais** - Monitora via netstat

### Monitoramento de Arquivos
- ✅ **Logs em Tempo Real** - Monitora arquivos de log continuamente
- ✅ **Padrões Regex** - Aplica múltiplos padrões para detectar eventos
- ✅ **Alertas Inteligentes** - Detecta erros, exceções e eventos críticos

### Sistema de Alertas
- ✅ **Alertas Configuráveis** - Triggers personalizáveis (up/down/regex)
- ✅ **Notificações por E-mail** - Envio automático para sys-admin
- ✅ **Múltiplos Provedores SMTP** - Gmail, Outlook, Yahoo, etc.

### Comunicação e Arquitetura
- ✅ **AMQP/RabbitMQ** - Comunicação robusta e confiável
- ✅ **Distribuído** - Múltiplos clientes, servidor centralizado
- ✅ **IPv4/IPv6** - Suporte completo para ambos protocolos

## 📁 Estrutura do Projeto

```
jmon/
├── jmon.py                     # Script principal (cliente e servidor)
├── env.server.yaml             # [Template] Configuração do servidor
├── env.client.yaml             # [Template] Configuração do cliente
├── profiles/                   # Perfis de monitoramento por cliente
│   └── example-alias.yaml      # Exemplo de configuração
├── requirements.txt            # Dependências Python
├── README.md                   # Este arquivo
```

## 🛠️ Instalação

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar RabbitMQ
```bash
# Ubuntu/Debian
sudo apt-get install rabbitmq-server

# CentOS/RHEL
sudo yum install rabbitmq-server

# Iniciar serviço
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server
```

### 3. Configurar arquivos
#### 3.1 - Servidor:
- Crie o arquivo `env.ser.yaml` usando o modelo `env.server.yaml` com configurações do servidor e e-mail.
- Configure profiles em `profiles/` para cada cliente
#### 3.2 - Cliente:
- Crie o arquivo `env.yaml` usando o modelo `env.client.yaml` com configurações do cliente.


## 🚀 Uso

### Iniciar Servidor
```bash
python jmon.py -s
```

### Iniciar Cliente
```bash
python jmon.py
```

## ⚙️ Configuração

### Servidor (env.server.yaml)
```yaml
server:
  port: 5656

amqp:
  host: '[::]'
  userid: guest
  password: guest

email:
  smtp_server: smtp.gmail.com
  smtp_port: 587
  username: seu_email@gmail.com
  password: sua_senha_de_app
  use_tls: true
  sys_admin_email: admin@empresa.com
```

### Cliente (env.client.yaml)
```yaml
server:
  host: 'servidor.empresa.com'
  port: 5656

alias: "cliente-01"

amqp:
  userid: guest
  password: guest
```

### Profile de Monitoramento (profiles/cliente-01.yaml)
```yaml
client:
  host: 192.168.1.100

service:
  # Monitoramento de conectividade
  - ping: 8.8.8.8
    topic: "ping-google"
    trigger: 
      down: 3
      up: 3

  # Monitoramento de porta
  - local: service-port
    tcp: 80
    topic: "web-server"
    trigger: 
      down: 2
      up: 2

  # Monitoramento de arquivo de log
  - local: file-content
    content: /var/log/apache2/error.log
    topic: "apache-errors"
    trigger: 
      - "\\[error\\]"
      - "\\[crit\\]"
      - "500 Internal Server Error"
```

## 📊 Tipos de Monitoramento Suportados

| Tipo | Configuração | Descrição |
|------|-------------|-----------|
| **ICMP Ping** | `ping: hostname` | Testa conectividade via ping |
| **TCP Port** | `http: host` + `port: 80` | Testa conexão TCP |
| **Local Service** | `local: service-port` + `tcp: 80` | Verifica serviço local via netstat |
| **File Content** | `local: file-content` + `content: /path/file.log` | Monitora arquivo com regex |

## 🔔 Tipos de Alertas

### Alertas de Status (UP/DOWN)
```yaml
trigger:
  down: 3  # Alerta após 3 falhas consecutivas
  up: 2    # Alerta após 2 sucessos consecutivos
```

### Alertas de Arquivo (Regex)
```yaml
trigger:
  - "ERROR"
  - "CRITICAL"
  - "\\[error\\]"
  - "Exception"
```

## 📈 Logs e Monitoramento

### Logs do Servidor
```
[EMAIL] Notificador configurado para enviar alertas para: admin@empresa.com
[FILE-MONITOR] Match encontrado em /var/log/app.log: ERROR: Database connection failed
ALERTA DE ARQUIVO: cliente-01 -> app-errors - Padrão detectado
[EMAIL] Alerta de arquivo enviado para admin@empresa.com
```

### Logs do Cliente
```
Instanciada fila /cliente-01/ping-google com 0 mensagem(s) e 0 consumidor(es)
Instanciada fila /cliente-01/app-errors com 0 mensagem(s) e 0 consumidor(es)
.....
```

## 🔧 Troubleshooting

### Problemas Comuns

1. **Conexão AMQP falha**
   - Verifique se RabbitMQ está rodando
   - Confirme credenciais em `env.ser.yaml`

2. **E-mails não enviados**
   - Verifique configurações SMTP
   - Use senhas de aplicativo para Gmail

3. **Arquivo não monitorado**
   - Verifique permissões de leitura
   - Confirme caminho do arquivo

4. **Regex não funciona**
   - Teste regex em validador online
   - Escape caracteres especiais com `\\`

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.