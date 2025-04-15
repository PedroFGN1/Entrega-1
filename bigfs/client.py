import socket
import json

HOST = 'localhost'
PORT = 12345

def enviar_comando(acao, caminho, extra=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        request = {'action': acao, 'path': caminho}
        if extra:
            request['extra'] = extra
        s.sendall(json.dumps(request).encode('utf-8'))
        resposta = s.recv(8192)
        return json.loads(resposta.decode('utf-8'))

if __name__ == "__main__":
    while True:
        print("\nComandos disponíveis:")
        print("1. ls <caminho>")
        print("2. rm <caminho>")
        print("3. cp <origem> <destino>")
        print("4. get <caminho>")
        print("5. sair")

        entrada = input("Digite o comando: ").strip()
        if entrada == '5' or entrada.lower() == 'sair':
            break

        partes = entrada.split()
        if not partes:
            continue

        comando = partes[0]
        if comando == 'ls' and len(partes) >= 1:
            caminho = partes[1] if len(partes) > 1 else ''
            resposta = enviar_comando('ls', caminho)
        elif comando == 'rm' and len(partes) == 2:
            resposta = enviar_comando('rm', partes[1])
        elif comando == 'cp' and len(partes) == 3:
            resposta = enviar_comando('cp', partes[1], extra=partes[2])
        elif comando == 'get' and len(partes) == 2:
            resposta = enviar_comando('get', partes[1])
        else:
            print("Comando inválido")
            continue

        print("Resposta do servidor:", json.dumps(resposta, indent=2, ensure_ascii=False))