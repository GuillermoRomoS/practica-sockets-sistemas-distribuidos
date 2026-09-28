"""
Prueba automatica del servidor: lanza dos clientes en paralelo (dos hilos)
que hablan con el servidor al mismo tiempo, para comprobar que atiende a
varias conexiones simultaneas y que cada una mantiene su propia
conversacion sin mezclarse con la otra.

Requiere que server.py este en ejecucion en 127.0.0.1:5050 antes de
lanzar este script.

Uso:
    Terminal 1> python server.py
    Terminal 2> python prueba_multicliente.py
"""

import socket
import threading
import time

HOST, PORT = "127.0.0.1", 5050


def run(nombre, comandos):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"[{nombre}] << {s.recv(1024).decode().strip()}")
        for c in comandos:
            s.sendall((c + "\n").encode())
            resp = s.recv(1024).decode().strip()
            print(f"[{nombre}] > {c}")
            print(f"[{nombre}] << {resp}")
            time.sleep(0.1)


if __name__ == "__main__":
    cliente1 = threading.Thread(target=run, args=("cliente1", [
        "HOLA",
        "HORA",
        "ECO hola mundo",
        "CORREO profesor@example.com|Entrega practica|Adjunto el servidor de sockets",
        "COMANDO_INVALIDO",
        "CORREO formato_incorrecto_sin_separadores",
        "SALIR",
    ]))
    cliente2 = threading.Thread(target=run, args=("cliente2", [
        "HOLA",
        "ECO soy el segundo cliente, en paralelo",
        "SALIR",
    ]))
    cliente1.start()
    cliente2.start()
    cliente1.join()
    cliente2.join()
