# Servidor de sockets multicliente con envio de correo (Sistemas Distribuidos)

Practica de la asignatura de Sistemas Distribuidos (Tema 2: Comunicacion). Implementa un servidor TCP multicliente en Python, con un pequeno protocolo de aplicacion propio, y un comando que delega el envio de un correo electronico real en un sistema de mensajeria externo (un MOM, en la terminologia de la asignatura).

El servidor esta desplegado publicamente en Railway y es accesible por cualquier cliente TCP.

Como caracteristica anadida, el repositorio incluye tambien una calculadora remota implementada con [gRPC](https://grpc.io) (`grpc_calculadora/`): el mismo problema de invocacion remota resuelto con un mecanismo de RPC moderno, para poder comparar ambos enfoques (ver [Calculadora gRPC](#calculadora-grpc-caracteristica-anadida)).

## Indice

- [Protocolo](#protocolo)
- [Calculadora gRPC (caracteristica anadida)](#calculadora-grpc-caracteristica-anadida)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Uso en local](#uso-en-local)
- [Uso contra el servidor desplegado](#uso-contra-el-servidor-desplegado)
- [Despliegue](#despliegue)
- [Documentacion](#documentacion)
- [Contribuir](#contribuir)

## Protocolo

Protocolo textual, orientado a lineas (cada mensaje termina en `\n`), sobre TCP.

| Comando | Comportamiento |
|---|---|
| `HOLA` | Responde `HOLA, cliente` |
| `HORA` | Responde con la fecha y hora actuales del servidor |
| `ECO <mensaje>` | Devuelve el mismo mensaje recibido |
| `CORREO <destino>\|<asunto>\|<cuerpo>` | Envia un correo real a traves de la API de [Resend](https://resend.com) |
| `SALIR` | Responde `ADIOS` y cierra la conexion |

El servidor atiende a varios clientes a la vez (un hilo por conexion) y reconstruye correctamente los mensajes aunque lleguen partidos o pegados en el flujo TCP.

## Calculadora gRPC (caracteristica anadida)

Ademas del servidor de sockets, el repositorio incluye una segunda practica de invocacion remota: una calculadora expuesta con [gRPC](https://grpc.io) en `grpc_calculadora/`. Resuelve el mismo problema de fondo (un cliente que invoca operaciones en un servidor remoto) pero con RPC moderno en lugar de sockets TCP en crudo, lo que permite comparar ambos mecanismos tal como se explican en el Tema 2 de la asignatura: aqui el contrato del servicio se declara primero, en un IDL (`calculadora.proto`), y de el se generan los stubs de cliente y servidor, en vez de construir e interpretar los mensajes a mano.

El servicio `Calculadora` expone dos de los cuatro modos de llamada de gRPC:

| Metodo | Modo | Comportamiento |
|---|---|---|
| `Sumar`, `Restar`, `Multiplicar`, `Dividir` | Unario | Una peticion con dos operandos (`a`, `b`), una respuesta con el resultado |
| `ObtenerHistorico` | Streaming de servidor | Una peticion vacia; el servidor devuelve, uno a uno, todos los registros del historial de operaciones realizadas desde que arranco |

`Dividir` entre cero no se representa con un campo de error en la respuesta: se devuelve como un error gRPC con codigo `INVALID_ARGUMENT`, que es el mecanismo propio de gRPC para separar un resultado valido de un fallo de la llamada. El historial se guarda en memoria, por lo que se reinicia en cada despliegue del servicio (no hay persistencia en disco ni en base de datos).

Uso en local:

```bash
cd grpc_calculadora
pip install -r requirements.txt

# Terminal 1
python servidor.py

# Terminal 2
python cliente.py
```

Uso contra el servicio desplegado en Railway:

```bash
python grpc_calculadora/cliente.py <host-del-servicio> <puerto>
```

Si se modifica `calculadora.proto`, los stubs (`calculadora_pb2.py` y `calculadora_pb2_grpc.py`) hay que regenerarlos con `grpc_calculadora/generar_stubs.sh` antes de volver a desplegar.

## Estructura del repositorio

```
.
├── server.py              Servidor TCP multicliente (lo que se despliega)
├── Dockerfile              Imagen del contenedor usada por Railway
├── Procfile                 Comando de arranque alternativo (Nixpacks)
├── requirements.txt         Sin dependencias externas (solo libreria estandar)
├── runtime.txt               Version de Python
├── fly.toml                  Configuracion alternativa para Fly.io (no usada actualmente)
├── client/
│   ├── client.py              Cliente interactivo de linea de comandos
│   └── prueba_multicliente.py Prueba automatica con dos clientes en paralelo
├── grpc_calculadora/           Caracteristica anadida: calculadora remota con gRPC
│   ├── calculadora.proto        Contrato del servicio (IDL)
│   ├── calculadora_pb2.py       Stub de mensajes (generado)
│   ├── calculadora_pb2_grpc.py  Stub de servicio (generado)
│   ├── servidor.py              Servidor gRPC
│   ├── cliente.py               Cliente gRPC interactivo
│   ├── generar_stubs.sh         Script para regenerar los stubs desde el .proto
│   ├── Dockerfile                Imagen del contenedor de este servicio
│   ├── Procfile
│   ├── requirements.txt
│   └── runtime.txt
└── docs/
    ├── memoria_practica_sockets.pdf   Memoria de la practica (PDF)
    ├── memoria_practica_sockets.tex   Memoria de la practica (fuente LaTeX / Overleaf)
    └── GUIA_DESPLIEGUE.md              Guia paso a paso del despliegue
```

## Uso en local

Requiere Python 3.11+ (no hay dependencias externas que instalar).

Terminal 1, arrancar el servidor:

```bash
python server.py
```

Sin las variables `RESEND_API_KEY` definidas, el servidor arranca en `MODO_PRUEBA`: el comando `CORREO` responde con normalidad pero simula el envio en vez de hacer una peticion real.

Terminal 2, cliente interactivo:

```bash
python client/client.py
```

Prueba automatica con dos clientes concurrentes:

```bash
python client/prueba_multicliente.py
```

## Uso contra el servidor desplegado

```bash
python client/client.py mainline.proxy.rlwy.net 59568
```

## Despliegue

El servidor esta desplegado en [Railway](https://railway.com), subiendo el proyecto directamente con el CLI (sin pasar por un repositorio Git intermedio para el propio despliegue):

```bash
railway login
railway link
railway up
```

Variables de entorno relevantes (se configuran en el panel de Railway, nunca en el codigo):

| Variable | Descripcion |
|---|---|
| `SERVER_HOST` | Direccion de escucha (por defecto `0.0.0.0`) |
| `SERVER_PORT` / `PORT` | Puerto interno de escucha (por defecto `5050`) |
| `RESEND_API_KEY` | Clave de API de Resend. Sin ella, el servidor queda en `MODO_PRUEBA` |
| `RESEND_FROM` | Direccion remitente (por defecto `onboarding@resend.dev`) |

El paso a paso completo, incluyendo la comparativa de plataformas consideradas y la configuracion del TCP Proxy, esta en [`docs/GUIA_DESPLIEGUE.md`](docs/GUIA_DESPLIEGUE.md).

La calculadora gRPC se despliega como un **segundo servicio, dentro del mismo proyecto de Railway**, con el directorio raiz (`Root Directory`) apuntando a `grpc_calculadora/`, para que Railway construya su propio `Dockerfile` de forma independiente del servidor de sockets. Railway le asigna su propio dominio/puerto publico (TCP Proxy), distinto del que usa `server.py`.

## Documentacion

La memoria completa de la practica ([`docs/memoria_practica_sockets.pdf`](docs/memoria_practica_sockets.pdf)) documenta el diseno, la implementacion y, con resultados reales de ejecucion, todos los problemas encontrados durante el despliegue (enrutamiento IPv6, filtrado de puertos SMTP salientes, bloqueo de Cloudflare por User-Agent) y las soluciones adoptadas para cada uno.

## Contribuir

Las propuestas de mejora y los informes de fallo se gestionan con issues (hay plantillas para ambos casos al crear uno nuevo). Los cambios de codigo se proponen mediante pull request siguiendo la plantilla correspondiente.
