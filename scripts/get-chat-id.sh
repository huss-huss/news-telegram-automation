#!/usr/bin/env bash
# Print the chat ID(s) that recently messaged your Telegram bot.
#
# Usage:
#   TELEGRAM_BOT_TOKEN=... ./scripts/get-chat-id.sh   # token from the environment
#   ./scripts/get-chat-id.sh                          # prompts for the token (input hidden)
#
# The token is never echoed and is passed to curl on stdin, so it does not show up
# in the process list or your shell history.
set -euo pipefail

token="${TELEGRAM_BOT_TOKEN:-}"
if [[ -z "$token" ]]; then
  read -r -s -p "Bot token (from @BotFather): " token
  echo
fi
if [[ ! "$token" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
  echo "error: that does not look like a bot token (expected <digits>:<characters>)" >&2
  exit 1
fi

echo "1. Open Telegram and send any message to your bot (or add it to a group and post there)."
read -r -p "2. Press Enter once the message is sent... "

if ! response="$(printf 'url = "https://api.telegram.org/bot%s/getUpdates"\n' "$token" \
    | curl --silent --show-error --max-time 15 --config -)"; then
  echo "error: could not reach the Telegram API" >&2
  exit 1
fi

if [[ "$response" == *'"ok":false'* ]]; then
  echo "error: Telegram API returned an error:" >&2
  grep -o '"description":"[^"]*"' <<<"$response" >&2 || true
  exit 1
fi

chat_ids="$(grep -oE '"chat":\{"id":-?[0-9]+' <<<"$response" | grep -oE -- '-?[0-9]+$' | sort -u || true)"
if [[ -z "$chat_ids" ]]; then
  echo "No chat found yet. Send a message to the bot, wait a few seconds and run this again." >&2
  exit 1
fi

echo
echo "Chat ID(s) that messaged the bot:"
echo "$chat_ids"
echo
echo "Put the one you want in .env as TELEGRAM_CHAT_ID=<id>."
