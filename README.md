# Telegram CryptoBot

A feature-rich Telegram bot that provides cryptocurrency prices, weather information, reminders, and more. Built with Python and the python-telegram-bot library.

## Features

- 📈 **Cryptocurrency Tracking**: Get real-time prices and changes for BTC, ETH, XMR, and ERG
- 🌤️ **Weather Information**: Get current weather and 3-day forecasts by ZIP code
- ⏰ **Reminder System**: Set reminders with flexible time formats
- 📄 **Resume Analysis**: Analyze resumes (PDF/DOCX) for ATS compatibility
- 🥠 **Fortune Cookie**: Get random fortune cookie messages
- 📁 **File Handling**: Basic file information display

## Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/prices` | Get current prices of cryptocurrencies | `/prices` |
| `/setcrypto` | Manage tracked cryptocurrencies | `/setcrypto +BTC,ETH` |
| `/weather <zipcode>` | Get current weather for a ZIP code | `/weather 12345` |
| `/forecast <zipcode>` | Get 3-day forecast for a ZIP code | `/forecast 12345` |
| `/remindme <time> <message>` | Set a reminder | `/remindme 30m check email` |
| `/resume` | Analyze a resume (send PDF/DOCX) | `/resume` with attached file |
| `/fortune` | Get a fortune cookie message | `/fortune` |
| `/info` | Show help message | `/info` |
| `/thanks` | Say you're welcome | `/thanks` |

### Cryptocurrency Management
The bot allows customization of tracked cryptocurrencies using the `/setcrypto` command:
- `/setcrypto +BTC,ETH` - Add BTC and ETH to tracking
- `/setcrypto -BTC` - Remove BTC from tracking
- `/setcrypto list` - Show currently tracked coins
- `/setcrypto clear` - Clear all tracked coins

### Reminder Time Format
- Supports: weeks(w), days(d), hours(h), minutes(m), seconds(s)
- Examples:
  - `/remindme 30m check email`
  - `/remindme 1h30m team meeting`
  - `/remindme 1d birthday tomorrow`

## Prerequisites

- Docker and Docker Compose
- OpenWeatherMap API key ([Get one here](https://openweathermap.org/api))

## Deployment

### Option 1: Pull from GitHub Container Registry
\`\`\`bash
# Pull the latest version
docker pull ghcr.io/yourusername/cryptobot:latest

# Create .env file
cp .env.template .env
# Edit .env with your API keys

# Run the container
docker run -d \
  --name cryptobot \
  --env-file .env \
  -v cryptobot-data:/app/data \
  ghcr.io/yourusername/cryptobot:latest
\`\`\`

### Option 2: Build Locally with Docker Compose
\`\`\`bash
git clone https://github.com/yourusername/CryptoBot.git
cd CryptoBot
cp .env.template .env
# Edit .env with your API keys
docker compose up -d
\`\`\`

## Data Persistence

The bot uses a Docker volume (`bot-data`) to persist:
- Reminder data
- Bot state information
- Uploaded files

## Updating the Bot

1. Pull the latest changes:
\`\`\`bash
git pull origin main
\`\`\`

2. Rebuild and restart with Docker Compose:
\`\`\`bash
docker compose down
docker compose up -d --build
\`\`\`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token from BotFather | Yes |
| `WEATHER_API_KEY` | OpenWeatherMap API key | Yes |

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Container Images

The bot is available as multi-architecture Docker images from GitHub Container Registry:

### Available Tags
- `latest`, `amd64-latest`: Latest stable build for AMD64/x86_64
- `arm64-latest`: Latest stable build for ARM64/aarch64
- `sha-XXXXXXX`: Generic commit build (AMD64)
- `amd64-sha-XXXXXXX`: AMD64-specific commit build
- `arm64-sha-XXXXXXX`: ARM64-specific commit build

### Platform-Specific Pulls
```bash
# For AMD64 (x86_64) systems:
docker pull ghcr.io/yourusername/cryptobot:amd64-latest
# or for specific commit:
docker pull ghcr.io/yourusername/cryptobot:amd64-sha-abc123

# For ARM64 (aarch64) systems:
docker pull ghcr.io/yourusername/cryptobot:arm64-latest
# or for specific commit:
docker pull ghcr.io/yourusername/cryptobot:arm64-sha-abc123

# For automatic platform selection:
docker pull ghcr.io/yourusername/cryptobot:latest
```

Images are automatically built and published to GitHub Container Registry on:
- Every push to main branch
- Every pull request (for testing)
