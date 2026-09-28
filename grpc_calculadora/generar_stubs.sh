#!/usr/bin/env bash
# Regenera calculadora_pb2.py y calculadora_pb2_grpc.py a partir de
# calculadora.proto. Hay que ejecutarlo cada vez que se modifique el
# fichero .proto, antes de volver a desplegar o de commitear el cambio.
#
# Uso:
#   cd grpc_calculadora
#   pip install grpcio-tools
#   ./generar_stubs.sh

set -euo pipefail
cd "$(dirname "$0")"
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. calculadora.proto
echo "Stubs regenerados: calculadora_pb2.py, calculadora_pb2_grpc.py"
