"""
Cliente interactivo para el servidor de sockets con envio de correo.
Practica de Sistemas Distribuidos: comunicacion mediante sockets (T2).

Uso:
    python client.py                       -> conecta a 127.0.0.1:5050
    python client.py mi-servidor.up.railway.app 12345   -> conecta al host y
                                               puerto publicos del despliegue
"""

import sys
from socket import socket, AF_INET, SOCK_STREAM

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5050


def main():
    with socket(AF_INET, SOCK_STREAM) as s:
        print(f"Conectando a {HOST}:{PORT}...")
        s.connect((HOST, PORT))
        bienvenida = s.recv(1024).decode("utf-8")
        print(bienvenida, end="")

        while True:
            linea = input("> ").strip()
            if not linea:
                continue
            s.sendall((linea + "\n").encode("utf-8"))
            respuesta = s.recv(1024).decode("utf-8")
            print(respuesta, end="")
            if linea.upper() == "SALIR":
                break


if __name__ == "__main__":
    main()
