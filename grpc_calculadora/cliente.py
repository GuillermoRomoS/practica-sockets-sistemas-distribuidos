"""
Cliente gRPC de la calculadora remota.

Uso:
    python cliente.py [host] [puerto]

Por defecto se conecta a localhost:50051. Para hablar con el servidor
desplegado en Railway se le pasa el host y el puerto publico que Railway
asigne a este servicio, igual que client.py recibe el host y puerto del
TCP Proxy en la practica de sockets. La diferencia es que aqui el
"protocolo" (como se delimitan y representan los mensajes) no lo decide
este cliente: lo fija calculadora.proto, y tanto el stub del cliente
como el servidor se generan a partir de el, asi que no pueden
desincronizarse mientras usen el mismo contrato.
"""

import sys

import grpc

import calculadora_pb2
import calculadora_pb2_grpc


def imprimir_menu():
    print("\nComandos: SUMA a b | RESTA a b | MULT a b | DIV a b | HIST | SALIR")


def ejecutar_operacion(stub, comando, a, b):
    peticion = calculadora_pb2.OperacionRequest(a=a, b=b)
    llamadas = {
        "SUMA": stub.Sumar,
        "RESTA": stub.Restar,
        "MULT": stub.Multiplicar,
        "DIV": stub.Dividir,
    }
    try:
        respuesta = llamadas[comando](peticion)
        print(f"OK resultado = {respuesta.resultado}")
    except grpc.RpcError as error:
        # Un RpcError trae un codigo de estado gRPC (por ejemplo
        # INVALID_ARGUMENT o UNAVAILABLE si el servidor no responde) y un
        # mensaje de detalle, ambos fijados por el servidor o por la
        # propia libreria gRPC segun el fallo.
        print(f"ERROR {error.code()}: {error.details()}")


def mostrar_historico(stub):
    try:
        registros = list(stub.ObtenerHistorico(calculadora_pb2.HistoricoRequest()))
    except grpc.RpcError as error:
        print(f"ERROR {error.code()}: {error.details()}")
        return

    if not registros:
        print("(el historial esta vacio: aun no se ha pedido ninguna operacion)")
        return

    for registro in registros:
        print(
            f"  [{registro.marca_temporal}] {registro.operacion}"
            f"({registro.a}, {registro.b}) = {registro.resultado}"
        )


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    puerto = sys.argv[2] if len(sys.argv) > 2 else "50051"
    direccion = f"{host}:{puerto}"

    # Un canal gRPC no es una conexion TCP nueva por cada llamada: se abre
    # una vez, se reutiliza para todas las llamadas del programa y por
    # debajo mantiene una conexion HTTP/2 (con sus llamadas multiplexadas
    # sobre ella), a diferencia del socket TCP en crudo de la otra
    # practica, donde la conexion se gestiona a mano.
    with grpc.insecure_channel(direccion) as canal:
        stub = calculadora_pb2_grpc.CalculadoraStub(canal)
        print(f"Conectado a {direccion}")
        imprimir_menu()

        while True:
            try:
                entrada = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not entrada:
                continue

            partes = entrada.split()
            comando = partes[0].upper()

            if comando == "SALIR":
                break

            if comando == "HIST":
                mostrar_historico(stub)
                continue

            if comando in ("SUMA", "RESTA", "MULT", "DIV") and len(partes) == 3:
                try:
                    a, b = float(partes[1]), float(partes[2])
                except ValueError:
                    print("ERROR: a y b deben ser numeros")
                    continue
                ejecutar_operacion(stub, comando, a, b)
                continue

            print("Comando no reconocido.")
            imprimir_menu()


if __name__ == "__main__":
    main()
