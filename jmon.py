# pip install pyyaml
import yaml
import socket
from typing import Any, ClassVar, Literal, SupportsIndex, TypeVar, List


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
            print(f"ERRO (TCP {self.host}:{self.port}) =>",e)
            return False


def main(configs:any):
    servidor = configs['server']
    consultas : List[Consulta] = []
    for servico in configs['service']:
        if ('http' in servico) and ('port' in servico):
            consultas.append(ConsultaTCP(servico['http'], int(servico['port'])))
    
    for consulta in consultas:
        nome = [servidor['host']]
        nome.extend(consulta.name())
        nome = "|".join(nome)
        print(nome,'=>',"Sucesso" if consulta.run() else "Falha")


if __name__ == "__main__":
    with open('env.yaml', 'r') as file:
        try:
            main(yaml.safe_load(file))
        except yaml.YAMLError as exc:
            print(exc)