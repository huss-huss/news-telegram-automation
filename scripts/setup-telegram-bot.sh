#!/bin/bash

# Telegram Bot Setup Script for n8n News Automation
# This script helps you set up your Telegram bot for the news automation project

echo "🤖 Telegram Bot Setup for n8n News Automation"
echo "=============================================="
echo ""

# Check if user has Telegram installed
echo "📱 Step 1: Telegram App Check"
echo "Please ensure you have Telegram installed on your device."
echo "You can download it from: https://telegram.org/"
echo ""
read -p "Do you have Telegram installed? (y/n): " has_telegram

if [[ $has_telegram != "y" && $has_telegram != "Y" ]]; then
    echo "❌ Please install Telegram first, then run this script again."
    exit 1
fi

echo "✅ Great! Let's set up your bot."
echo ""

# Bot creation instructions
echo "📝 Step 2: Create Your Bot"
echo "1. Open Telegram and search for '@BotFather'"
echo "2. Start a chat with BotFather"
echo "3. Send the command: /newbot"
echo "4. Choose a name for your bot (e.g., 'News Daily Bot')"
echo "5. Choose a username (must end with 'bot', e.g., 'news_daily_bot')"
echo "6. BotFather will give you a bot token"
echo ""

read -p "Have you created your bot and received the token? (y/n): " bot_created

if [[ $bot_created != "y" && $bot_created != "Y" ]]; then
    echo "❌ Please create your bot first, then run this script again."
    exit 1
fi

# Get bot token
echo ""
echo "🔑 Step 3: Bot Token"
echo "Please enter your bot token (it looks like: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz)"
read -p "Bot Token: " bot_token

if [[ -z "$bot_token" ]]; then
    echo "❌ Bot token is required. Please run the script again."
    exit 1
fi

# Test bot token
echo ""
echo "🧪 Step 4: Testing Bot Token"
echo "Testing your bot token..."

# Make a test request to Telegram API
response=$(curl -s "https://api.telegram.org/bot$bot_token/getMe")

if [[ $response == *"\"ok\":true"* ]]; then
    echo "✅ Bot token is valid!"
    bot_name=$(echo $response | grep -o '"first_name":"[^"]*"' | cut -d'"' -f4)
    bot_username=$(echo $response | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    echo "Bot Name: $bot_name"
    echo "Bot Username: @$bot_username"
else
    echo "❌ Invalid bot token. Please check and try again."
    exit 1
fi

# Get chat ID instructions
echo ""
echo "💬 Step 5: Get Your Chat ID"
echo "1. Search for your bot in Telegram: @$bot_username"
echo "2. Start the bot by clicking 'Start'"
echo "3. Send any message to your bot (e.g., 'Hello')"
echo "4. Wait a few seconds, then press Enter to continue"
echo ""

read -p "Have you sent a message to your bot? (y/n): " message_sent

if [[ $message_sent != "y" && $message_sent != "Y" ]]; then
    echo "❌ Please send a message to your bot first, then run this script again."
    exit 1
fi

# Get chat ID
echo ""
echo "🔍 Step 6: Retrieving Chat ID"
echo "Getting your chat ID..."

updates_response=$(curl -s "https://api.telegram.org/bot$bot_token/getUpdates")

if [[ $updates_response == *"\"chat\""* ]]; then
    chat_id=$(echo $updates_response | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    echo "✅ Chat ID found: $chat_id"
else
    echo "❌ Could not find chat ID. Please try sending another message to your bot."
    exit 1
fi

# Test message
echo ""
echo "📤 Step 7: Testing Message Sending"
echo "Sending a test message to your bot..."

test_response=$(curl -s -X POST "https://api.telegram.org/bot$bot_token/sendMessage" \
  -d "chat_id=$chat_id" \
  -d "text=🎉 Hello! Your n8n news automation bot is working!" \
  -d "parse_mode=Markdown")

if [[ $test_response == *"\"ok\":true"* ]]; then
    echo "✅ Test message sent successfully!"
    echo "Check your Telegram to see the message."
else
    echo "❌ Failed to send test message. Please check your bot settings."
    exit 1
fi

# Save configuration
echo ""
echo "💾 Step 8: Saving Configuration"
echo "Creating configuration file..."

cat > .env << EOF
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=$bot_token
TELEGRAM_CHAT_ID=$chat_id

# n8n Configuration
N8N_BASIC_AUTH_USER=user
N8N_BASIC_AUTH_PASSWORD=pass
EOF

echo "✅ Configuration saved to .env file"
echo ""

# n8n setup instructions
echo "🚀 Step 9: n8n Setup Instructions"
echo "Now you need to set up your credentials in n8n:"
echo ""
echo "1. Open n8n at http://localhost:5678"
echo "2. Go to Settings (gear icon) → Credentials"
echo "3. Click 'Add Credential'"
echo "4. Select 'Telegram'"
echo "5. Fill in:"
echo "   - Name: My Telegram Bot"
echo "   - Bot Token: $bot_token"
echo "6. Click 'Save'"
echo ""

# Final instructions
echo "🎯 Next Steps:"
echo "1. Import the workflow files from the /workflows directory"
echo "2. Configure the Telegram node with your credentials"
echo "3. Set the Chat ID to: $chat_id"
echo "4. Test your workflow!"
echo ""

echo "📚 Additional Resources:"
echo "- API Setup Guide: docs/api-setup.md"
echo "- Workflow Tutorials: docs/workflow-*.md"
echo "- Troubleshooting: docs/troubleshooting.md"
echo ""

echo "🎉 Setup Complete! Your Telegram bot is ready for n8n automation."
echo ""
echo "Your bot details:"
echo "  Name: $bot_name"
echo "  Username: @$bot_username"
echo "  Chat ID: $chat_id"
echo "  Token: $bot_token"
echo ""

echo "⚠️  Security Note: Keep your bot token secret and never share it publicly!"
echo ""
