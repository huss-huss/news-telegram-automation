#!/usr/bin/env bash
# Interactive helper: verify a Telegram bot token, find your chat ID, send a test
# message and write TELEGRAM_CHAT_ID into .env (created from .env.example).
#
# The bot token itself is NOT written to .env: store it as an n8n "Telegram API"
# credential instead (Settings -> Credentials). It is never printed by this script.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$repo_root/.env"

telegram_api() {
  # $1 = method, remaining args are extra curl options. Token goes via stdin config.
  local method="$1"
  shift
  printf 'url = "https://api.telegram.org/bot%s/%s"\n' "$bot_token" "$method" \
    | curl --silent --show-error --max-time 15 --config - "$@"
}

json_field() {
  # Extract the first "key":"value" string from JSON on stdin.
  grep -o "\"$1\":\"[^\"]*\"" | head -n 1 | cut -d '"' -f 4
}

echo "Telegram bot setup for n8n news automation"
echo "==========================================="
echo
echo "1. In Telegram, open @BotFather, send /newbot and follow the prompts."
echo "2. BotFather replies with a bot token."
echo
read -r -s -p "Paste the bot token (input hidden): " bot_token
echo
if [[ ! "$bot_token" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
  echo "error: that does not look like a bot token" >&2
  exit 1
fi

me="$(telegram_api getMe)"
if [[ "$me" != *'"ok":true'* ]]; then
  echo "error: Telegram rejected the token" >&2
  exit 1
fi
bot_username="$(json_field username <<<"$me")"
echo "Token is valid for @${bot_username}."
echo
echo "3. Open @${bot_username} in Telegram, press Start and send any message."
read -r -p "   Press Enter when done... "

updates="$(telegram_api getUpdates)"
chat_id="$(grep -oE '"chat":\{"id":-?[0-9]+' <<<"$updates" | head -n 1 | grep -oE -- '-?[0-9]+$' || true)"
if [[ -z "$chat_id" ]]; then
  echo "error: no chat found; send another message to the bot and re-run" >&2
  exit 1
fi
echo "Found chat ID: ${chat_id}"

sent="$(telegram_api sendMessage --data-urlencode "chat_id=${chat_id}" \
  --data-urlencode "text=Your n8n news bot is connected.")"
if [[ "$sent" != *'"ok":true'* ]]; then
  echo "error: could not send the test message" >&2
  exit 1
fi
echo "Test message sent. Check Telegram."

if [[ ! -f "$env_file" ]]; then
  cp "$repo_root/.env.example" "$env_file"
  echo "Created .env from .env.example"
fi
chmod 600 "$env_file"
tmp_file="$(mktemp)"
grep -v '^TELEGRAM_CHAT_ID=' "$env_file" >"$tmp_file" || true
echo "TELEGRAM_CHAT_ID=${chat_id}" >>"$tmp_file"
cat "$tmp_file" >"$env_file"
rm -f "$tmp_file"
echo "Saved TELEGRAM_CHAT_ID to .env"

cat <<MSG

Next steps:
  1. docker compose up -d   (then open http://localhost:5678)
  2. In n8n: Settings -> Credentials -> Add "Telegram API", paste the bot token,
     name it "Telegram bot".
  3. Import the workflows (see README) and select that credential on the Telegram nodes.
MSG
