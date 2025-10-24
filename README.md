# Discord Translator Bot

A Discord bot that automatically translates messages to different languages based on channel settings. Perfect for multilingual Discord servers where different channels are dedicated to specific languages.

## Features

- 🌍 **Multi-language support** - Supports 100+ languages via Google Translate
- 👥 **Translation Groups** - Group multiple channels together for automatic cross-translation
- 🚩 **Flag Reactions** - React with flag emojis to translate messages on-demand
- 🤖 **Automatic translation** - Messages in grouped channels are automatically translated
- 💬 **Preserved context** - Shows original author and source/target languages
- 🔐 **Permission-based** - Only users with channel management permissions can configure settings

## Commands

### Translation Groups

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `!creategroup <name>` | Create a new translation group | Manage Channels |
| `!addchannel <group> <lang>` | Add current channel to a group with language | Manage Channels |
| `!removechannel` | Remove current channel from its group | Manage Channels |
| `!deletegroup <name>` | Delete a translation group | Manage Channels |
| `!listgroups` | List all translation groups | None |

### Flag Reactions

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `!enableflags` | Enable flag reactions in current channel | Manage Channels |
| `!disableflags` | Disable flag reactions in current channel | Manage Channels |

### General

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `!channelinfo` | Display current channel's translation settings | None |
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
   - Add Reactions
   - Manage Messages (optional)
4. Copy the generated URL and open it in your browser
5. Select your server and authorize

### 6. Run the Bot

```bash
python bot.py
```

## Usage Examples

### Setting up Translation Groups

Create a group where messages are automatically translated between channels:

```
# Create a group for general chat
!creategroup general

# In your #english channel
!addchannel general en

# In your #spanish channel
!addchannel general es

# In your #french channel
!addchannel general fr
```

Now messages in any of these channels will automatically appear translated in the other channels!

### Setting up Flag Reactions

Enable on-demand translation via flag reactions:

```
# In any channel where you want flag reactions
!enableflags
```

Users can now react to any message with a flag emoji (🇪🇸, 🇫🇷, 🇯🇵, etc.) to get an instant translation!

### Supported Flag Emojis

- 🇺🇸 🇬🇧 English
- 🇪🇸 🇲🇽 Spanish
- 🇫🇷 French
- 🇩🇪 German
- 🇮🇹 Italian
- 🇵🇹 🇧🇷 Portuguese
- 🇷🇺 Russian
- 🇯🇵 Japanese
- 🇰🇷 Korean
- 🇨🇳 Chinese
- 🇸🇦 Arabic
- 🇮🇳 Hindi
- And many more!

### Checking configuration

```
# View current channel settings
!channelinfo

# List all groups
!listgroups
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

### Translation Groups

1. Server administrators create translation groups and add channels to them
2. When a user sends a message in any grouped channel:
   - The bot detects which group the channel belongs to
   - Translates the message to all other languages in that group
   - Posts translations in each corresponding channel
3. Each group operates independently

### Flag Reactions

1. Server administrators enable flag reactions in specific channels
2. When a user reacts to a message with a flag emoji:
   - The bot detects which language the flag represents
   - Translates the message to that language
   - Replies to the message with the translation
3. Multiple users can request different translations of the same message

## Configuration Storage

All settings are stored in `language_config.json` in the bot's directory:
- Translation groups and their channel mappings
- Flag-enabled channels

This file is automatically created and updated when you use bot commands.

**Note:** If deploying to Railway or similar platforms, this file will reset on container restart unless you set up persistent storage or use environment variables.

## Troubleshooting

### Bot doesn't respond
- Check that Message Content Intent is enabled in Discord Developer Portal
- Verify the bot has proper permissions in your server
- For flag reactions, ensure the bot has Add Reactions permission

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
