# Guia de despliegue en la nube

## Por que no se despliega desde este chat

El entorno en el que yo ejecuto codigo (esta conversacion) solo tiene salida
a internet por HTTPS y a una lista cerrada de dominios: no puede abrir
conexiones TCP en el puerto 587 (SMTP) ni exponer un puerto propio de forma
publica y permanente. Lo he comprobado directamente:

```
$ timeout 6 bash -c 'cat < /dev/null > /dev/tcp/smtp.gmail.com/587'
TCP 587 FAILED
```

Por eso el despliegue real tiene que hacerse en una plataforma de hosting,
con tu cuenta, no en esta conversacion. Aqui tienes el codigo ya preparado
y los pasos exactos.

## Comparativa de plataformas gratuitas (comprobado en septiembre de 2026)

| Plataforma | Tarjeta de credito | TCP en bruto (no solo HTTP) | SMTP 587 saliente |
|---|---|---|---|
| Railway (Full Trial, verificando con GitHub) | No | Si (TCP Proxy) | Probable, no documentado explicitamente |
| Fly.io (trial de 7 dias / 2 horas de VM) | Si, aunque no se cobra en el trial | Si, nativo | Si, confirmado |
| Render.com (plan gratuito) | No | Solo HTTP(S) en el plan gratuito | No, bloqueado desde 2025 |
| PythonAnywhere (plan gratuito) | No | No permite servidor propio con socket | No, solo en planes de pago |

**Recomendacion**: empezar por **Railway**, porque no pide tarjeta si
verificas la cuenta con GitHub. Si el proxy TCP o el puerto SMTP no
funcionan ahi, la alternativa segura es **Fly.io** (pide tarjeta al crear
la cuenta, aunque el trial no cobra nada).

## Opcion A: Railway (recomendada, sin tarjeta)

1. Crea una cuenta en https://railway.app e inicia sesion con tu cuenta de
   GitHub (la verificacion con GitHub es la que te da la "Full Trial" con
   red sin restricciones, en vez de la "Limited Trial").
2. Sube esta carpeta a un repositorio de GitHub (puede ser privado):
   ```bash
   cd "Practica - Servidor Sockets"
   git init
   git add server.py client.py Procfile runtime.txt requirements.txt
   git commit -m "Servidor de sockets con envio de correo"
   git branch -M main
   git remote add origin https://github.com/<tu_usuario>/practica-sockets.git
   git push -u origin main
   ```
3. En el panel de Railway: **New Project > Deploy from GitHub repo**, elige
   el repositorio. Railway detecta Python automaticamente (por
   `runtime.txt` y `requirements.txt`) y usa el `Procfile` para arrancar
   `python server.py`.
4. En **Settings > Networking** del servicio, activa **TCP Proxy** y
   apunta al puerto interno `5050` (el mismo que usa `server.py` por
   defecto). Railway te da un host y un puerto publicos, por ejemplo
   `containers-us-west-1.railway.app:23456` (el numero real lo veras tu en
   el panel, no lo invento aqui).
5. En **Variables**, anade (sin tocar el codigo):
   - `SMTP_USER` = tu correo (por ejemplo de Gmail)
   - `SMTP_PASSWORD` = una **contraseña de aplicacion** (no la contraseña
     normal de tu cuenta de Google; se genera en la configuracion de
     seguridad de tu cuenta de Google, con la verificacion en dos pasos
     activada)
   - Opcionalmente `SMTP_HOST` y `SMTP_PORT` si usas otro proveedor.
6. Railway reinicia el servicio solo al guardar las variables. En **Logs**
   deberias ver `Servidor escuchando en 0.0.0.0:5050 (MODO_PRUEBA=inactivo)`.
   Si sigue en `MODO_PRUEBA=activo`, revisa que las dos variables SMTP
   esten bien escritas.
7. Prueba desde tu propio ordenador:
   ```bash
   python client.py containers-us-west-1.railway.app 23456
   > CORREO tu_correo_personal@ejemplo.com|Prueba desde la nube|Hola, esto viene del servidor desplegado
   ```
   La respuesta `OK correo enviado` (o `ERROR ...` con el motivo) es la
   salida real de tu ejecucion: yo no puedo predecirla desde aqui.

## Opcion B: Fly.io (si Railway no permite el puerto SMTP)

1. Crea una cuenta en https://fly.io (pide tarjeta para verificar la
   identidad; el trial de 7 dias / 2 horas de VM no cobra nada mientras no
   lo amplies).
2. Instala `flyctl` (instrucciones oficiales en su web, cambian segun el
   sistema operativo).
3. Desde la carpeta del proyecto (usa `Dockerfile` y `fly.toml`, ya
   incluidos):
   ```bash
   flyctl auth login
   flyctl launch --no-deploy      # crea la app, usa el nombre que propongas
   flyctl secrets set SMTP_USER=tu_correo@gmail.com SMTP_PASSWORD=tu_contraseña_de_aplicacion
   flyctl deploy
   ```
4. Fly te da un host publico del tipo `tu-app.fly.dev`. Como el servicio es
   TCP puro (no HTTP), conecta indicando el puerto que pusiste en
   `fly.toml` (5050):
   ```bash
   python client.py tu-app.fly.dev 5050
   ```
5. Revisa los logs en vivo con `flyctl logs` para confirmar que el
   servidor arranco y en que modo (`MODO_PRUEBA` activo o inactivo).

## Seguridad

- Nunca subas `SMTP_USER` ni `SMTP_PASSWORD` al repositorio de GitHub:
  van solo como variables/secrets del panel de la plataforma, que es
  donde deben vivir las credenciales.
- Usa una contraseña de aplicacion, no la contraseña principal de tu
  cuenta de correo, y revocala cuando termines la practica.
- Si compartes el host y puerto publicos con el profesor para que pruebe
  el servidor, cualquiera con esa direccion puede enviar correos a traves
  de tu cuenta mientras el servicio este activo: para la entrega, apaga el
  servicio despues de la demostracion o cambia la contraseña de aplicacion.
