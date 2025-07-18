# pip install pyyaml
import yaml
import argparse
import socket
from threading import Thread, Event
import signal
import os
from typing import List

import subprocess
import sys

import amqp
import time
import yaml.serializer
import requests
from datetime import datetime, timezone, timedelta

exit_event = Event()

parser = argparse.ArgumentParser()
parser.add_argument("-s","--server", help="Inicia como servidor", action="store_true")
args = parser.parse_args()

server_profiles = {}

def get_current_timestamp() -> float:
    return time.time()


def signal_handler(signum, frame):
    print("Terminando...")
    global exit_event
    exit_event.set()


def resolveIP(host):
    ''' Resolução de Host -> IPv4 + IPv6 ou diretamente '''
    ipv4 = ""
    ipv6 = ""
    try:
        addresses = socket.getaddrinfo(host, None, socket.AF_INET)
        ipv4 = str(addresses[-1][4][0])
    except:
        pass
    try:
        addresses_v6 = socket.getaddrinfo(host, None, socket.AF_INET6)
        ipv6 = str(addresses_v6[-1][4][0])
    except:
        pass
    return ipv4, ipv6

class ClientsServerMonitor:
    def __init__(self):
        self.aliases = {}
        pass
    
    def addEvent(self, alias:str, topic:str, headers:dict, profile_service: list, timestamp:int):
        # print( (alias, topic, headers, timestamp, profile_service) )
        if not (alias in self.aliases.keys()):
            self.aliases[alias] = {}
        if not (topic in self.aliases[alias].keys()):
            self.aliases[alias][topic] = {
                'value': headers['return'],
                'count': 1
            }
        elif topic in self.aliases[alias].keys():
            if self.aliases[alias][topic]['value'] == headers['return']:
                self.aliases[alias][topic]['count']+=1
                
        _NOTIFY = False
        # HTTP or Ping or service-port
        if (('http' in profile_service) and ('port' in profile_service)) or ('ping' in profile_service) or (('local' in profile_service) and (profile_service['local'] == 'service-port')):
            if headers['return'] == 0:
                if "down" in profile_service['trigger']:
                    if profile_service['trigger']["down"] == self.aliases[alias][topic]['count']: # Valor de alerta atingido:
                        _NOTIFY = True
            elif headers['return'] == 1:
                if "up" in profile_service['trigger']:
                    if profile_service['trigger']["up"] == self.aliases[alias][topic]['count']: # Valor de alerta atingido:
                        _NOTIFY = True
        
        if _NOTIFY:
            print(F"ALERTA: {alias} -> {topic} ESTÁ {'UP' if headers['return'] else 'DOWN'}")
    
class Consulta:
    ''' Estrutura básica de uma Consulta. '''
    topic : str = ""
    
    def __init__(self, topic:str):
        self.topic = topic
        pass
    
    def name(self) -> str:
        pass
    
    def run(self) -> bool:
        ''' Procedimento que verifica se houve sucesso ou falha '''
        pass

class ConsultaTCP(Consulta):
    def __init__(self, topic:str, host:str, port:int):
        self.topic = topic
        self.host = host
        self.port = port
        
    def name(self):
        return self.topic
    
    def run(self):
        try:
            # Existe a hipótese de não conseguir resolver. Falha no acesso ao serviço DNS por exemplo?
            self.ipv4, self.ipv6 = resolveIP(self.host)
            
            if self.ipv6:
                clientsocket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                clientsocket.connect((self.ipv6, self.port))
                clientsocket.close()
                return True
            elif self.ipv4:
                clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                clientsocket.connect((self.ipv4, self.port))
                clientsocket.close()
                return True
            else:
                return False
        except Exception as e:
            print(f"ERRO (TCP <{self.host}:{self.port}>) =>",e)
            return False
        
class ConsultaICMP(Consulta):
    def __init__(self, topic:str, host:str, tentativas:int=2, timeout_sec:int=3):
        self.topic = topic
        self.host = host
        self.timeout_sec = timeout_sec
        self.tentativas = tentativas
    def name(self):
        return self.topic
    
    def run(self):
        try:
            # Existe a hipótese de não conseguir resolver. Falha no acesso ao serviço DNS por exemplo?
            self.ipv4, self.ipv6 = resolveIP(self.host)
            
            if self.ipv6:
                if 'win' in sys.platform:
                    # processo = subprocess.Popen(['ping', self.ipv6], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    # saida, erro = processo.communicate()
                    # print(saida, erro)
                    pass
                else: # UNIX: Linux/Mac
                    processo = subprocess.run(['ping', '-c', str(self.tentativas), '-W', str(self.timeout_sec), self.ipv6], capture_output=True)
                    # print('RETORNO',processo.returncode)
                    # print('STDOUT>\n',processo.stdout.decode(),'\n=====================')
                    # print('STDERR>\n',processo.stderr.decode(),'\n=====================')
                return processo.returncode == 0
            elif self.ipv4:
                if 'win' in sys.platform:
                    # processo = subprocess.Popen(['ping', self.ipv4], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    # saida, erro = processo.communicate()
                    # print(saida, erro)
                    pass
                else: # UNIX: Linux/Mac
                    processo = subprocess.run(['ping', '-c', str(self.tentativas), '-W', str(self.timeout_sec), self.ipv4], capture_output=True)
                    # print('RETORNO',processo.returncode)
                    # print('STDOUT>\n',processo.stdout.decode(),'\n=====================')
                    # print('STDERR>\n',processo.stderr.decode(),'\n=====================')
                return processo.returncode == 0
            else:
                return False
        except Exception as e:
            print(f"ERRO (ICMP <{self.host}>) =>",e)
            return False
        
class ConsultaNetstat(Consulta):
    def __init__(self, topic:str, proto:str, port:int):
        self.topic = topic
        self.proto = proto
        self.port = port

    def name(self):
        return self.topic
    
    def run(self):
        try:
            if 'win' in sys.platform:
                return False
            else: # UNIX: Linux/Mac
                processo = subprocess.run(['netstat', '-tupln'], capture_output=True)
                # print('STDOUT>\n',processo.stdout.decode(),'\n=====================')
                linhas = processo.stdout.decode().split('\n')
                registros = []
                while len(linhas)>0:
                    linha = linhas.pop()
                    if 'tcp' in linha or 'udp' in linha:
                        parametros = linha.split(' ')
                        while parametros.count('') > 0:
                            parametros.remove('')
                        registros.append(parametros)
                for _valores in registros:
                    proto, ipport = _valores[0], _valores[3]
                    portInt = int(str(ipport).split(':')[-1])
                    if proto == self.proto and portInt == self.port:
                        return True
        except Exception as e:
            print(f"ERRO (NETSTAT <{self.proto} {self.port}>) =>",e)
            return False
        return False


def main(configs, configs_profile):
    global exit_event
    # print("CONFIGS",configs)
    # print("CONFIGS_PROFILE",configs_profile)
    # configs_profile["server_time"] de BIAS
    remote_offset_time = float(configs_profile["server_time"])-get_current_timestamp()
    
    apelido = configs['alias']
    with amqp.Connection(configs_profile['amqp']['host'], userid=configs['amqp']['userid'], password=configs['amqp']['password']) as c:
        canal = c.channel()
        consultas : List[Consulta] = []
        for servico in configs_profile['service']:
            topic = servico['topic']
            # TCP
            if ('http' in servico) and ('port' in servico):
                consultas.append(ConsultaTCP(topic, servico['http'], int(servico['port'])))
            # Ping
            elif ('ping' in servico):
                consultas.append(ConsultaICMP(topic, servico['ping']))
            # Netstat - service
            elif ('local' in servico) and (servico['local'] == 'service-port'):
                if 'tcp' in servico:
                    consultas.append(ConsultaNetstat(topic, 'tcp', int(servico['tcp'])))
                elif 'tcp6' in servico:
                    consultas.append(ConsultaNetstat(topic, 'tcp6', int(servico['tcp6'])))
                elif 'udp' in servico:
                    consultas.append(ConsultaNetstat(topic, 'udp', int(servico['udp'])))
                elif 'udp6' in servico:
                    consultas.append(ConsultaNetstat(topic, 'udp6', int(servico['udp6'])))
            else:
                continue
            nomeQueue = "/".join(["", apelido, consultas[-1].name()])
            nome, num_mensagens, consumidores = canal.queue_declare(queue=nomeQueue, durable=True, exclusive=False, auto_delete=False)
            print(f"Instanciada fila {nome} com {num_mensagens} mensagem(s) e {consumidores} consumidor(es)")
            # canal.queue_bind()
    
    
    
        while not exit_event.is_set():
            c.send_heartbeat()
            if canal is not None:
                for consulta in consultas:
                    nomeQueue = "/".join(["", apelido, consulta.name()])
                    resultado = 1 if consulta.run() else 0
                    # print(nomeQueue,'=>',"Sucesso" if resultado else "Falha")
                    canal.basic_publish(amqp.Message(
                        str(resultado),
                        application_headers={'return': resultado},
                        timestamp=int((remote_offset_time+get_current_timestamp())*1000),
                    ), routing_key=nomeQueue)
            print('.',end='', flush=True)
            for _ in range(5):
                time.sleep(1)
                if exit_event.is_set():
                    break

def host_connect(ip:str, port:int, configs):
    global exit_event
    while not exit_event.is_set():
        sockt_info = None
        try:
            sockinfov6 = socket.getaddrinfo(ip, port, socket.AF_INET6)
            # print(sockinfov6[0][-1])
            sockt_info = sockinfov6
        except Exception as ev6:
            try:
                sockinfov4 = socket.getaddrinfo(ip, port, socket.AF_INET)
                # print(sockinfov4[0][-1])
                sockt_info = sockinfov4
            except Exception as e:
                print("Incapaz de realizar conexão.")
                print(ev6)
                print(e)
                return
        if sockt_info:
            s = socket.socket(sockt_info[0][0], sockt_info[0][1])
            s.settimeout(2)
            print(sockt_info[0][-1])
            s.connect(sockt_info[0][-1])
            s.sendall(f"{configs['alias']}\n".encode('utf-8'))
            configs_str = ""
            try:
                while True:
                    byte = s.recv(1)
                    if byte == b'\0':
                        break
                    configs_str += byte.decode("utf-8")
                # print(configs_str)
                try:
                    profile_configs = yaml.safe_load(configs_str)
                    s.sendall(b"OK\n")
                except yaml.YAMLError as exc:
                    print(f"ERRO YAML:",exc)
                    s.sendall(b"ERR:YAML\n")
                s.close()
                while not exit_event.is_set():
                    try:
                        main(configs, profile_configs)
                    except amqp.ConnectionForced as e:
                        print("FIM DE CONEXÃO FORÇADO:",e.message)
                        if e.message == 'CONNECTION_FORCED - exit':
                            break
                        else:
                            print('Reiniciando.')
                    except Exception as e:
                        print("ERRO:",e)
                        
            except TimeoutError:
                print("[CLIENT] Timeout ocorrido.")


def thread_server_ipv6(_PORT:int):
    '''
    ## Thread Servidor IPv6
    '''
    global exit_event, server_profiles
    s = socket.socket(socket.AF_INET6)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("::1", _PORT))
    print(f"Iniciado servidor IPv6 na porta {_PORT}", flush=True)
    s.listen(5)
    s.settimeout(1)
    while True:
        if exit_event.is_set():
            s.close()
            break
        try:
            (clientsocket, address) = s.accept()
            print(f"{address} : Nova conexão")
            alias = ""
            lastChar = clientsocket.recv(1).decode('utf-8')
            while lastChar != '\n':
                alias += lastChar
                lastChar = clientsocket.recv(1).decode('utf-8')
            print(f"{address} : Autenticando ALIAS {alias}")
            if alias in server_profiles:
                if address[0] == server_profiles[alias]['client']['host']:
                    server_profiles[alias]['server_time'] = get_current_timestamp()
                    clientsocket.send(yaml.dump(server_profiles[alias]).encode())
                    clientsocket.send(b'\0')
                    status = ""
                    lastChar = clientsocket.recv(1).decode('utf-8')
                    while lastChar != '\n':
                        status += lastChar
                        lastChar = clientsocket.recv(1).decode('utf-8')
                    print(f"{address} : TERMINADO=>{status}", end='\n\n')
                else:
                    print(f"{address} ERRO : Tentativa de conexão do ALIAS {alias} de origem inesperada.")
                    s.close()
            else:
                s.close()
            
        except TimeoutError:
            pass
        except KeyboardInterrupt:
            return

def thread_server_ipv4(_PORT:int):
    '''
    ## Thread Servidor IPv4
    '''
    global exit_event, server_profiles
    s = socket.socket(socket.AF_INET)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", _PORT))
    print(f"Iniciado servidor IPv4 na porta {_PORT}", flush=True)
    s.listen(5)
    s.settimeout(1)
    while True:
        if exit_event.is_set():
            s.close()
            break
        try:
            (clientsocket, address) = s.accept()
            print(f"{address} : Nova conexão")
            alias = ""
            lastChar = clientsocket.recv(1).decode('utf-8')
            while lastChar != '\n':
                alias += lastChar
                lastChar = clientsocket.recv(1).decode('utf-8')
            print(f"{address} : Autenticando ALIAS {alias}")
            if alias in server_profiles:
                if address[0] == server_profiles[alias]['client']['host']:
                    server_profiles[alias]['server_time'] = get_current_timestamp()
                    clientsocket.send(yaml.dump(server_profiles[alias]).encode())
                    clientsocket.send(b'\0')
                    status = ""
                    lastChar = clientsocket.recv(1).decode('utf-8')
                    while lastChar != '\n':
                        status += lastChar
                        lastChar = clientsocket.recv(1).decode('utf-8')
                    print(f"{address} : TERMINADO=>{status}")
                else:
                    print(f"{address} ERRO : Tentativa de conexão do ALIAS {alias} de origem inesperada.")
                    s.close()
            else:
                s.close()
        except TimeoutError:
            pass
        except KeyboardInterrupt:
            return


def thread_server(configs):
    '''
    ## Thread consumidor AMQP/MQTT
    '''
    global exit_event, server_profiles
    events_listener = ClientsServerMonitor()
    print('Iniciando conexão com Broker...')
    try:
        filas_ativas = []
        
        # Ignorar esta busca.
        
        # r = requests.get('http://%s:%d/api/queues/%s' % (configs['amqp']['host'], 15672, ''), auth=(configs['amqp']['userid'], configs['amqp']['password']))
        # if r.status_code == 200:
        #     if r.headers['content-type'] == 'application/json':
        #         # print(r.text)
        #         queues = r.json()
        #     else:
        #         print(f"[Servidor][Erro][Broker][WEB]: Conexão mal sucedida. Tipo de conteúdo: {r.headers['content-type']}")
        #         return
        # else:
        #     print(f"[Servidor][Erro][Broker][WEB]: Conexão mal sucedida. Código de status: {r.status_code}")
        #     return
        
        # for fila in queues:
        #     filas_ativas.append(fila['name'])
        #     pendentes = fila['messages']
        #     if pendentes > 0:
        #         if 'idle_since' in fila:
        #             last_changes = datetime.fromisoformat(fila['idle_since']).astimezone(timezone(timedelta(hours=-3)))
        #             print(f"[{fila['name']}] {fila['messages']} mensagens em fila, desde {last_changes}")
        #         else:
        #             print(f"[{fila['name']}] {fila['messages']} mensagens em fila")
        
        # Usar somente a busca abaixo:
        
        # Preencher filas_ativas com as que REALMENTE conhecemos:
        for _alias in server_profiles.keys():
            for service in server_profiles[_alias]['service']:
                topic_add = "/".join(["", _alias, service['topic']])
                if filas_ativas.count(topic_add) == 0:
                    filas_ativas.append(topic_add)

        with amqp.Connection(configs['amqp']['host'], userid=configs['amqp']['userid'], password=configs['amqp']['password']) as c:
            canal = c.channel()
            
            def on_message(message:amqp.basic_message.Message):
                try:
                    ch = message.channel
                    key = message.delivery_info['routing_key']
                    [_, _alias, _topic] = key.split("/")
                    _return = message.properties['application_headers']['return']
                    _body = message.body
                    _timestamp = message.properties['timestamp']
                    _offset_stamp = int(get_current_timestamp()*1000) - _timestamp
                    print(f"[{_offset_stamp} ms] {key} => {_return}")
                    for service in server_profiles[_alias]['service']:
                        if _topic == service['topic']:
                            events_listener.addEvent(alias=_alias, topic=_topic, headers=message.properties['application_headers'], profile_service=service, timestamp=_timestamp)
                            break
                    ch.basic_ack(message.delivery_tag)
                except Exception as e:
                    pass
            
            for fila in filas_ativas:
                canal.queue_declare(queue=fila, durable=True, auto_delete=False)
                canal.basic_consume(queue=fila, callback=on_message)
            
            while not exit_event.is_set():
                try:
                    c.drain_events(timeout=2)
                except TimeoutError as e:
                    pass
    except amqp.exceptions.AMQPError as e:
        print(f"[Servidor][Erro][Broker][Conexão]: {e}\nFinalizando...")
        exit_event.set()
    except Exception as e:
        print(f"[Servidor][Erro][Broker][Conexão]: {e}\nFinalizando...")
        exit_event.set()


if __name__ == "__main__":
    
    if args.server:
        with open('env.ser.yaml', 'r') as file:
            try:
                configs = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                print(exc)
                exit(0)
        print("[Servidor] Iniciando...")
        signal.signal(signal.SIGINT, signal_handler)
        
        amqp_server_host = configs['amqp']['host']
        amqp_server = ConsultaTCP('',amqp_server_host, 5672)
        amqp_server_ping = ConsultaICMP('',amqp_server_host, tentativas=1)
        while not exit_event.is_set():
            if not amqp_server.run():
                print(f"[Servidor][ERRO] Broker não está acessível no host {amqp_server_host}.")
                if amqp_server_ping.run():
                    print("[Servidor][INFO] O host parece estar acessível. Verifique o estado do serviço.")
                else:
                    print("[Servidor][ERRO] O host parece estar inacessível. Verifique o estado da máquina.")
                print("[Servidor] Tentando novamente em 5 segundos.")
                time.sleep(5)
            else:
                print("[Servidor] Serviço no Broker está ativo.")
                break
        if exit_event.is_set():
            exit(0)
        
        for subdir, dirs, files in os.walk('profiles/'):
            for arquivo in files:
                if '.yaml' == arquivo.lower()[-5:]:
                    alias = arquivo[:-5]
                    with open(f'{subdir}{arquivo}', 'r') as file:
                        try:
                            server_profiles[alias] = yaml.safe_load(file)
                            # Parâmetros de ambiente do servidor adicionais
                            server_profiles[alias]['amqp'] = configs['amqp']
                            
                            print(f"- Carregado ALIAS {alias} [IP {server_profiles[alias]['client']['host']}]")
                        except yaml.YAMLError as exc:
                            print(f"ERRO EM PROFILE {arquivo}:")
                            print(exc)
        tipv6 = Thread(target=thread_server_ipv6, args=[int(configs['server']['port'])])
        tipv4 = Thread(target=thread_server_ipv4, args=[int(configs['server']['port'])])
        tconsum = Thread(target=thread_server, args=[configs])
        tipv6.start()
        tipv4.start()
        tconsum.start()
        
    else:
        with open('env.yaml', 'r') as file:
            try:
                configs = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                print(exc)
                exit(0)
        signal.signal(signal.SIGINT, signal_handler)
        while not exit_event.is_set():
            try:
                host_connect(configs['server']['host'], int(configs['server']['port']), configs=configs)
            except ConnectionRefusedError as e:
                print("ERRO: Servidor offline.")
                time.sleep(5)
    