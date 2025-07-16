# JMON - Advanced Monitoring System

> **🌐 Language**: [Português (PT-BR)](README.pt.md) | **English**

Distributed monitoring system using AMQP/RabbitMQ for client-server communication, with email alerts and log file monitoring support.

## 🚀 Features

### Service Monitoring
- ✅ **Connectivity (ICMP/Ping)** - Monitor host availability
- ✅ **TCP/UDP Ports** - Check if services are listening
- ✅ **HTTP Services** - Test HTTP/HTTPS connectivity
- ✅ **Local Services** - Monitor via netstat

### File Monitoring
- ✅ **Real-time Logs** - Continuously monitor log files
- ✅ **Regex Patterns** - Apply multiple patterns to detect events
- ✅ **Smart Alerts** - Detect errors, exceptions and critical events

### Alert System
- ✅ **Configurable Alerts** - Customizable triggers (up/down/regex)
- ✅ **Email Notifications** - Automatic sending to sys-admin
- ✅ **Multiple SMTP Providers** - Gmail, Outlook, Yahoo, etc.

### Communication & Architecture
- ✅ **AMQP/RabbitMQ** - Robust and reliable communication
- ✅ **Distributed** - Multiple clients, centralized server
- ✅ **IPv4/IPv6** - Complete support for both protocols

## 📁 Project Structure

```
jmon/
├── jmon.py                     # Main script (client and server)
├── env.server.yaml             # [Template] Server configuration
├── env.client.yaml             # [Template] Client configuration
├── profiles/                   # Monitoring profiles per client
│   └── example-alias.yaml      # Configuration example
├── requirements.txt            # Python dependencies
├── README.md                   # This file
```

## 🛠️ Installation

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure RabbitMQ
```bash
# Ubuntu/Debian
sudo apt-get install rabbitmq-server

# CentOS/RHEL
sudo yum install rabbitmq-server

# Start service
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server
```

### 3. Configure files
#### 3.1 - Server:
- Create `env.ser.yaml` file using `env.server.yaml` template with server and email settings
- Configure profiles in `profiles/` for each client
#### 3.2 - Client:
- Create `env.yaml` file using `env.client.yaml` template with client settings

## 🚀 Usage

### Start Server
```bash
python jmon.py -s
```

### Start Client
```bash
python jmon.py
```

## ⚙️ Configuration

### Server (env.server.yaml)
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
  username: your_email@gmail.com
  password: your_app_password
  use_tls: true
  sys_admin_email: admin@company.com
```

### Client (env.client.yaml)
```yaml
server:
  host: 'server.company.com'
  port: 5656

alias: "client-01"

amqp:
  userid: guest
  password: guest
```

### Monitoring Profile (profiles/client-01.yaml)
```yaml
client:
  host: 192.168.1.100

service:
  # Connectivity monitoring
  - ping: 8.8.8.8
    topic: "ping-google"
    trigger: 
      down: 3
      up: 3

  # Port monitoring
  - local: service-port
    tcp: 80
    topic: "web-server"
    trigger: 
      down: 2
      up: 2

  # Log file monitoring
  - local: file-content
    content: /var/log/apache2/error.log
    topic: "apache-errors"
    trigger: 
      - "\\[error\\]"
      - "\\[crit\\]"
      - "500 Internal Server Error"
```

## 📊 Supported Monitoring Types

| Type | Configuration | Description |
|------|-------------|-----------|
| **ICMP Ping** | `ping: hostname` | Test connectivity via ping |
| **TCP Port** | `http: host` + `port: 80` | Test TCP connection |
| **Local Service** | `local: service-port` + `tcp: 80` | Check local service via netstat |
| **File Content** | `local: file-content` + `content: /path/file.log` | Monitor file with regex |

## 🔔 Alert Types

### Status Alerts (UP/DOWN)
```yaml
trigger:
  down: 3  # Alert after 3 consecutive failures
  up: 2    # Alert after 2 consecutive successes
```

### File Alerts (Regex)
```yaml
trigger:
  - "ERROR"
  - "CRITICAL"
  - "\\[error\\]"
  - "Exception"
```

## 📈 Logs and Monitoring

### Server Logs
```
[EMAIL] Notifier configured to send alerts to: admin@company.com
[FILE-MONITOR] Match found in /var/log/app.log: ERROR: Database connection failed
FILE ALERT: client-01 -> app-errors - Pattern detected
[EMAIL] File alert sent to admin@company.com
```

### Client Logs
```
Queue instantiated /client-01/ping-google with 0 message(s) and 0 consumer(s)
Queue instantiated /client-01/app-errors with 0 message(s) and 0 consumer(s)
.....
```

## 🔧 Troubleshooting

### Common Issues

1. **AMQP connection fails**
   - Check if RabbitMQ is running
   - Confirm credentials in `env.ser.yaml`

2. **Emails not sent**
   - Check SMTP settings
   - Use app passwords for Gmail

3. **File not monitored**
   - Check read permissions
   - Confirm file path

4. **Regex not working**
   - Test regex in online validator
   - Escape special characters with `\\`

## 🤝 Contributing

1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is under the MIT license. See the [LICENSE](LICENSE) file for details.