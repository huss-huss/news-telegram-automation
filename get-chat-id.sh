#!/bin/bash

echo "🔍 Telegram Chat ID Finder"
echo "=========================="
echo ""

# Check if bot token is provided
if [ -z "$1" ]; then
    echo "❌ Please provide your bot token as an argument"
    echo ""
    echo "Usage: ./get-chat-id.sh YOUR_BOT_TOKEN"
    echo ""
    echo "Example: ./get-chat-id.sh 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
    echo ""
    echo "To get your bot token:"
    echo "1. Open Telegram and search for @BotFather"
    echo "2. Send /newbot command"
    echo "3. Follow the instructions to create your bot"
    echo "4. Copy the token BotFather gives you"
    exit 1
fi

BOT_TOKEN="$1"

echo "🤖 Bot Token: ${BOT_TOKEN:0:10}..."
echo ""
echo "📱 Instructions:"
echo "1. Open Telegram and search for your bot"
echo "2. Start a chat with your bot"
echo "3. Send any message (like 'hello')"
echo "4. Press Enter here to check for updates..."
echo ""

read -p "Press Enter after sending a message to your bot..."

echo ""
echo "🔍 Checking for updates..."

# Get updates from Telegram API
RESPONSE=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getUpdates")

# Check if we got a response
if [ $? -ne 0 ]; then
    echo "❌ Failed to connect to Telegram API"
    echo "Please check your internet connection and bot token"
    exit 1
fi

# Check for errors in response
if echo "$RESPONSE" | grep -q '"ok":false'; then
    echo "❌ Error from Telegram API:"
    echo "$RESPONSE" | grep -o '"description":"[^"]*"' | head -1
    exit 1
fi

# Extract chat ID
CHAT_ID=$(echo "$RESPONSE" | grep -o '"chat":{"id":[0-9]*' | head -1 | grep -o '[0-9]*')

if [ -z "$CHAT_ID" ]; then
    echo "❌ No chat ID found"
    echo ""
    echo "Make sure you:"
    echo "1. Created your bot with @BotFather"
    echo "2. Started a chat with your bot"
    echo "3. Sent a message to your bot"
    echo ""
    echo "Raw response:"
    echo "$RESPONSE"
else
    echo "✅ Chat ID found: $CHAT_ID"
    echo ""
    echo "📝 Next steps:"
    echo "1. Copy this Chat ID: $CHAT_ID"
    echo "2. Update your n8n workflow with this Chat ID"
    echo "3. Or set environment variable: TELEGRAM_CHAT_ID=$CHAT_ID"
    echo ""
    echo "🎉 You're ready to send news to Telegram!"
fi
