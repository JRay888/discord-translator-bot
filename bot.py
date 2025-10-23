import discord
from discord.ext import commands
import json
import os
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Storage for channel language mappings
LANGUAGE_CONFIG_FILE = 'language_config.json'


def load_language_config():
    """Load language configuration from JSON file."""
    if os.path.exists(LANGUAGE_CONFIG_FILE):
        with open(LANGUAGE_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_language_config(config):
    """Save language configuration to JSON file."""
    with open(LANGUAGE_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


# Load config on startup
language_config = load_language_config()


@bot.event
async def on_ready():
    """Event handler for when bot is ready."""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guild(s)')


@bot.command(name='setlang', help='Set language for a channel. Usage: !setlang <language_code>')
@commands.has_permissions(manage_channels=True)
async def set_language(ctx, language_code: str):
    """
    Set the target language for a channel.
    Examples: !setlang es (Spanish), !setlang fr (French), !setlang ja (Japanese)
    """
    channel_id = str(ctx.channel.id)
    language_config[channel_id] = language_code.lower()
    save_language_config(language_config)
    
    await ctx.send(f'✅ Channel language set to: **{language_code.upper()}**\n'
                   f'Messages will now be translated to {language_code.upper()}')


@bot.command(name='getlang', help='Get the current language setting for this channel')
async def get_language(ctx):
    """Display the current language setting for the channel."""
    channel_id = str(ctx.channel.id)
    
    if channel_id in language_config:
        lang = language_config[channel_id]
        await ctx.send(f'📍 Current channel language: **{lang.upper()}**')
    else:
        await ctx.send('❌ No language set for this channel. Use `!setlang <code>` to set one.')


@bot.command(name='removelang', help='Remove language setting for this channel')
@commands.has_permissions(manage_channels=True)
async def remove_language(ctx):
    """Remove the language setting for a channel."""
    channel_id = str(ctx.channel.id)
    
    if channel_id in language_config:
        del language_config[channel_id]
        save_language_config(language_config)
        await ctx.send('✅ Language setting removed for this channel.')
    else:
        await ctx.send('❌ No language setting found for this channel.')


@bot.command(name='listlangs', help='List all language codes available')
async def list_languages(ctx):
    """Display common language codes."""
    langs = """
    **Common Language Codes:**
    `en` - English
    `es` - Spanish
    `fr` - French
    `de` - German
    `it` - Italian
    `pt` - Portuguese
    `ru` - Russian
    `ja` - Japanese
    `ko` - Korean
    `zh-cn` - Chinese (Simplified)
    `ar` - Arabic
    `hi` - Hindi
    
    For more codes, visit: https://cloud.google.com/translate/docs/languages
    """
    await ctx.send(langs)


@bot.event
async def on_message(message):
    """Handle incoming messages and cross-post translations to all language channels."""
    # Ignore bot's own messages
    if message.author.bot:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Skip if message is a command
    if message.content.startswith(bot.command_prefix):
        return
    
    # Check if the message is from a language-configured channel
    source_channel_id = str(message.channel.id)
    
    if source_channel_id in language_config:
        source_lang = language_config[source_channel_id]
        
        # Get all other language channels in the same guild
        for channel_id, target_lang in language_config.items():
            # Skip if it's the same channel or same language
            if channel_id == source_channel_id or target_lang == source_lang:
                continue
            
            try:
                # Get the target channel
                target_channel = bot.get_channel(int(channel_id))
                
                # Skip if channel not found or not in the same guild
                if not target_channel or target_channel.guild.id != message.guild.id:
                    continue
                
                # Translate the message
                translator = GoogleTranslator(source=source_lang, target=target_lang)
                translated_text = translator.translate(message.content)
                
                # Create embed with translation
                embed = discord.Embed(
                    description=translated_text,
                    color=discord.Color.blue()
                )
                embed.set_author(
                    name=f"{message.author.display_name} (from #{message.channel.name})",
                    icon_url=message.author.avatar.url if message.author.avatar else None
                )
                embed.set_footer(text=f"{source_lang.upper()} → {target_lang.upper()}")
                
                # Send to target channel
                await target_channel.send(embed=embed)
                
            except Exception as e:
                print(f'Translation error for {channel_id}: {e}')
                # Continue to next channel even if one fails


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ You don\'t have permission to use this command.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'❌ Missing required argument. Use `!help {ctx.command}` for usage.')
    else:
        print(f'Error: {error}')


# Run the bot
if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    if not TOKEN:
        print('ERROR: DISCORD_BOT_TOKEN not found in environment variables!')
        print('Please create a .env file with your bot token.')
    else:
        bot.run(TOKEN)
