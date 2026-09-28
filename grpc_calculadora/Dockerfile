FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Se copian tanto el codigo escrito a mano (servidor.py) como los stubs
# ya generados a partir de calculadora.proto (calculadora_pb2.py y
# calculadora_pb2_grpc.py), para no depender de protoc en el momento del
# build. Si se modifica calculadora.proto hay que regenerarlos antes de
# desplegar (ver generar_stubs.sh).
COPY calculadora_pb2.py calculadora_pb2_grpc.py servidor.py ./

EXPOSE 50051

CMD ["python", "servidor.py"]
