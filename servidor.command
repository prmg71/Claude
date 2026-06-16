#!/usr/bin/env bash
# servidor.command — duplo clique para ligar/desligar o servidor
# Coloque este arquivo na raiz do projeto.

set -euo pipefail

# Garante que o working directory é sempre a pasta do script,
# independentemente de onde o macOS o executa.
cd "$(dirname "$0")"

PID_FILE=".uvicorn.pid"
LOG_FILE=".uvicorn.log"
UVICORN="venv/bin/uvicorn"
APP="app.api.main:app"
PORT=8000

_esta_rodando() {
  [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

ligar() {
  echo ">>> Iniciando servidor na porta $PORT..."
  "$UVICORN" "$APP" --host 0.0.0.0 --port "$PORT" \
    --log-level info >> "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  echo ">>> Servidor iniciado (PID $(cat "$PID_FILE"))."
  echo ">>> Acesse: http://localhost:$PORT/docs"
  echo ">>> Logs em: $LOG_FILE"
  echo ""
  echo "    Feche esta janela ou clique duas vezes em servidor.command para desligar."
  # Mantém o terminal aberto mostrando os logs.
  tail -f "$LOG_FILE"
}

desligar() {
  local pid
  pid=$(cat "$PID_FILE")
  echo ">>> Desligando servidor (PID $pid)..."
  kill "$pid"
  rm -f "$PID_FILE"
  echo ">>> Servidor encerrado."
  read -rp "    Pressione Enter para fechar esta janela."
}

# --- Toggle ---
if _esta_rodando; then
  desligar
else
  ligar
fi
