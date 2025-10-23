# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

A Discord bot that automatically translates messages to channel-specific languages using Google Translate. Single-file Python application with JSON-based configuration storage.

## Development Commands

### Setup
```pwsh
# Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure bot (copy .env.example to .env and add DISCORD_BOT_TOKEN)
cp .env.example .env
```

### Running the Bot
```pwsh
python bot.py
```

### Testing Bot Commands
The bot uses command prefix `!`. Key commands:
- `!setlang <code>` - Set channel target language (requires Manage Channels permission)
- `!getlang` - Display current channel language
- `!removelang` - Remove channel language setting
- `!listlangs` - Show common language codes

## Architecture

### Core Components

**Single-file architecture (bot.py):**
- **Discord.py bot** with command prefix `!` and message content intents enabled
- **googletrans Translator** for language detection and translation
- **JSON persistence** (`language_config.json`) storing channel ID → language code mappings

### Critical Flow: Message Translation

1. **on_message event** receives all messages
2. Bot **ignores** its own messages and command invocations
3. Checks if channel ID exists in `language_config` dictionary
4. If configured:
   - Detects source language via `translator.detect()`
   - Only translates if source ≠ target language
   - Posts Discord embed with author info and language arrow (e.g., "EN → ES")
5. Silently catches translation errors to avoid spam

### State Management

- **language_config** dict loaded on startup from `language_config.json`
- Persisted to disk after every `!setlang` and `!removelang` command
- Channel IDs stored as strings (JSON serialization requirement)

### Permission Model

Commands requiring `manage_channels` permission:
- `!setlang`
- `!removelang`

Error handler (`on_command_error`) provides user-friendly permission denial messages.

## Environment Configuration

**Required:** `DISCORD_BOT_TOKEN` in `.env` file (never commit this)

**Discord Bot Setup Requirements:**
- Message Content Intent must be enabled in Discord Developer Portal
- Bot needs these permissions: Read Messages, Send Messages, Embed Links, Read Message History

## Important Notes

- Uses **googletrans 4.0.0rc1** (free, unofficial Google Translate API - rate limits may apply)
- No unit tests present in codebase
- No linting/formatting configuration files
- Translation errors are logged to console but not surfaced to users
- Original messages remain visible; translations posted as separate embeds
