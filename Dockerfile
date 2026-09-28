# Dockerfile: usado tanto por Railway como por Fly.io si esta presente
# (ambas plataformas priorizan el Dockerfile sobre Procfile/Nixpacks
# cuando lo encuentran en la raiz del proyecto).
FROM python:3.11-slim
WORKDIR /app
COPY server.py .
EXPOSE 5050
# PYTHONUNBUFFERED evita que Python retenga los print() en un buffer de
# bloque cuando la salida no va a una terminal (como en un contenedor):
# sin esto, "Servidor escuchando..." podia no llegar nunca a los logs.
ENV PYTHONUNBUFFERED=1
CMD ["python", "-u", "server.py"]
