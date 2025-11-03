"""
Telegram Bridge Module
Bridges messages between Discord channels and Telegram groups
"""
import os
import json
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

# Bridge configuration file
BRIDGE_CONFIG_FILE = 'bridge_config.json'

# Store the Discord bot reference
discord_bot = None


def load_bridge_config():
    """Load bridge configuration from JSON file."""
    data_dir = '/app/data' if os.path.exists('/app/data') else os.path.dirname(__file__)
    config_file = os.path.join(data_dir, BRIDGE_CONFIG_FILE)
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {
        'bridges': {}  # telegram_group_id: {'discord_channel_id': 'xxx', 'language': 'es'}
    }


def save_bridge_config(config):
    """Save bridge configuration to JSON file."""
    data_dir = '/app/data' if os.path.exists('/app/data') else os.path.dirname(__file__)
    config_file = os.path.join(data_dir, BRIDGE_CONFIG_FILE)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)


bridge_config = load_bridge_config()


async def telegram_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages from Telegram and forward to Discord."""
    if not update.message or not update.message.text:
        return
    
    chat_id = str(update.effective_chat.id)
    
    # Check if this Telegram group is bridged
    if chat_id not in bridge_config['bridges']:
        return
    
    bridge_info = bridge_config['bridges'][chat_id]
    discord_channel_id = bridge_info['discord_channel_id']
    
    # Get Discord channel
    if not discord_bot:
        print('Discord bot not initialized')
        return
    
    discord_channel = discord_bot.get_channel(int(discord_channel_id))
    if not discord_channel:
        print(f'Discord channel {discord_channel_id} not found')
        return
    
    # Format message for Discord
    username = update.effective_user.first_name
    if update.effective_user.last_name:
        username += f' {update.effective_user.last_name}'
    
    message_text = f'**[Telegram] {username}:** {update.message.text}'
    
    try:
        await discord_channel.send(message_text)
        print(f'Forwarded Telegram message from {username} to Discord #{discord_channel.name}')
    except Exception as e:
        print(f'Error forwarding to Discord: {e}')


async def telegram_get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to get the current Telegram group ID."""
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title or "Private Chat"
    
    await update.message.reply_text(
        f'📋 **Chat Info:**\n'
        f'Title: {chat_title}\n'
        f'Chat ID: `{chat_id}`\n\n'
        f'Use this ID in Discord with: `!linktelegraming <discord_channel_id> <language>`'
    )


async def send_to_telegram(telegram_group_id: str, username: str, message: str):
    """Send a message from Discord to Telegram."""
    if not telegram_app:
        print('Telegram app not initialized')
        return False
    
    try:
        formatted_message = f'**[Discord] {username}:** {message}'
        await telegram_app.bot.send_message(
            chat_id=int(telegram_group_id),
            text=formatted_message,
            parse_mode='Markdown'
        )
        print(f'Forwarded Discord message from {username} to Telegram group {telegram_group_id}')
        return True
    except Exception as e:
        print(f'Error forwarding to Telegram: {e}')
        return False


telegram_app = None


async def start_telegram_bot(discord_bot_instance):
    """Start the Telegram bot."""
    global telegram_app, discord_bot
    
    # Try to get token from environment, fallback to hardcoded for Railway testing
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # TEMPORARY: Hardcode for testing Railway deployment
    if not token:
        token = '8482820935:AAGTJ3IH6fcfoGgTI6lG7RlcgdtFboAqETA'
        print('⚠️  Using hardcoded token (REMOVE THIS IN PRODUCTION!)')
    
    if not token:
        print('⚠️  TELEGRAM_BOT_TOKEN not found - Telegram bridge disabled')
        return None
    
    discord_bot = discord_bot_instance
    
    # Create Telegram application
    telegram_app = Application.builder().token(token).build()
    
    # Add handlers
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_message_handler))
    telegram_app.add_handler(CommandHandler('chatid', telegram_get_chat_id))
    
    # Start polling in the background
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    
    print('✅ Telegram bridge started')
    return telegram_app


async def stop_telegram_bot():
    """Stop the Telegram bot."""
    global telegram_app
    
    if telegram_app:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
        print('Telegram bridge stopped')
