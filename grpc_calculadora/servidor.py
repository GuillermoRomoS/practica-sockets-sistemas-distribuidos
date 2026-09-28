"""
Servidor gRPC de la calculadora remota.

Caracteristica anadida a la practica de sockets: implementa el mismo tipo
de comunicacion cliente-servidor, pero usando gRPC en lugar de sockets
TCP en crudo, para poder comparar ambos mecanismos de invocacion remota
tal como se explican en el Tema 2 (Comunicacion) de la asignatura.

El contrato del servicio esta declarado primero, en calculadora.proto (el
IDL), y de el se generan los stubs (calculadora_pb2.py y
calculadora_pb2_grpc.py) con protoc. Este servidor implementa esos stubs;
no construye ni interpreta mensajes a mano como en server.py.

Expone dos modos de llamada gRPC distintos:
  - Unario: Sumar, Restar, Multiplicar, Dividir. Una peticion, una
    respuesta, igual que una llamada a funcion local (transparencia de
    la llamada).
  - Streaming de servidor: ObtenerHistorico. Una peticion, y el servidor
    responde con una secuencia de mensajes (el historial de operaciones
    realizadas), en lugar de una unica respuesta.

El historial se guarda en memoria: se reinicia cada vez que el proceso
del servidor se reinicia (por ejemplo, en cada despliegue en Railway).
No hay persistencia en disco ni en base de datos; se indica de forma
explicita para no dar por sentada una garantia que el servidor no ofrece,
igual que se hizo con el modo de prueba del envio de correo en la otra
practica.

Uso local:
    python servidor.py
    (escucha en 0.0.0.0:50051 salvo que la variable de entorno PORT
    indique otro puerto, que es como Railway asigna el puerto en
    produccion)
"""

import os
import threading
from concurrent import futures
from datetime import datetime, timezone

import grpc

import calculadora_pb2
import calculadora_pb2_grpc


class ServicioCalculadora(calculadora_pb2_grpc.CalculadoraServicer):
    def __init__(self):
        # Historial compartido entre todas las llamadas atendidas por este
        # proceso. grpc.server despacha cada RPC en un hilo de su propio
        # pool (ver ThreadPoolExecutor en servir()), asi que el acceso a
        # esta lista debe protegerse igual que cualquier recurso
        # compartido entre hilos concurrentes.
        self._historial = []
        self._bloqueo = threading.Lock()

    def _registrar(self, operacion, a, b, resultado):
        registro = calculadora_pb2.RegistroHistorico(
            operacion=operacion,
            a=a,
            b=b,
            resultado=resultado,
            marca_temporal=datetime.now(timezone.utc).isoformat(),
        )
        with self._bloqueo:
            self._historial.append(registro)

    def Sumar(self, request, context):
        resultado = request.a + request.b
        self._registrar("suma", request.a, request.b, resultado)
        return calculadora_pb2.OperacionResponse(resultado=resultado)

    def Restar(self, request, context):
        resultado = request.a - request.b
        self._registrar("resta", request.a, request.b, resultado)
        return calculadora_pb2.OperacionResponse(resultado=resultado)

    def Multiplicar(self, request, context):
        resultado = request.a * request.b
        self._registrar("multiplicacion", request.a, request.b, resultado)
        return calculadora_pb2.OperacionResponse(resultado=resultado)

    def Dividir(self, request, context):
        if request.b == 0:
            # Un error de aplicacion (division entre cero) se comunica con
            # un codigo de estado gRPC, no con una excepcion Python que
            # cruzaria la red sin significado para el cliente ni con un
            # campo de error dentro de OperacionResponse. El cliente lo
            # recibe como grpc.RpcError con codigo INVALID_ARGUMENT, de
            # forma analoga a como HTTP usa un codigo 4xx para senalar un
            # error del solicitante en lugar de un fallo del servidor.
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "No se puede dividir entre cero",
            )
        resultado = request.a / request.b
        self._registrar("division", request.a, request.b, resultado)
        return calculadora_pb2.OperacionResponse(resultado=resultado)

    def ObtenerHistorico(self, request, context):
        # Se copia la lista bajo el lock para no iterarla mientras otro
        # hilo la modifica en paralelo, y despues se entrega un mensaje
        # por llamada a yield: esto es lo que distingue el streaming de
        # servidor de devolver una unica respuesta con una lista dentro,
        # y permite al cliente empezar a consumir resultados antes de que
        # el servidor haya terminado de enviarlos todos.
        with self._bloqueo:
            copia = list(self._historial)
        for registro in copia:
            yield registro


def servir():
    puerto = os.environ.get("PORT", "50051")
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    calculadora_pb2_grpc.add_CalculadoraServicer_to_server(
        ServicioCalculadora(), servidor
    )
    servidor.add_insecure_port(f"[::]:{puerto}")
    servidor.start()
    print(f"Servidor gRPC de la calculadora escuchando en el puerto {puerto}")
    servidor.wait_for_termination()


if __name__ == "__main__":
    servir()
