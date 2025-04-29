import argparse
import socket
from threading import Thread, Event
import signal

exit_event = Event()

parser = argparse.ArgumentParser()
parser.add_argument("-s","--server", help="Inicia como servidor", action="store_true")
parser.add_argument("-p","--port", help="Porta utilizada pela aplicação", type=int, default=9998)
parser.add_argument("-c","--connect", help="IP do host", default="localhost")
args = parser.parse_args()


def thread_ipv6(_PORT:int):
    '''
    ## Thread Servidor IPv6
    '''
    global exit_event
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
            print(f"Conexão {address}: ->")
            mensagem = [b'']
            msg_sz = 0
            while b'\n' not in mensagem[-1] and msg_sz < 10_000:
                mensagem.append(clientsocket.recv(2000))
                msg_sz += len(mensagem[-1])
            print(f"=> {(b''.join(mensagem)).decode("utf-8")}")
            clientsocket.send(b''.join(mensagem))
            # clientsocket.close()
        except TimeoutError:
            pass
        except KeyboardInterrupt:
            return

def thread_ipv4(_PORT:int):
    '''
    ## Thread Servidor IPv4
    '''
    global exit_event
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
            print(f"Conexão {address}: ->")
            mensagem = [b'']
            msg_sz = 0
            while b'\n' not in mensagem[-1] and msg_sz < 10_000:
                mensagem.append(clientsocket.recv(2000))
                msg_sz += len(mensagem[-1])
            print(f"=> {(b''.join(mensagem)).decode("utf-8")}")
            clientsocket.send(b''.join(mensagem))
            # clientsocket.close()
        except TimeoutError:
            pass
        except KeyboardInterrupt:
            return


def signal_handler(signum, frame):
    print("Terminando...")
    global exit_event
    exit_event.set()
    
    
def host_connect(ip:str, port:int):
    s = None
    sockt_info = None
    try:
        sockinfov6 = socket.getaddrinfo(ip, port, socket.AF_INET6)
        print(sockinfov6[0][-1])
        sockt_info = sockinfov6
    except Exception as ev6:
        try:
            sockinfov4 = socket.getaddrinfo(ip, port, socket.AF_INET)
            print(sockinfov4[0][-1])
            sockt_info = sockinfov4
        except Exception as e:
            print("Incapaz de realizar conexão.")
            print(e)
            return
    if sockt_info:
        s = socket.socket(sockt_info[0][0], sockt_info[0][1])
        s.settimeout(2)
        s.connect(sockt_info[0][-1])
        s.send(b"Oi\n")
        chunks = []
        bytes_recd = 0
        terminated = False
        try:
            while bytes_recd < 256 and not terminated:
                chunk = s.recv(1)
                if chunk == b'':
                    terminated = True
                    raise RuntimeError("socket connection broken")
                elif chunk == b'\n':
                    terminated = True
                chunks.append(chunk)
                bytes_recd = bytes_recd + len(chunk)
            print(b''.join(chunks))
            s.close()
        except TimeoutError:
            print("Timeout ocorrido.")
    return
    ipnum = socket.gethostbyname(ip)
    s:socket.socket
    # if ip.count(':') > 0:
    #     s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    # elif ip.count('.') == 4:
    # s.connect(("www.python.org", 80))
    pass

if __name__ == "__main__":
    if args.server:
        print("Iniciando servidor...")
        signal.signal(signal.SIGINT, signal_handler)
        tipv6 = Thread(target=thread_ipv6, args=[args.port])
        tipv4 = Thread(target=thread_ipv4, args=[args.port])
        tipv6.start()
        tipv4.start()
    else:
        host_connect(args.connect,args.port)
        
        