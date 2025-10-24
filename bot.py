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
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Storage for channel language mappings
LANGUAGE_CONFIG_FILE = 'language_config.json'

# Flag emoji to language code mapping
FLAG_TO_LANG = {
    '🇺🇸': 'en', '🇬🇧': 'en',  # English
    '🇪🇸': 'es', '🇲🇽': 'es',  # Spanish
    '🇫🇷': 'fr',  # French
    '🇩🇪': 'de',  # German
    '🇮🇹': 'it',  # Italian
    '🇵🇹': 'pt', '🇧🇷': 'pt',  # Portuguese
    '🇷🇺': 'ru',  # Russian
    '🇯🇵': 'ja',  # Japanese
    '🇰🇷': 'ko',  # Korean
    '🇨🇳': 'zh-CN',  # Chinese (Simplified)
    '🇸🇦': 'ar',  # Arabic
    '🇮🇳': 'hi',  # Hindi
    '🇳🇱': 'nl',  # Dutch
    '🇵🇱': 'pl',  # Polish
    '🇹🇷': 'tr',  # Turkish
    '🇸🇪': 'sv',  # Swedish
    '🇳🇴': 'no',  # Norwegian
    '🇩🇰': 'da',  # Danish
    '🇫🇮': 'fi',  # Finnish
}


def load_language_config():
    """Load language configuration from JSON file."""
    if os.path.exists(LANGUAGE_CONFIG_FILE):
        with open(LANGUAGE_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'groups': {},  # group_name: {channel_id: language}
        'flag_enabled_channels': []  # list of channel IDs where flag reactions are enabled
    }


def save_language_config(config):
    """Save language configuration to JSON file."""
    with open(LANGUAGE_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


# Load config on startup
language_config = load_language_config()

# Ensure structure exists
if 'groups' not in language_config:
    language_config['groups'] = {}
if 'flag_enabled_channels' not in language_config:
    language_config['flag_enabled_channels'] = []


@bot.event
async def on_ready():
    """Event handler for when bot is ready."""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guild(s)')


@bot.command(name='creategroup', help='Create a translation group. Usage: !creategroup <group_name>')
@commands.has_permissions(manage_channels=True)
async def create_group(ctx, group_name: str):
    """Create a new translation group."""
    if group_name in language_config['groups']:
        await ctx.send(f'❌ Group **{group_name}** already exists.')
        return
    
    language_config['groups'][group_name] = {}
    save_language_config(language_config)
    await ctx.send(f'✅ Created translation group: **{group_name}**\n'
                   f'Use `!addchannel {group_name} <lang>` to add channels to this group.')


@bot.command(name='addchannel', help='Add channel to a group. Usage: !addchannel <group_name> <language_code>')
@commands.has_permissions(manage_channels=True)
async def add_channel(ctx, group_name: str, language_code: str):
    """Add the current channel to a translation group with a specific language."""
    if group_name not in language_config['groups']:
        await ctx.send(f'❌ Group **{group_name}** does not exist. Create it with `!creategroup {group_name}` first.')
        return
    
    channel_id = str(ctx.channel.id)
    language_config['groups'][group_name][channel_id] = language_code.lower()
    save_language_config(language_config)
    
    await ctx.send(f'✅ Added **{ctx.channel.name}** to group **{group_name}** with language **{language_code.upper()}**')


@bot.command(name='removechannel', help='Remove current channel from its group')
@commands.has_permissions(manage_channels=True)
async def remove_channel(ctx):
    """Remove the current channel from any translation group."""
    channel_id = str(ctx.channel.id)
    removed = False
    
    for group_name, channels in language_config['groups'].items():
        if channel_id in channels:
            del channels[channel_id]
            removed = True
            await ctx.send(f'✅ Removed **{ctx.channel.name}** from group **{group_name}**')
            break
    
    if removed:
        save_language_config(language_config)
    else:
        await ctx.send('❌ This channel is not in any translation group.')


@bot.command(name='deletegroup', help='Delete a translation group. Usage: !deletegroup <group_name>')
@commands.has_permissions(manage_channels=True)
async def delete_group(ctx, group_name: str):
    """Delete a translation group."""
    if group_name not in language_config['groups']:
        await ctx.send(f'❌ Group **{group_name}** does not exist.')
        return
    
    del language_config['groups'][group_name]
    save_language_config(language_config)
    await ctx.send(f'✅ Deleted translation group: **{group_name}**')


@bot.command(name='listgroups', help='List all translation groups')
async def list_groups(ctx):
    """List all translation groups and their channels."""
    if not language_config['groups']:
        await ctx.send('❌ No translation groups exist. Create one with `!creategroup <name>`')
        return
    
    embed = discord.Embed(title='Translation Groups', color=discord.Color.blue())
    
    for group_name, channels in language_config['groups'].items():
        if channels:
            channel_list = []
            for ch_id, lang in channels.items():
                channel = bot.get_channel(int(ch_id))
                if channel:
                    channel_list.append(f'<#{ch_id}> ({lang.upper()})')
            if channel_list:
                embed.add_field(name=group_name, value='\n'.join(channel_list), inline=False)
        else:
            embed.add_field(name=group_name, value='*No channels*', inline=False)
    
    await ctx.send(embed=embed)


@bot.command(name='enableflags', help='Enable flag reactions for translation in this channel')
@commands.has_permissions(manage_channels=True)
async def enable_flags(ctx):
    """Enable flag reaction translations for the current channel."""
    channel_id = str(ctx.channel.id)
    
    if channel_id in language_config['flag_enabled_channels']:
        await ctx.send('❌ Flag reactions are already enabled in this channel.')
        return
    
    language_config['flag_enabled_channels'].append(channel_id)
    save_language_config(language_config)
    await ctx.send('✅ Flag reactions enabled! Users can now react with flag emojis to translate messages.\n'
                   'Example: React with 🇪🇸 for Spanish, 🇫🇷 for French, etc.')


@bot.command(name='disableflags', help='Disable flag reactions in this channel')
@commands.has_permissions(manage_channels=True)
async def disable_flags(ctx):
    """Disable flag reaction translations for the current channel."""
    channel_id = str(ctx.channel.id)
    
    if channel_id not in language_config['flag_enabled_channels']:
        await ctx.send('❌ Flag reactions are not enabled in this channel.')
        return
    
    language_config['flag_enabled_channels'].remove(channel_id)
    save_language_config(language_config)
    await ctx.send('✅ Flag reactions disabled for this channel.')


@bot.command(name='channelinfo', help='Get info about the current channel')
async def channel_info(ctx):
    """Display translation settings for the current channel."""
    channel_id = str(ctx.channel.id)
    
    # Check if in a group
    in_group = None
    channel_lang = None
    for group_name, channels in language_config['groups'].items():
        if channel_id in channels:
            in_group = group_name
            channel_lang = channels[channel_id]
            break
    
    # Check if flags enabled
    flags_enabled = channel_id in language_config['flag_enabled_channels']
    
    embed = discord.Embed(title=f'Channel Info: {ctx.channel.name}', color=discord.Color.blue())
    
    if in_group:
        embed.add_field(name='Translation Group', value=f'**{in_group}** ({channel_lang.upper()})', inline=False)
    else:
        embed.add_field(name='Translation Group', value='Not in any group', inline=False)
    
    embed.add_field(name='Flag Reactions', value='✅ Enabled' if flags_enabled else '❌ Disabled', inline=False)
    
    await ctx.send(embed=embed)


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
    """Handle incoming messages and cross-post translations to group channels."""
    # Ignore bot's own messages
    if message.author.bot:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Skip if message is a command
    if message.content.startswith(bot.command_prefix):
        return
    
    # Check if the message is from a channel in a translation group
    source_channel_id = str(message.channel.id)
    
    # Find which group this channel belongs to
    for group_name, channels in language_config['groups'].items():
        if source_channel_id in channels:
            source_lang = channels[source_channel_id]
            
            # Translate to all other channels in the same group
            for target_channel_id, target_lang in channels.items():
                # Skip if it's the same channel or same language
                if target_channel_id == source_channel_id or target_lang == source_lang:
                    continue
                
                try:
                    # Get the target channel
                    target_channel = bot.get_channel(int(target_channel_id))
                    
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
                    embed.set_footer(text=f"{source_lang.upper()} → {target_lang.upper()} | Group: {group_name}")
                    
                    # Send to target channel
                    await target_channel.send(embed=embed)
                    
                except Exception as e:
                    print(f'Translation error for {target_channel_id} in group {group_name}: {e}')
                    # Continue to next channel even if one fails
            
            # Only process for one group (channel shouldn't be in multiple groups)
            break


@bot.event
async def on_reaction_add(reaction, user):
    """Handle flag reactions for on-demand translation."""
    # Ignore bot's own reactions
    if user.bot:
        return
    
    # Check if channel has flag reactions enabled
    channel_id = str(reaction.message.channel.id)
    if channel_id not in language_config['flag_enabled_channels']:
        return
    
    # Check if reaction is a flag emoji
    emoji = str(reaction.emoji)
    if emoji not in FLAG_TO_LANG:
        return
    
    target_lang = FLAG_TO_LANG[emoji]
    
    # Don't translate empty messages
    if not reaction.message.content:
        return
    
    try:
        # Translate the message
        translator = GoogleTranslator(source='auto', target=target_lang)
        translated_text = translator.translate(reaction.message.content)
        
        # Create embed with translation
        embed = discord.Embed(
            description=translated_text,
            color=discord.Color.green()
        )
        embed.set_author(
            name=f"Translation for {user.display_name}",
            icon_url=user.avatar.url if user.avatar else None
        )
        embed.set_footer(text=f"Translated to {target_lang.upper()} | Original by {reaction.message.author.display_name}")
        
        # Send as a reply to the original message
        await reaction.message.reply(embed=embed, mention_author=False)
        
    except Exception as e:
        print(f'Flag translation error: {e}')
        try:
            await reaction.message.channel.send(f'❌ Translation failed: {str(e)}', delete_after=5)
        except:
            pass


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
