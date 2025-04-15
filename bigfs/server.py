import socket
import json
import os
import shutil
import threading
from datetime import datetime

HOST = 'localhost'
PORT = 12345
STORAGE_DIR = 'storage'

# Garante que o diretório de armazenamento exista
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

def log_acao(acao, path, extra=None, resultado=""):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    extra_info = f", Extra: {extra}" if extra else ""
    print(f"[{agora}] Ação: {acao}, Caminho: {path}{extra_info} => {resultado}")


def handle_client(conn, addr):
    print(f"[+] Cliente conectado: {addr}")
    try:
        data = conn.recv(4096).decode('utf-8')
        if not data:
            return
        request = json.loads(data)
        action = request.get('action')
        path = request.get('path')
        extra = request.get('extra')  # usado em cp (origem/destino)

        if action == 'ls':
            response = listar(path)
        elif action == 'rm':
            response = remover(path)
        elif action == 'cp':
            response = copiar(path, extra)
        elif action == 'get':
            response = baixar(path)
        else:
            response = {'status': 'error', 'message': 'Ação inválida'}
    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
    
    log_acao(action, path, extra, response.get('status'))
    conn.sendall(json.dumps(response).encode('utf-8'))
    conn.close()

def caminho_absoluto(rel_path):
    return os.path.abspath(os.path.join(STORAGE_DIR, rel_path))

def listar(path):
    abs_path = caminho_absoluto(path or '')
    print(f"[DEBUG] Listando: {abs_path}")
    if os.path.exists(abs_path):
        if os.path.isdir(abs_path):
            items = os.listdir(abs_path)
            return {'status': 'success', 'type': 'dir', 'content': items}
        else:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {'status': 'success', 'type': 'file', 'content': content}
    else:
        return {'status': 'error', 'message': 'Arquivo ou diretório não encontrado'}

def remover(path):
    abs_path = caminho_absoluto(path)
    if os.path.exists(abs_path):
        try:
            if os.path.isfile(abs_path):
                os.remove(abs_path)
            else:
                shutil.rmtree(abs_path)
            return {'status': 'success', 'message': f'{path} removido com sucesso'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    else:
        return {'status': 'error', 'message': 'Arquivo ou diretório não encontrado'}

def copiar(origem, destino):
    src = caminho_absoluto(origem)
    dst = caminho_absoluto(destino)
    if not os.path.exists(src):
        return {'status': 'error', 'message': 'Origem não encontrada'}
    try:
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        else:
            if os.path.exists(dst):
                dst = os.path.join(dst, os.path.basename(src))
            shutil.copytree(src, dst)
        return {'status': 'success', 'message': 'Cópia realizada com sucesso'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def baixar(path):
    abs_path = caminho_absoluto(path)
    if os.path.isfile(abs_path):
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {'status': 'success', 'file': os.path.basename(abs_path), 'content': content}
    elif os.path.isdir(abs_path):
        arquivos = {}
        for root, dirs, files in os.walk(abs_path):
            for name in files:
                filepath = os.path.join(root, name)
                rel_path = os.path.relpath(filepath, STORAGE_DIR)
                with open(filepath, 'r', encoding='utf-8') as f:
                    arquivos[rel_path] = f.read()
        return {'status': 'success', 'files': arquivos}
    else:
        return {'status': 'error', 'message': 'Arquivo ou diretório não encontrado'}

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[SERVER] Servidor rodando em {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    start_server()
