# Servidor de sockets multicliente con envio de correo (Sistemas Distribuidos)

Practica de la asignatura de Sistemas Distribuidos (Tema 2: Comunicacion). Implementa un servidor TCP multicliente en Python, con un pequeno protocolo de aplicacion propio, y un comando que delega el envio de un correo electronico real en un sistema de mensajeria externo (un MOM, en la terminologia de la asignatura).

El servidor esta desplegado publicamente en Railway y es accesible por cualquier cliente TCP.

## Indice

- [Protocolo](#protocolo)
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

## Documentacion

La memoria completa de la practica ([`docs/memoria_practica_sockets.pdf`](docs/memoria_practica_sockets.pdf)) documenta el diseno, la implementacion y, con resultados reales de ejecucion, todos los problemas encontrados durante el despliegue (enrutamiento IPv6, filtrado de puertos SMTP salientes, bloqueo de Cloudflare por User-Agent) y las soluciones adoptadas para cada uno.

## Contribuir

Las propuestas de mejora y los informes de fallo se gestionan con issues (hay plantillas para ambos casos al crear uno nuevo). Los cambios de codigo se proponen mediante pull request siguiendo la plantilla correspondiente.
