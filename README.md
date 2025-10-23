# Discord Translator Bot

A Discord bot that automatically translates messages to different languages based on channel settings. Perfect for multilingual Discord servers where different channels are dedicated to specific languages.

## Features

- 🌍 **Multi-language support** - Supports 100+ languages via Google Translate
- 🔧 **Channel-specific settings** - Set different target languages for different channels
- 🤖 **Automatic translation** - Messages are automatically translated to the channel's language
- 💬 **Preserved context** - Shows original author and source/target languages
- 🔐 **Permission-based** - Only users with channel management permissions can configure languages

## Commands

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `!setlang <code>` | Set the target language for the current channel | Manage Channels |
| `!getlang` | Display the current language setting | None |
| `!removelang` | Remove language setting for the channel | Manage Channels |
| `!listlangs` | Show common language codes | None |

## Setup

### 1. Prerequisites

- Python 3.8 or higher
- A Discord account
- Discord Developer Portal access

### 2. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot"
5. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
   - Server Members Intent (optional)
6. Copy your bot token (you'll need this later)

### 3. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Bot

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your bot token:
   ```
   DISCORD_BOT_TOKEN=your_actual_token_here
   ```

### 5. Invite Bot to Server

1. Go to Discord Developer Portal > Your App > OAuth2 > URL Generator
2. Select scopes:
   - `bot`
   - `applications.commands`
3. Select bot permissions:
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
   - Read Message History
   - Manage Messages (optional)
4. Copy the generated URL and open it in your browser
5. Select your server and authorize

### 6. Run the Bot

```bash
python bot.py
```

## Usage Examples

### Setting up language rooms

```
# In your #spanish channel
!setlang es

# In your #french channel
!setlang fr

# In your #japanese channel
!setlang ja
```

### Checking configuration

```
!getlang
```

### Viewing available languages

```
!listlangs
```

## Common Language Codes

- `en` - English
- `es` - Spanish (Español)
- `fr` - French (Français)
- `de` - German (Deutsch)
- `it` - Italian (Italiano)
- `pt` - Portuguese (Português)
- `ru` - Russian (Русский)
- `ja` - Japanese (日本語)
- `ko` - Korean (한국어)
- `zh-cn` - Chinese Simplified (简体中文)
- `zh-tw` - Chinese Traditional (繁體中文)
- `ar` - Arabic (العربية)
- `hi` - Hindi (हिन्दी)

For a complete list, see [Google Translate Language Codes](https://cloud.google.com/translate/docs/languages).

## How It Works

1. Server administrators set a target language for each channel using `!setlang`
2. When users send messages in those channels, the bot:
   - Detects the source language
   - Translates to the target language (if different)
   - Posts the translation with the author's name and language info
3. The original message remains visible for context

## Configuration Storage

Language settings are stored in `language_config.json` in the bot's directory. This file is automatically created and updated when you use the `!setlang` command.

## Troubleshooting

### Bot doesn't respond
- Check that Message Content Intent is enabled in Discord Developer Portal
- Verify the bot has proper permissions in your server

### Translation errors
- The bot uses Google Translate's free API which may have rate limits
- Some messages may be too long to translate
- Check console for error messages

### Bot token errors
- Make sure `.env` file exists and contains valid token
- Token should have no quotes or extra spaces

## Contributing

Feel free to submit issues or pull requests to improve the bot!

## License

MIT License - Feel free to use and modify as needed.

## Disclaimer

This bot uses Google Translate via the `googletrans` library. For production use with high volume, consider using the official Google Cloud Translation API with proper authentication and billing.
