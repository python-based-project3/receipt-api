#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE_PATH="${1:-$ROOT_DIR/receipt.jpg}"
API_URL="${API_URL:-http://127.0.0.1:8000/receipts/ocr}"

if [[ ! -f "$IMAGE_PATH" ]]; then
  echo "Image not found: $IMAGE_PATH" >&2
  exit 1
fi

echo "Uploading: $IMAGE_PATH"
echo "API: $API_URL"

curl -X POST "$API_URL" \
  -F "image=@$IMAGE_PATH"

echo
