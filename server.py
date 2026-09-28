"""
Servidor TCP multicliente con un pequeno protocolo de comandos.
Practica de Sistemas Distribuidos: comunicacion mediante sockets (T2).

Este servidor parte del ejemplo visto en clase (socket + bind + listen +
accept + recv/send) y lo amplia en tres puntos, precisamente los tres
limites que la diapositiva senala en el servidor basico:

  1. Atiende a varios clientes a la vez: un hilo por conexion, en lugar
     de bloquearse en un unico accept() tras el primer cliente.
  2. Trabaja con mensajes completos y no con bytes sueltos: como TCP
     entrega un flujo de bytes sin fronteras propias, el servidor arma
     cada mensaje acumulando en un buffer hasta encontrar un salto de
     linea, que actua como delimitador del protocolo de aplicacion.
  3. Incorpora un comando que envia un correo electronico real, para
     mostrar como un servicio construido sobre sockets puede apoyarse en
     un sistema de mensajeria externo (un MOM, en la terminologia del
     tema 2) para completar una peticion del cliente.

Sobre el mecanismo de envio de correo: la primera version de esta
practica usaba SMTP directo (conexion de socket al puerto 587/465 de un
servidor de correo). Al desplegar en Railway se comprobo empiricamente
que la plataforma bloquea el trafico saliente hacia esos puertos (la
conexion agota el tiempo de espera sin respuesta), una restriccion
habitual en plataformas de hosting gratuitas para evitar que sus
contenedores se usen para enviar spam. La solucion adoptada es enviar el
correo a traves de la API HTTP de Resend (https://resend.com): en lugar
de que el servidor hable el protocolo SMTP directamente, hace una
peticion HTTPS (puerto 443, sin restriccion en Railway) a un servicio
externo que es quien finalmente entrega el correo por SMTP. Sigue siendo
el mismo concepto (delegar en un sistema de mensajeria externo), con un
protocolo de transporte distinto hacia ese sistema.

HOST y PORT son configurables por variable de entorno para poder
desplegar el mismo codigo sin tocarlo en distintas plataformas (Railway,
Fly.io, tu propio equipo...), que asignan el puerto interno de formas
distintas.
"""

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import threading
import datetime
import json
import os
import urllib.request
import urllib.error

HOST = os.environ.get("SERVER_HOST", "0.0.0.0")   # escucha en todas las interfaces
PORT = int(os.environ.get("SERVER_PORT", os.environ.get("PORT", "5050")))

# --- Configuracion del servicio de correo (API HTTP de Resend) ----------
# La clave de API nunca se escribe en el codigo fuente: se lee de una
# variable de entorno (en el hosting, se configura como "secret" o
# "variable" desde el panel, nunca en el repositorio). Si no esta
# definida, el servidor entra en MODO_PRUEBA y simula el envio en lugar
# de hacer una peticion real.
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
# Direccion remitente. "onboarding@resend.dev" es la direccion de prueba
# que ofrece Resend sin necesidad de verificar un dominio propio; en modo
# sandbox (sin dominio verificado) solo se puede enviar correo a la
# direccion con la que se creo la cuenta de Resend.
RESEND_FROM = os.environ.get("RESEND_FROM", "onboarding@resend.dev")
MODO_PRUEBA = RESEND_API_KEY is None


def enviar_correo(destinatario, asunto, cuerpo):
    """
    Envia un correo mediante una peticion HTTPS POST a la API de Resend
    (https://api.resend.com/emails), autenticada con la cabecera
    "Authorization: Bearer <clave>". El cuerpo de la peticion va en JSON,
    tal como exige esa API.

    En MODO_PRUEBA no se abre ninguna conexion de red: se registra por
    consola lo que se habria enviado, para poder probar el protocolo
    completo (el comando CORREO y su respuesta) sin credenciales reales.
    """
    if MODO_PRUEBA:
        print(f"[MODO_PRUEBA] Simulando envio -> Para: {destinatario} "
              f"| Asunto: {asunto} | Cuerpo: {cuerpo}")
        return True, "simulado (MODO_PRUEBA activo, sin RESEND_API_KEY)"

    cuerpo_peticion = json.dumps({
        "from": RESEND_FROM,
        "to": [destinatario],
        "subject": asunto,
        "text": cuerpo,
    }).encode("utf-8")

    peticion = urllib.request.Request(
        "https://api.resend.com/emails",
        data=cuerpo_peticion,
        method="POST",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
            # Cloudflare (que protege la API de Resend) bloquea con un 403
            # (error code: 1010) las peticiones que usan el User-Agent por
            # defecto de urllib ("Python-urllib/x.y"), por ser una firma
            # facilmente identificable como trafico de script. Un
            # User-Agent propio evita ese bloqueo.
            "User-Agent": "practica-sistemas-distribuidos-sockets/1.0",
        },
    )

    try:
        with urllib.request.urlopen(peticion, timeout=10) as respuesta:
            datos_respuesta = json.loads(respuesta.read().decode("utf-8"))
            return True, f"correo enviado (id Resend: {datos_respuesta.get('id', '?')})"
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", errors="replace")
        return False, f"error HTTP {error.code} de Resend: {detalle}"
    except urllib.error.URLError as error:
        return False, f"error de red: {error.reason}"


class Servidor:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    def iniciar(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        print(f"Servidor escuchando en {self.host}:{self.port} "
              f"(MODO_PRUEBA={'activo' if MODO_PRUEBA else 'inactivo'})")
        try:
            while True:
                conn, addr = self.sock.accept()
                hilo = threading.Thread(
                    target=self.atender_cliente, args=(conn, addr), daemon=True
                )
                hilo.start()
        except KeyboardInterrupt:
            print("\nCerrando servidor...")
        finally:
            self.sock.close()

    def atender_cliente(self, conn, addr):
        print(f"[+] Conexion aceptada de {addr}")
        buffer = ""
        try:
            with conn:
                conn.sendall(
                    b"BIENVENIDO. Comandos: HOLA | HORA | ECO <msg> | "
                    b"CORREO <destino>|<asunto>|<cuerpo> | SALIR\n"
                )
                while True:
                    datos = conn.recv(1024)
                    if not datos:
                        # recv vacio: el cliente cerro la conexion
                        break
                    buffer += datos.decode("utf-8", errors="replace")
                    # Un mensaje termina en salto de linea: puede llegar
                    # partido en varios recv, o varios mensajes en un recv.
                    while "\n" in buffer:
                        linea, buffer = buffer.split("\n", 1)
                        if not self.procesar_linea(conn, linea.strip(), addr):
                            return
        except ConnectionResetError:
            print(f"[!] {addr} cerro la conexion de forma abrupta")
        finally:
            print(f"[-] Conexion cerrada con {addr}")

    def procesar_linea(self, conn, linea, addr):
        """Interpreta un comando y responde. Devuelve False si hay que cerrar."""
        if not linea:
            return True

        partes = linea.split(" ", 1)
        comando = partes[0].upper()
        resto = partes[1] if len(partes) > 1 else ""

        if comando == "HOLA":
            conn.sendall(b"HOLA, cliente\n")

        elif comando == "HORA":
            ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.sendall(f"{ahora}\n".encode("utf-8"))

        elif comando == "ECO":
            conn.sendall(f"{resto}\n".encode("utf-8"))

        elif comando == "CORREO":
            try:
                destinatario, asunto, cuerpo = resto.split("|", 2)
            except ValueError:
                conn.sendall(b"ERROR formato: CORREO <destino>|<asunto>|<cuerpo>\n")
                return True
            ok, detalle = enviar_correo(destinatario.strip(), asunto.strip(), cuerpo.strip())
            estado = "OK" if ok else "ERROR"
            conn.sendall(f"{estado} {detalle}\n".encode("utf-8"))

        elif comando == "SALIR":
            conn.sendall(b"ADIOS\n")
            return False

        else:
            conn.sendall(b"ERROR comando no reconocido\n")

        return True


if __name__ == "__main__":
    Servidor().iniciar()
