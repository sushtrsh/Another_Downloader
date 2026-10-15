#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1

IFS='|' read -r API_ID API_HASH PORT < <(python3 -c '
import json
from urllib.parse import urlparse
c = json.load(open("config.json", encoding="utf-8"))
port = urlparse(c.get("LOCAL_API_URL", "")).port or 8081
print("|".join([str(c.get("API_ID", "")), str(c.get("API_HASH", "")), str(port)]))
')

if [ -z "$API_ID" ] || [ -z "$API_HASH" ]; then
  echo "Isi API_ID dan API_HASH di config.json dulu."
  exit 1
fi

mkdir -p "$HOME/tgapi-data"
exec "$HOME/telegram-bot-api/bin/telegram-bot-api" \
  --api-id="$API_ID" --api-hash="$API_HASH" \
  --local --http-ip-address=127.0.0.1 --http-port="$PORT" \
  --dir="$HOME/tgapi-data"
