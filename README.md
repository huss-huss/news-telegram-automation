# 📰 News Telegram Automation

> **Automated news delivery to Telegram using n8n workflows** 🚀

A complete automation system that fetches top news headlines and delivers them directly to your Telegram chat.

![n8n](https://img.shields.io/badge/n8n-Workflow%20Automation-blue?style=for-the-badge)
![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-blue?style=for-the-badge)
![News API](https://img.shields.io/badge/News%20API-Real%20Time%20News-green?style=for-the-badge)

## ✨ Features

- 🔄 **Automated News Fetching** - Get fresh headlines from TheNewsAPI.com
- 📱 **Telegram Integration** - Instant delivery to your mobile device
- ⏰ **Scheduled Automation** - Daily news delivery at 9 AM
- 🛠️ **Manual Triggers** - Test and control workflows anytime
- 📊 **Success Logging** - Track execution and performance

## 🚀 Quick Start

### 1. Start n8n
```bash
docker run -it --rm --name n8n -p 5678:5678 \
  -e N8N_BASIC_AUTH_USER=user \
  -e N8N_BASIC_AUTH_PASSWORD=pass \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n
```

### 2. Setup Telegram Bot
```bash
./scripts/setup-telegram-bot.sh
```

### 3. Import Workflows
Import these workflows in order:
1. `workflows/02-news-api.json` - Basic news fetching
2. `workflows/03-telegram-integration.json` - News + Telegram
3. `workflows/04-scheduled-automation.json` - Full automation

## 📁 Project Structure

```
news-telegram-automation/
├── 📄 README.md
├── 📁 workflows/                   # n8n workflow files
│   ├── 02-news-api.json           # Basic news API integration
│   ├── 03-telegram-integration.json # News + Telegram sending
│   └── 04-scheduled-automation.json # Complete automation
└── 📁 scripts/                     # Setup scripts
    ├── setup-telegram-bot.sh      # Telegram bot setup
    └── get-chat-id.sh             # Chat ID finder
```

## 🔧 Workflow Details

### Workflow 02: News API Integration
- **Purpose**: Fetch news from TheNewsAPI.com
- **Trigger**: Manual
- **Features**: Error handling with fallback data

### Workflow 03: Telegram Integration
- **Purpose**: Send news to Telegram
- **Trigger**: Manual
- **Features**: Markdown formatting, error handling

### Workflow 04: Scheduled Automation
- **Purpose**: Complete automated news delivery
- **Trigger**: Daily at 9 AM
- **Features**: Full automation with logging

## 🛠️ Configuration

### Environment Variables
```bash
TELEGRAM_CHAT_ID=your_chat_id_here
NEWS_API_TOKEN=your_api_token_here
```

### Customization Options
- **Schedule Time**: Modify the Schedule Trigger node
- **News Count**: Change the `limit` parameter
- **News Categories**: Add category filters
- **Message Format**: Customize message templates

## 📱 Telegram Setup

1. **Create Bot**: Message @BotFather on Telegram
2. **Get Token**: Save the bot token provided
3. **Get Chat ID**: Use the provided script
4. **Configure**: Add credentials in n8n

```bash
./get-chat-id.sh YOUR_BOT_TOKEN
```

## 🎯 Use Cases

- **Daily News Digest** - Start your day with top headlines
- **Breaking News Alerts** - Get notified of important events
- **Custom News Feeds** - Filter by category or keywords
- **Team Updates** - Share news with colleagues

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

<div align="center">

**Made with ❤️ and ☕**

[![GitHub stars](https://img.shields.io/github/stars/yourusername/news-telegram-automation?style=social)](https://github.com/yourusername/news-telegram-automation)

</div>
