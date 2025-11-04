"""
Telegram Bridge Module
Bridges messages between Discord channels and Telegram groups
"""
import os
import json
import asyncio
import io
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

# Track seen Telegram chats for easy ID lookup
seen_telegram_chats = {}  # chat_id: {'title': str, 'type': str, 'last_seen': datetime}


async def telegram_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages from Telegram and forward to Discord."""
    print(f'[Telegram] Update received: {update}')
    
    # Support both regular messages and channel posts
    message = update.message or update.channel_post
    
    print(f'[Telegram] Has message: {message is not None}')
    if message:
        print(f'[Telegram] Message text: {message.text}')
        print(f'[Telegram] Chat type: {update.effective_chat.type if update.effective_chat else "Unknown"}')
        print(f'[Telegram] Chat ID: {update.effective_chat.id if update.effective_chat else "Unknown"}')
        print(f'[Telegram] Has photo: {message.photo is not None if message else False}')
        print(f'[Telegram] Has video: {message.video is not None if message else False}')
        print(f'[Telegram] Has document: {message.document is not None if message else False}')
    
    if not message:
        print('[Telegram] No message object')
        return
    
    # Skip if no text AND no media
    has_media = message.photo or message.video or message.document
    if not message.text and not has_media:
        print('[Telegram] Message has no text or media, skipping')
        return
    
    chat_id = str(update.effective_chat.id)
    print(f'[Telegram] Processing message from chat {chat_id}')
    
    # Track this chat for easy lookup
    from datetime import datetime
    seen_telegram_chats[chat_id] = {
        'title': update.effective_chat.title or 'Unknown',
        'type': update.effective_chat.type.value if update.effective_chat.type else 'unknown',
        'last_seen': datetime.utcnow()
    }
    
    # Check if this Telegram group is bridged
    if chat_id not in bridge_config['bridges']:
        print(f'[Telegram] Chat {chat_id} not bridged, ignoring')
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
    
    # Format username for Discord
    # For channels, use channel name instead of user
    if update.channel_post:
        username = update.effective_chat.title or "Channel"
    elif update.effective_user:
        username = update.effective_user.first_name
        if update.effective_user.last_name:
            username += f' {update.effective_user.last_name}'
    else:
        username = "Unknown"
    
    try:
        # Send text message if present
        if message.text:
            message_text = f'**[Telegram] {username}:** {message.text}'
            await discord_channel.send(message_text)
            print(f'Forwarded Telegram message from {username} to Discord #{discord_channel.name}')
        
        # Send media if present
        print(f'[Telegram] Checking for media to forward...')
        import aiohttp
        import discord as discord_lib
        
        if message.photo:
            print(f'[Telegram] Found photo, starting download...')
            try:
                # Get highest resolution photo
                photo = message.photo[-1]
                print(f'[Telegram] Getting file for photo: {photo.file_id}')
                file = await telegram_app.bot.get_file(photo.file_id)
                print(f'[Telegram] Got file path: {file.file_path}')
                
                # Download using the file's URL (bot token is embedded)
                file_url = f'https://api.telegram.org/file/bot{telegram_app.bot.token}/{file.file_path}'
                print(f'[Telegram] Downloading from: {file_url[:50]}...')
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(file_url) as resp:
                        print(f'[Telegram] Download response status: {resp.status}')
                        if resp.status == 200:
                            data = await resp.read()
                            print(f'[Telegram] Downloaded {len(data)} bytes')
                            
                            caption = f'🖼️ Photo from **[Telegram] {username}**'
                            if message.caption:
                                caption += f': {message.caption}'
                            
                            discord_file = discord_lib.File(fp=io.BytesIO(data), filename='photo.jpg')
                            print(f'[Telegram] Sending to Discord channel {discord_channel.name}')
                            await discord_channel.send(content=caption, file=discord_file)
                            print(f'✅ Forwarded Telegram photo from {username} to Discord')
                        else:
                            print(f'❌ Failed to download photo: HTTP {resp.status}')
            except Exception as photo_error:
                print(f'❌ Error forwarding photo: {photo_error}')
                import traceback
                traceback.print_exc()
        
        elif message.video:
            file = await telegram_app.bot.get_file(message.video.file_id)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://api.telegram.org/file/bot{telegram_app.bot.token}/{file.file_path}') as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        caption = f'🎥 Video from **[Telegram] {username}**'
                        if message.caption:
                            caption += f': {message.caption}'
                        
                        discord_file = discord_lib.File(fp=io.BytesIO(data), filename='video.mp4')
                        await discord_channel.send(content=caption, file=discord_file)
                        print(f'Forwarded Telegram video from {username} to Discord')
        
        elif message.document:
            file = await telegram_app.bot.get_file(message.document.file_id)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://api.telegram.org/file/bot{telegram_app.bot.token}/{file.file_path}') as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        caption = f'📄 File from **[Telegram] {username}**'
                        if message.caption:
                            caption += f': {message.caption}'
                        
                        discord_file = discord_lib.File(fp=io.BytesIO(data), filename=message.document.file_name or 'file')
                        await discord_channel.send(content=caption, file=discord_file)
                        print(f'Forwarded Telegram document from {username} to Discord')
        
    except Exception as e:
        print(f'Error forwarding to Discord: {e}')
        import traceback
        traceback.print_exc()


async def telegram_get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to get the current Telegram group ID."""
    print(f'[Telegram] /chatid command received!')
    print(f'[Telegram] Update: {update}')
    print(f'[Telegram] From user: {update.effective_user.first_name if update.effective_user else "Unknown"}')
    
    try:
        chat_id = update.effective_chat.id
        chat_title = update.effective_chat.title or "Private Chat"
        
        print(f'[Telegram] Chat ID: {chat_id}, Title: {chat_title}')
        
        await update.message.reply_text(
            f'📋 **Chat Info:**\n'
            f'Title: {chat_title}\n'
            f'Chat ID: `{chat_id}`\n\n'
            f'Use this ID in Discord with: `!linktelegram {chat_id} <discord_channel_id> <language>`'
        )
        print('[Telegram] Sent chat ID response')
    except Exception as e:
        print(f'[Telegram] Error in /chatid command: {e}')
        import traceback
        traceback.print_exc()


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


async def send_media_to_telegram(telegram_group_id: str, username: str, attachment):
    """Send media (image/video/file) from Discord to Telegram."""
    if not telegram_app:
        print('Telegram app not initialized')
        return False
    
    try:
        import aiohttp
        
        # Download the file from Discord
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status == 200:
                    file_data = await resp.read()
                    
                    caption = f'**[Discord] {username}:** {attachment.filename}'
                    
                    # Determine file type and send accordingly
                    if attachment.content_type:
                        if attachment.content_type.startswith('image/'):
                            await telegram_app.bot.send_photo(
                                chat_id=int(telegram_group_id),
                                photo=file_data,
                                caption=caption,
                                parse_mode='Markdown'
                            )
                        elif attachment.content_type.startswith('video/'):
                            await telegram_app.bot.send_video(
                                chat_id=int(telegram_group_id),
                                video=file_data,
                                caption=caption,
                                parse_mode='Markdown'
                            )
                        else:
                            await telegram_app.bot.send_document(
                                chat_id=int(telegram_group_id),
                                document=file_data,
                                caption=caption,
                                filename=attachment.filename,
                                parse_mode='Markdown'
                            )
                    else:
                        # Unknown type, send as document
                        await telegram_app.bot.send_document(
                            chat_id=int(telegram_group_id),
                            document=file_data,
                            caption=caption,
                            filename=attachment.filename,
                            parse_mode='Markdown'
                        )
                    
                    print(f'Forwarded media {attachment.filename} from {username} to Telegram group {telegram_group_id}')
                    return True
        
        return False
    except Exception as e:
        print(f'Error forwarding media to Telegram: {e}')
        import traceback
        traceback.print_exc()
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
    
    # Delete any existing webhook (webhooks block polling)
    await telegram_app.bot.delete_webhook(drop_pending_updates=True)
    print('🔧 Cleared any existing webhooks')
    
    # Add handlers for both regular messages and channel posts (text and media)
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_message_handler))
    telegram_app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, telegram_message_handler))
    telegram_app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, telegram_message_handler))
    telegram_app.add_handler(CommandHandler('chatid', telegram_get_chat_id))
    
    # Initialize and start manually (don't use run_polling - it tries to run its own loop)
    try:
        await telegram_app.initialize()
        await telegram_app.start()
        
        # Start polling manually in background task
        asyncio.create_task(_telegram_polling_task(telegram_app))
        
        # Give it a moment to start
        await asyncio.sleep(1)
        
        print('✅ Telegram bridge started successfully')
        print(f'ℹ️ Telegram bot username: @{telegram_app.bot.username}')
        print(f'ℹ️ Listening for messages and /chatid commands...')
        return telegram_app
    except Exception as e:
        print(f'❌ Error starting Telegram polling: {e}')
        import traceback
        traceback.print_exc()
        raise


async def _telegram_polling_task(app):
    """Background task to poll Telegram for updates."""
    print('🔄 Starting Telegram polling loop...')
    try:
        # Use updater.start_polling which works with existing event loop
        await app.updater.start_polling(
            poll_interval=1.0,
            timeout=10,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        print('✅ Telegram polling started')
    except Exception as e:
        print(f'❌ Telegram polling error: {e}')
        import traceback
        traceback.print_exc()


async def stop_telegram_bot():
    """Stop the Telegram bot."""
    global telegram_app
    
    if telegram_app:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
        print('Telegram bridge stopped')
