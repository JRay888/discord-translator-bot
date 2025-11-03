# Telegram Bridge Setup Guide

This guide explains how to set up and use the Telegram bridge for bidirectional messaging between Discord language channels and Telegram groups.

## Prerequisites

1. ✅ Telegram bot created and token obtained
2. ✅ `TELEGRAM_BOT_TOKEN` environment variable set in Railway
3. ✅ `python-telegram-bot` added to `requirements.txt`
4. ✅ Telegram bot added to your Telegram groups as an admin

## Setup Steps

### 1. Get Telegram Group ID

In your Telegram group, use the bot command:
```
/chatid
```

The bot will reply with the group's Chat ID (e.g., `-1001234567890`).

### 2. Get Discord Channel ID

In Discord:
- Right-click on the channel you want to link
- Click "Copy Channel ID" (you need Developer Mode enabled in Discord settings)

### 3. Link the Channels

In Discord, run the admin command:
```
!linktelegram <telegram_group_id> <discord_channel_id> <language>
```

**Example:**
```
!linktelegram -1001234567890 1234567890123456789 es
```

This links:
- Telegram group `-1001234567890`
- Discord channel `1234567890123456789`
- Language: Spanish (`es`)

### 4. Verify the Bridge

List all active bridges:
```
!listbridges
```

## Usage

Once linked, messages are forwarded **bidirectionally**:

### Discord → Telegram
- Messages sent in the Discord channel appear in the Telegram group
- Format: `**[Discord] Username:** message text`

### Telegram → Discord
- Messages sent in the Telegram group appear in the Discord channel
- Format: `**[Telegram] First Last:** message text`

## Admin Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!linktelegram <tg_id> <dc_id> <lang>` | Link a Telegram group to a Discord channel | `!linktelegram -1001234567890 1234567890123456789 es` |
| `!unlinktelegram <tg_id>` | Unlink a Telegram group | `!unlinktelegram -1001234567890` |
| `!listbridges` | List all active bridges | `!listbridges` |

All commands require **Administrator** permissions.

## Language Codes

Common language codes for the `<language>` parameter:

- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ar` - Arabic
- `ru` - Russian
- `ja` - Japanese
- `ko` - Korean
- `zh-CN` - Chinese (Simplified)
- `hi` - Hindi
- `tr` - Turkish
- `nl` - Dutch
- `pl` - Polish
- `sv` - Swedish

## Data Persistence

Bridge configurations are saved in `/app/data/bridge_config.json` on Railway, ensuring they persist across deploys.

## Troubleshooting

### Bot not forwarding messages

1. **Check Telegram bot is running:**
   - Look for `✅ Telegram bridge started` in bot logs on Railway

2. **Check bot permissions:**
   - Telegram: Bot must be an **admin** in the group
   - Discord: Bot needs **Send Messages** permission in the channel

3. **Check bridge is active:**
   - Run `!listbridges` to verify the link exists

4. **Check environment variable:**
   - Ensure `TELEGRAM_BOT_TOKEN` is set in Railway variables

### Messages forwarding only one way

- Check both bots have proper permissions in their respective platforms
- Verify the channel/group IDs are correct with `!listbridges`

### Telegram bot not responding to `/chatid`

- Ensure bot is added to the group
- Ensure bot has not been blocked
- Try removing and re-adding the bot to the group

## Example Setup for Multiple Language Rooms

```bash
# Spanish room
!linktelegram -1001234567890 1111111111111111111 es

# French room
!linktelegram -1009876543210 2222222222222222222 fr

# Arabic room
!linktelegram -1001122334455 3333333333333333333 ar
```

Now Spanish speakers can communicate seamlessly between Discord #spanish and the Telegram Spanish group, and the same for other languages!

## Notes

- Bot messages are ignored to prevent infinite loops
- Messages are forwarded as-is (no translation between platforms)
- The `language` parameter is for organizational purposes and future features
- Bridge configs persist across bot restarts and Railway deploys
