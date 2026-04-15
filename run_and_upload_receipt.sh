#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE_PATH="${1:-$ROOT_DIR/receipt.jpg}"
API_BASE="${API_BASE:-http://127.0.0.1:8000}"
HEALTH_URL="$API_BASE/health"
OCR_URL="$API_BASE/receipts/ocr"
LIST_URL="$API_BASE/receipts/"
LOG_PATH="$ROOT_DIR/.uvicorn.log"

if [[ ! -f "$IMAGE_PATH" ]]; then
  echo "Image not found: $IMAGE_PATH" >&2
  exit 1
fi

cd "$ROOT_DIR"

SERVER_STARTED=0

if ! curl -s "$HEALTH_URL" >/dev/null 2>&1; then
  echo "Starting API server..."
  nohup venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 >"$LOG_PATH" 2>&1 &
  SERVER_STARTED=1

  for _ in {1..30}; do
    if curl -s "$HEALTH_URL" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

if ! curl -s "$HEALTH_URL" >/dev/null 2>&1; then
  echo "Server did not start successfully. Check $LOG_PATH" >&2
  exit 1
fi

echo "Uploading: $IMAGE_PATH"
RESPONSE="$(curl -s -X POST "$OCR_URL" -F "image=@$IMAGE_PATH")"
echo "$RESPONSE"

echo
echo "Latest receipts:"
curl -s "$LIST_URL"

if [[ "$SERVER_STARTED" -eq 1 ]]; then
  echo
  echo "Server started in background. Log: $LOG_PATH"
fi
