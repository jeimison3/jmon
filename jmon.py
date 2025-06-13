# pip install pyyaml
import yaml
import socket
from typing import List

import subprocess
import sys

import amqp
import time


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

class Consulta:
    ''' Estrutura básica de uma Consulta. '''
    
    def __init__(self):
        pass
    
    def name(self) -> list[str]:
        pass
    
    def run(self) -> bool:
        ''' Procedimento que verifica se houve sucesso ou falha '''
        pass

class ConsultaTCP(Consulta):
    def __init__(self, host:str, port:int):
        self.host = host
        self.port = port
        
    def name(self):
        return ["TCP",self.host,str(self.port)]
    
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
                clientsocket.connect((self.ipv6, self.port))
                clientsocket.close()
                return True
            else:
                return False
        except Exception as e:
            print(f"ERRO (TCP <{self.host}:{self.port}>) =>",e)
            return False
        
class ConsultaICMP(Consulta):
    def __init__(self, host:str, tentativas:int=2, timeout_sec:int=3):
        self.host = host
        self.timeout_sec = timeout_sec
        self.tentativas = tentativas
    def name(self):
        return ["ICMP",self.host]
    
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
    def __init__(self, proto:str, port:int):
        self.proto = proto
        self.port = port
    def name(self):
        return ["NETSTAT",self.proto,str(self.port)]
    
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


def main(configs:any):
    servidor = configs['server']
    
    apelido = configs['alias']
    with amqp.Connection(servidor['host'], userid=servidor['userid'], password=servidor['password']) as c:
        canal = c.channel()
        consultas : List[Consulta] = []
        for servico in configs['service']:
            # TCP
            if ('http' in servico) and ('port' in servico):
                consultas.append(ConsultaTCP(servico['http'], int(servico['port'])))
            # Ping
            elif ('ping' in servico):
                consultas.append(ConsultaICMP(servico['ping']))
            # Netstat
            elif ('local' in servico) and ('tcp' in servico):
                consultas.append(ConsultaNetstat('tcp', int(servico['tcp'])))
            elif ('local' in servico) and ('tcp6' in servico):
                consultas.append(ConsultaNetstat('tcp6', int(servico['tcp6'])))
            elif ('local' in servico) and ('udp' in servico):
                consultas.append(ConsultaNetstat('udp', int(servico['udp'])))
            elif ('local' in servico) and ('udp6' in servico):
                consultas.append(ConsultaNetstat('udp6', int(servico['udp6'])))
            else:
                continue
            nomeQueue = f"/{apelido}/{'/'.join(consultas[-1].name())}"
            nome, num_mensagens, consumidores = canal.queue_declare(queue=nomeQueue, durable=True, exclusive=False, auto_delete=False)
            print(f"Instanciada fila {nome} com {num_mensagens} mensagem(s) e {consumidores} consumidor(es)")
            # canal.queue_bind()
    
    
    
        while True:
            c.send_heartbeat()
            if canal is not None:
                while not canal.is_open:
                    canal.open()
                    time.sleep(0.5)
                for consulta in consultas:
                    nomeQueue = f"/{apelido}/{'/'.join(consulta.name())}"
                    resultado = 1 if consulta.run() else 0
                    print(nomeQueue,'=>',"Sucesso" if resultado else "Falha")
                    canal.basic_publish(amqp.Message(str(resultado), content_type='text/plain', application_headers={'status': resultado}), routing_key=nomeQueue)#, routing_key=apelido)
            time.sleep(5)


if __name__ == "__main__":
    with open('env.yaml', 'r') as file:
        try:
            configs = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)
            exit(0)
            
        while True:
            try:
                main(configs)
            except amqp.ConnectionForced as e:
                print("FIM DE CONEXÃO FORÇADO:",e.message)
                if e.message == 'CONNECTION_FORCED - exit':
                    break
                else:
                    print('Reiniciando.')
            except Exception as e:
                print("ERRO:",e)
    