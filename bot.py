import discord
from discord.ext import commands
from discord import ui
import json
import os
import re
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Storage for channel language mappings
# Use /app/data for Railway persistent volume, fallback to current dir for local dev
DATA_DIR = '/app/data' if os.path.exists('/app/data') else os.path.dirname(__file__)
LANGUAGE_CONFIG_FILE = os.path.join(DATA_DIR, 'language_config.json')
REGISTRATION_CONFIG_FILE = os.path.join(DATA_DIR, 'registration_config.json')

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


def load_registration_config():
    """Load registration configuration from JSON file."""
    if os.path.exists(REGISTRATION_CONFIG_FILE):
        with open(REGISTRATION_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'holding_room_channel_id': None,  # Channel ID where new members appear
        'leadership_approval_channel_id': None,  # Channel for approvals
        'member_log_channel_id': None,  # Channel for logging all registrations
        'roles_channel_id': None,  # Channel for role selection (all members)
        'leadership_roles_channel_id': None,  # Channel for R4/R5 role selection
        'registered_members': {},  # member_id: {ign, gang_code, rank}
        'pending_approvals': {},  # member_id: {ign, gang_code, rank, message_id}
        'welcome_messages': {},  # member_id: {channel_id, message_id}
        'approval_required': {  # Which ranks require approval
            'R1': False,
            'R2': False,
            'R3': False,
            'R4': True,
            'R5': True
        }
    }


def save_registration_config(config):
    """Save registration configuration to JSON file."""
    with open(REGISTRATION_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


# Load config on startup
language_config = load_language_config()
registration_config = load_registration_config()


async def send_member_log(guild, member, ign, gang_code, rank, status='Registered'):
    """Send registration info to member log channel."""
    log_channel_id = registration_config.get('member_log_channel_id')
    if not log_channel_id:
        return
    
    log_channel = guild.get_channel(int(log_channel_id))
    if not log_channel:
        return
    
    try:
        embed = discord.Embed(
            title='Member Registration',
            color=discord.Color.blue() if status == 'Registered' else discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name='Member', value=member.mention, inline=True)
        embed.add_field(name='User', value=f'{member.name}#{member.discriminator}', inline=True)
        embed.add_field(name='Status', value=status, inline=True)
        embed.add_field(name='In Game Name', value=ign, inline=True)
        embed.add_field(name='Gang Code', value=gang_code, inline=True)
        embed.add_field(name='Rank', value=rank, inline=True)
        embed.add_field(name='Nickname', value=f'[{gang_code}][{rank}]:{ign}', inline=False)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.set_footer(text=f'User ID: {member.id}')
        
        await log_channel.send(embed=embed)
    except Exception as e:
        print(f'Error sending member log: {e}')


async def delete_welcome_message(guild, member_id):
    """Delete the welcome message for a member after they register."""
    member_id_str = str(member_id)
    if member_id_str not in registration_config['welcome_messages']:
        return
    
    welcome_data = registration_config['welcome_messages'][member_id_str]
    channel = guild.get_channel(int(welcome_data['channel_id']))
    
    if channel:
        try:
            message = await channel.fetch_message(int(welcome_data['message_id']))
            await message.delete()
        except discord.NotFound:
            pass  # Message already deleted
        except Exception as e:
            print(f'Error deleting welcome message: {e}')
    
    # Remove from tracking
    del registration_config['welcome_messages'][member_id_str]
    save_registration_config(registration_config)


async def send_role_channel_redirects(guild, member, rank):
    """Send member to appropriate role channels after registration/approval."""
    roles_channel_id = registration_config.get('roles_channel_id')
    leadership_roles_channel_id = registration_config.get('leadership_roles_channel_id')
    
    # Send DM
    try:
        dm_message = '✅ Registration complete! Please visit the following channels to complete your setup:\n'
        
        if roles_channel_id:
            roles_channel = guild.get_channel(int(roles_channel_id))
            if roles_channel:
                dm_message += f'• {roles_channel.mention} - Select your language and preferences\n'
        
        if rank in ['R4', 'R5'] and leadership_roles_channel_id:
            leadership_channel = guild.get_channel(int(leadership_roles_channel_id))
            if leadership_channel:
                dm_message += f'• {leadership_channel.mention} - Select your leadership roles\n'
        
        await member.send(dm_message)
    except discord.Forbidden:
        print(f'Cannot send DM to {member.name}')
    except Exception as e:
        print(f'Error sending DM: {e}')
    
    # Send mention in #roles channel (auto-delete after 5 minutes)
    if roles_channel_id:
        roles_channel = guild.get_channel(int(roles_channel_id))
        if roles_channel:
            try:
                await roles_channel.send(
                    f'{member.mention} Welcome! Please select your roles.',
                    delete_after=300  # 5 minutes
                )
            except Exception as e:
                print(f'Error sending roles channel message: {e}')
    
    # Send mention in #r5r4-roles channel if R4/R5 (auto-delete after 5 minutes)
    if rank in ['R4', 'R5'] and leadership_roles_channel_id:
        leadership_channel = guild.get_channel(int(leadership_roles_channel_id))
        if leadership_channel:
            try:
                await leadership_channel.send(
                    f'{member.mention} Welcome to leadership! Please select your leadership roles.',
                    delete_after=300  # 5 minutes
                )
            except Exception as e:
                print(f'Error sending leadership roles channel message: {e}')

# Ensure structure exists
if 'groups' not in language_config:
    language_config['groups'] = {}
if 'flag_enabled_channels' not in language_config:
    language_config['flag_enabled_channels'] = []
if 'holding_room_channel_id' not in registration_config:
    registration_config['holding_room_channel_id'] = None
if 'leadership_approval_channel_id' not in registration_config:
    registration_config['leadership_approval_channel_id'] = None
if 'member_log_channel_id' not in registration_config:
    registration_config['member_log_channel_id'] = None
if 'roles_channel_id' not in registration_config:
    registration_config['roles_channel_id'] = None
if 'leadership_roles_channel_id' not in registration_config:
    registration_config['leadership_roles_channel_id'] = None
if 'registered_members' not in registration_config:
    registration_config['registered_members'] = {}
if 'pending_approvals' not in registration_config:
    registration_config['pending_approvals'] = {}
if 'welcome_messages' not in registration_config:
    registration_config['welcome_messages'] = {}
if 'approval_required' not in registration_config:
    registration_config['approval_required'] = {
        'R1': False,
        'R2': False,
        'R3': False,
        'R4': True,
        'R5': True
    }


# Registration Modal Class
class RegistrationModal(ui.Modal, title='Server Registration'):
    ign = ui.TextInput(
        label='In Game Name',
        placeholder='Enter your in-game name',
        required=True,
        max_length=50
    )
    
    gang_code = ui.TextInput(
        label='Gang Code (3 characters)',
        placeholder='e.g., ABC',
        required=True,
        min_length=3,
        max_length=3
    )
    
    rank = ui.TextInput(
        label='Rank (R1, R2, R3, R4, or R5)',
        placeholder='e.g., R3',
        required=True,
        max_length=2
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        # Validate rank
        rank_input = self.rank.value.upper().strip()
        if not re.match(r'^R[1-5]$', rank_input):
            await interaction.response.send_message(
                '❌ Invalid rank! Please use R1, R2, R3, R4, or R5.',
                ephemeral=True
            )
            return
        
        # Validate gang code (3 uppercase letters)
        gang_code_input = self.gang_code.value.upper().strip()
        if not re.match(r'^[A-Z]{3}$', gang_code_input):
            await interaction.response.send_message(
                '❌ Gang code must be exactly 3 letters!',
                ephemeral=True
            )
            return
        
        ign_input = self.ign.value.strip()
        
        # Process registration
        guild = interaction.guild
        member = interaction.user
        member_id_str = str(member.id)
        
        # Check if already registered
        is_reregistration = member_id_str in registration_config['registered_members']
        was_pending = member_id_str in registration_config['pending_approvals']
        
        # If re-registering, remove old data and roles first
        if is_reregistration:
            # Get old data for comparison
            old_data = registration_config['registered_members'][member_id_str]
            old_rank = old_data['rank']
            
            # Remove old rank roles
            if old_rank in ['R1', 'R2', 'R3']:
                pirate_role = discord.utils.get(guild.roles, name='Pirate')
                if pirate_role and pirate_role in member.roles:
                    await member.remove_roles(pirate_role)
            elif old_rank == 'R4':
                r4_role = discord.utils.get(guild.roles, name='R4')
                if r4_role and r4_role in member.roles:
                    await member.remove_roles(r4_role)
            elif old_rank == 'R5':
                r5_role = discord.utils.get(guild.roles, name='R5')
                if r5_role and r5_role in member.roles:
                    await member.remove_roles(r5_role)
            
            # Remove old gang role if gang code changed
            old_gang = old_data['gang_code']
            if old_gang != gang_code_input:
                old_gang_role = discord.utils.get(guild.roles, name=old_gang)
                if old_gang_role and old_gang_role in member.roles:
                    await member.remove_roles(old_gang_role)
            
            # Remove old registration
            del registration_config['registered_members'][member_id_str]
            save_registration_config(registration_config)
        
        if was_pending:
            del registration_config['pending_approvals'][member_id_str]
            save_registration_config(registration_config)
        
        try:
            # Set nickname format: [GangCode][Rank]:InGameName
            new_nickname = f"[{gang_code_input}][{rank_input}]:{ign_input}"
            await member.edit(nick=new_nickname)
            
            # Get or create gang code role (case-insensitive search to prevent duplicates)
            gang_role = None
            for role in guild.roles:
                if role.name.upper() == gang_code_input:
                    gang_role = role
                    break
            
            if not gang_role:
                gang_role = await guild.create_role(
                    name=gang_code_input,
                    mentionable=True,
                    hoist=True  # Display role members separately from online members
                )
            
            # Remove DaviesLocker role if they have it
            davies_locker_role = discord.utils.get(guild.roles, name='DaviesLocker')
            if davies_locker_role and davies_locker_role in member.roles:
                await member.remove_roles(davies_locker_role)
            
            # Check if rank requires approval
            requires_approval = registration_config['approval_required'].get(rank_input, False)
            
            # Determine rank roles
            roles_to_add = [gang_role]
            
            # If no approval required, add rank role and GenUser immediately
            if not requires_approval:
                # Everyone gets GenUser role
                genuser_role = discord.utils.get(guild.roles, name='GenUser')
                if not genuser_role:
                    genuser_role = await guild.create_role(name='GenUser', mentionable=True)
                roles_to_add.append(genuser_role)
                # R1-R3 get Pirate role
                if rank_input in ['R1', 'R2', 'R3']:
                    pirate_role = discord.utils.get(guild.roles, name='Pirate')
                    if not pirate_role:
                        pirate_role = await guild.create_role(name='Pirate', mentionable=True)
                    roles_to_add.append(pirate_role)
                # R4 gets R4 role
                elif rank_input == 'R4':
                    r4_role = discord.utils.get(guild.roles, name='R4')
                    if not r4_role:
                        r4_role = await guild.create_role(name='R4', mentionable=True)
                    roles_to_add.append(r4_role)
                # R5 gets R5 role
                elif rank_input == 'R5':
                    r5_role = discord.utils.get(guild.roles, name='R5')
                    if not r5_role:
                        r5_role = await guild.create_role(name='R5', mentionable=True)
                    roles_to_add.append(r5_role)
                
                # Add all roles
                await member.add_roles(*roles_to_add)
                
                # Save registration data
                registration_config['registered_members'][str(member.id)] = {
                    'ign': ign_input,
                    'gang_code': gang_code_input,
                    'rank': rank_input
                }
                save_registration_config(registration_config)
                
                # Send to member log
                await send_member_log(guild, member, ign_input, gang_code_input, rank_input, 'Registered')
                
                # Delete welcome message (only if it exists)
                if member_id_str in registration_config['welcome_messages']:
                    await delete_welcome_message(guild, member.id)
                
                # Send role channel redirects
                await send_role_channel_redirects(guild, member, rank_input)
                
                await interaction.response.send_message(
                    f'\u2705 Registration complete!\n'
                    f'**Nickname:** {new_nickname}\n'
                    f'**Roles:** {", ".join([r.name for r in roles_to_add])}\n'
                    f'Check your DMs for next steps!',
                    ephemeral=True
                )
                
            # If approval required, send to approval channel
            else:
                # Only add gang role (no GenUser until approved)
                await member.add_roles(*roles_to_add)
                
                # Save to pending approvals
                registration_config['pending_approvals'][str(member.id)] = {
                    'ign': ign_input,
                    'gang_code': gang_code_input,
                    'rank': rank_input
                }
                save_registration_config(registration_config)
                
                # Send to member log
                await send_member_log(guild, member, ign_input, gang_code_input, rank_input, 'Pending Approval')
                
                # Delete welcome message (only if it exists)
                if member_id_str in registration_config['welcome_messages']:
                    await delete_welcome_message(guild, member.id)
                
                # Send approval request to approval channel
                approval_channel_id = registration_config.get('leadership_approval_channel_id')
                if approval_channel_id:
                    approval_channel = guild.get_channel(int(approval_channel_id))
                    if approval_channel:
                        approval_embed = discord.Embed(
                            title='Rank Approval Request',
                            description=f'{member.mention} has requested a rank that requires approval.',
                            color=discord.Color.orange()
                        )
                        approval_embed.add_field(name='In Game Name', value=ign_input, inline=True)
                        approval_embed.add_field(name='Gang Code', value=gang_code_input, inline=True)
                        approval_embed.add_field(name='Requested Rank', value=rank_input, inline=True)
                        approval_embed.add_field(name='Nickname', value=new_nickname, inline=False)
                        approval_embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
                        approval_embed.set_footer(text=f'User ID: {member.id}')
                        
                        view = LeadershipApprovalView(str(member.id))
                        await approval_channel.send(embed=approval_embed, view=view)
                
                await interaction.response.send_message(
                    f'\u2705 Registration submitted!\n'
                    f'**Nickname:** {new_nickname}\n'
                    f'**Roles:** {", ".join([r.name for r in roles_to_add])}\n\n'
                    f'\u23f3 Your **{rank_input}** rank requires approval. You will be notified once reviewed.',
                    ephemeral=True
                )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                '❌ I don\'t have permission to set your nickname or assign roles. Please contact an admin.',
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f'❌ An error occurred during registration: {str(e)}',
                ephemeral=True
            )


# Registration Button View
class RegistrationView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
    
    @ui.button(label='Register', style=discord.ButtonStyle.primary, custom_id='register_button')
    async def register_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(RegistrationModal())


# Leadership Approval View
class LeadershipApprovalView(ui.View):
    def __init__(self, member_id: str):
        super().__init__(timeout=None)
        self.member_id = member_id
    
    @ui.button(label='Approve', style=discord.ButtonStyle.success, custom_id='approve_leadership')
    async def approve_button(self, interaction: discord.Interaction, button: ui.Button):
        # Check if user has LeadershipApproval role
        approval_role = discord.utils.get(interaction.guild.roles, name='LeadershipApproval')
        if not approval_role or approval_role not in interaction.user.roles:
            await interaction.response.send_message(
                '❌ You need the LeadershipApproval role to approve members.',
                ephemeral=True
            )
            return
        
        # Get pending approval data
        if self.member_id not in registration_config['pending_approvals']:
            await interaction.response.send_message(
                '❌ This approval request is no longer valid.',
                ephemeral=True
            )
            return
        
        pending_data = registration_config['pending_approvals'][self.member_id]
        member = interaction.guild.get_member(int(self.member_id))
        
        if not member:
            await interaction.response.send_message(
                '❌ Member not found in server.',
                ephemeral=True
            )
            return
        
        try:
            # Add the appropriate rank role
            rank = pending_data['rank']
            roles_to_add = []
            
            # R1-R3 get Pirate role
            if rank in ['R1', 'R2', 'R3']:
                rank_role = discord.utils.get(interaction.guild.roles, name='Pirate')
                if not rank_role:
                    rank_role = await interaction.guild.create_role(name='Pirate', mentionable=True)
                roles_to_add.append(rank_role)
            # R4 gets R4 role
            elif rank == 'R4':
                rank_role = discord.utils.get(interaction.guild.roles, name='R4')
                if not rank_role:
                    rank_role = await interaction.guild.create_role(name='R4', mentionable=True)
                roles_to_add.append(rank_role)
            # R5 gets R5 role
            elif rank == 'R5':
                rank_role = discord.utils.get(interaction.guild.roles, name='R5')
                if not rank_role:
                    rank_role = await interaction.guild.create_role(name='R5', mentionable=True)
                roles_to_add.append(rank_role)
            else:
                await interaction.response.send_message('\u274c Invalid rank in approval.', ephemeral=True)
                return
            
            # Add GenUser role upon approval
            genuser_role = discord.utils.get(interaction.guild.roles, name='GenUser')
            if not genuser_role:
                genuser_role = await interaction.guild.create_role(name='GenUser', mentionable=True)
            roles_to_add.append(genuser_role)
            
            await member.add_roles(*roles_to_add)
            
            # Move to registered members
            registration_config['registered_members'][self.member_id] = {
                'ign': pending_data['ign'],
                'gang_code': pending_data['gang_code'],
                'rank': pending_data['rank']
            }
            
            # Remove from pending
            del registration_config['pending_approvals'][self.member_id]
            save_registration_config(registration_config)
            
            # Send to member log
            await send_member_log(
                interaction.guild,
                member,
                pending_data['ign'],
                pending_data['gang_code'],
                pending_data['rank'],
                f'Approved by {interaction.user.name}'
            )
            
            # Send role channel redirects
            await send_role_channel_redirects(interaction.guild, member, rank)
            
            # Update the message
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.green()
            embed.add_field(name='Status', value=f'\u2705 Approved by {interaction.user.mention}', inline=False)
            
            await interaction.message.edit(embed=embed, view=None)
            await interaction.response.send_message(f'\u2705 {member.mention} approved for {rank}!', ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f'❌ Error approving member: {str(e)}', ephemeral=True)
    
    @ui.button(label='Deny', style=discord.ButtonStyle.danger, custom_id='deny_leadership')
    async def deny_button(self, interaction: discord.Interaction, button: ui.Button):
        # Check if user has LeadershipApproval role
        approval_role = discord.utils.get(interaction.guild.roles, name='LeadershipApproval')
        if not approval_role or approval_role not in interaction.user.roles:
            await interaction.response.send_message(
                '❌ You need the LeadershipApproval role to deny members.',
                ephemeral=True
            )
            return
        
        # Get pending approval data
        if self.member_id not in registration_config['pending_approvals']:
            await interaction.response.send_message(
                '❌ This approval request is no longer valid.',
                ephemeral=True
            )
            return
        
        pending_data = registration_config['pending_approvals'][self.member_id]
        member = interaction.guild.get_member(int(self.member_id))
        
        # Remove from pending
        del registration_config['pending_approvals'][self.member_id]
        save_registration_config(registration_config)
        
        # Update the message
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(name='Status', value=f'❌ Denied by {interaction.user.mention}', inline=False)
        
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(f'❌ Leadership request denied.', ephemeral=True)
        
        # Notify the member
        if member:
            try:
                await member.send(f'❌ Your leadership rank ({pending_data["rank"]}) request was denied. Please contact an administrator for more information.')
            except:
                pass


@bot.event
async def on_ready():
    """Event handler for when bot is ready."""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guild(s)')
    
    # Add persistent view for registration button
    bot.add_view(RegistrationView())


@bot.event
async def on_member_remove(member: discord.Member):
    """Event handler for when a member leaves the server."""
    member_id_str = str(member.id)
    
    # Clean up registration data
    if member_id_str in registration_config['registered_members']:
        del registration_config['registered_members'][member_id_str]
    
    if member_id_str in registration_config['pending_approvals']:
        del registration_config['pending_approvals'][member_id_str]
    
    if member_id_str in registration_config['welcome_messages']:
        del registration_config['welcome_messages'][member_id_str]
    
    save_registration_config(registration_config)
    print(f'Cleaned up registration data for {member.name} (left server)')


@bot.event
async def on_member_join(member: discord.Member):
    """Event handler for when a member joins the server."""
    holding_room_id = registration_config.get('holding_room_channel_id')
    
    if not holding_room_id:
        print(f'New member {member.name} joined, but holding room is not configured.')
        return
    
    holding_room = member.guild.get_channel(int(holding_room_id))
    if not holding_room:
        print(f'Holding room channel ID {holding_room_id} not found.')
        return
    
    try:
        embed = discord.Embed(
            title='Welcome to the Server!',
            description=f'Hello {member.mention}! Please register to gain access to the server.',
            color=discord.Color.green()
        )
        embed.add_field(
            name='Registration',
            value='Click the button below to register. You will be asked for:\n'
                  '• **In Game Name**\n'
                  '• **Gang Code** (3 characters)\n'
                  '• **Rank** (R1-R5)',
            inline=False
        )
        
        view = RegistrationView()
        welcome_msg = await holding_room.send(embed=embed, view=view)
        
        # Store the welcome message ID so we can delete it later
        registration_config['welcome_messages'][str(member.id)] = {
            'channel_id': str(holding_room.id),
            'message_id': str(welcome_msg.id)
        }
        save_registration_config(registration_config)
        
    except discord.Forbidden:
        print(f'Cannot send message to holding room - missing permissions')
    except Exception as e:
        print(f'Error sending welcome message: {e}')


@bot.command(name='setholdingroom', help='Set the holding room channel for new members')
@commands.has_permissions(administrator=True)
async def set_holding_room(ctx):
    """Set the current channel as the holding room for new members."""
    registration_config['holding_room_channel_id'] = str(ctx.channel.id)
    save_registration_config(registration_config)
    await ctx.send(f'\u2705 Holding room set to {ctx.channel.mention}. New members will receive registration messages here.')


@bot.command(name='setleadershipchannel', help='Set the leadership approval channel')
@commands.has_permissions(administrator=True)
async def set_leadership_channel(ctx):
    """Set the current channel as the leadership approval channel."""
    registration_config['leadership_approval_channel_id'] = str(ctx.channel.id)
    save_registration_config(registration_config)
    await ctx.send(f'\u2705 Approval channel set to {ctx.channel.mention}. Registration requests requiring approval will be sent here.')


@bot.command(name='setmemberlog', help='Set the member log channel')
@commands.has_permissions(administrator=True)
async def set_member_log(ctx):
    """Set the current channel as the member log channel."""
    registration_config['member_log_channel_id'] = str(ctx.channel.id)
    save_registration_config(registration_config)
    await ctx.send(f'\u2705 Member log channel set to {ctx.channel.mention}. All registration profiles will be logged here.')


@bot.command(name='setroleschannel', help='Set the general roles channel (for all members)')
@commands.has_permissions(administrator=True)
async def set_roles_channel(ctx):
    """Set the current channel as the general roles channel."""
    registration_config['roles_channel_id'] = str(ctx.channel.id)
    save_registration_config(registration_config)
    await ctx.send(f'\u2705 General roles channel set to {ctx.channel.mention}. All registered members will be directed here.')


@bot.command(name='setleadershiproleschannel', help='Set the leadership roles channel (for R4/R5 only)')
@commands.has_permissions(administrator=True)
async def set_leadership_roles_channel(ctx):
    """Set the current channel as the leadership roles channel."""
    registration_config['leadership_roles_channel_id'] = str(ctx.channel.id)
    save_registration_config(registration_config)
    await ctx.send(f'\u2705 Leadership roles channel set to {ctx.channel.mention}. R4/R5 members will be directed here.')


@bot.command(name='requireapproval', help='Set which ranks require approval. Usage: !requireapproval <rank> <on|off>')
@commands.has_permissions(administrator=True)
async def require_approval(ctx, rank: str, setting: str):
    """Toggle approval requirement for a specific rank."""
    rank_upper = rank.upper()
    setting_lower = setting.lower()
    
    if rank_upper not in ['R1', 'R2', 'R3', 'R4', 'R5']:
        await ctx.send('\u274c Invalid rank! Use R1, R2, R3, R4, or R5.')
        return
    
    if setting_lower not in ['on', 'off']:
        await ctx.send('\u274c Invalid setting! Use "on" or "off".')
        return
    
    registration_config['approval_required'][rank_upper] = (setting_lower == 'on')
    save_registration_config(registration_config)
    
    status = 'enabled' if setting_lower == 'on' else 'disabled'
    await ctx.send(f'\u2705 Approval requirement for **{rank_upper}** has been **{status}**.')


@bot.command(name='approvalstatus', help='View current approval requirements for all ranks')
@commands.has_permissions(administrator=True)
async def approval_status(ctx):
    """Display current approval requirements."""
    embed = discord.Embed(
        title='Approval Requirements',
        description='Shows which ranks require approval before full registration',
        color=discord.Color.blue()
    )
    
    for rank in ['R1', 'R2', 'R3', 'R4', 'R5']:
        required = registration_config['approval_required'].get(rank, False)
        status = '\u2705 Required' if required else '\u274c Not Required'
        embed.add_field(name=rank, value=status, inline=True)
    
    await ctx.send(embed=embed)


@bot.command(name='reregister', help='Update your profile (IGN, Gang, or Rank)')
async def reregister(ctx):
    """Allow users to re-register to update their profile."""
    member = ctx.author
    member_id_str = str(member.id)
    
    # Check if they're registered
    if member_id_str not in registration_config['registered_members']:
        await ctx.send('❌ You need to be registered first! Please complete registration in the holding room.', delete_after=10)
        return
    
    try:
        # Get their current info
        current_reg = registration_config['registered_members'][member_id_str]
        
        # Send them a registration button right here
        embed = discord.Embed(
            title='Update Your Profile',
            description='Click the button below to update your profile.',
            color=discord.Color.blue()
        )
        embed.add_field(name='Current Profile', 
                       value=f'**IGN:** {current_reg["ign"]}\n'
                             f'**Gang:** {current_reg["gang_code"]}\n'
                             f'**Rank:** {current_reg["rank"]}',
                       inline=False)
        embed.add_field(name='Instructions',
                       value='Enter your NEW information in the form. This will replace your current profile.',
                       inline=False)
        
        view = RegistrationView()
        update_msg = await ctx.send(embed=embed, view=view)
        
        # Store the message so we can delete it after re-registration (just like new registrations)
        registration_config['welcome_messages'][member_id_str] = {
            'channel_id': str(ctx.channel.id),
            'message_id': str(update_msg.id)
        }
        save_registration_config(registration_config)
        
        # Delete the user's command message
        try:
            await ctx.message.delete()
        except:
            pass
            
    except Exception as e:
        await ctx.send(f'❌ Error: {str(e)}', delete_after=10)


@bot.command(name='updateprofile', help='Update a member\'s profile (Admin only). Usage: !updateprofile <user_id>')
@commands.has_permissions(administrator=True)
async def update_profile(ctx, member: discord.Member):
    """Allow admins to manually trigger re-registration for a member."""
    member_id_str = str(member.id)
    
    # Check if registered
    if member_id_str not in registration_config['registered_members']:
        await ctx.send(f'❌ {member.mention} is not registered yet.')
        return
    
    # Clear their current registration so they can re-register
    del registration_config['registered_members'][member_id_str]
    save_registration_config(registration_config)
    
    # Send them a DM with re-registration instructions
    try:
        await member.send(
            '🔄 Your profile has been reset by an administrator.\n'
            'Please return to the holding room to re-register with your updated information.'
        )
        await ctx.send(f'✅ {member.mention}\'s registration has been cleared. They can now re-register.')
    except discord.Forbidden:
        await ctx.send(f'✅ {member.mention}\'s registration has been cleared, but I couldn\'t DM them. Please let them know to re-register.')


@bot.command(name='fixnicknames', help='Update nicknames for all members based on their roles')
@commands.has_permissions(administrator=True)
async def fix_nicknames(ctx):
    """Fix nicknames for all members based on their roles."""
    await ctx.send('⏳ Processing nicknames...')
    
    fixed_count = 0
    error_count = 0
    
    # Roles we want to display in nicknames
    gang_roles = []  # 3-letter gang codes
    rank_roles = ['R4', 'R5', 'Pirate']  # Rank roles
    
    for member in ctx.guild.members:
        if member.bot:
            continue
        
        # Find gang code and rank from roles
        member_gang = None
        member_rank = None
        
        for role in member.roles:
            # Check if it's a gang code (3 uppercase letters)
            if re.match(r'^[A-Z]{3}$', role.name):
                member_gang = role.name
            # Check for rank roles
            elif role.name in ['R4', 'R5']:
                member_rank = role.name
            elif role.name == 'Pirate':
                # Try to determine R1-R3 from other info or default to R1
                if not member_rank or member_rank not in ['R1', 'R2', 'R3']:
                    member_rank = 'R1'  # Default for Pirates
        
        # If we found both gang and rank, update nickname
        if member_gang and member_rank:
            # Try to extract IGN from current nickname or use username
            current_nick = member.nick if member.nick else member.name
            
            # Try to parse existing format [XXX][RX]:IGN
            match = re.match(r'\[[A-Z]{3}\]\[R[1-5]\]:(.+)', current_nick)
            if match:
                ign = match.group(1)
            else:
                # Check if registered
                if str(member.id) in registration_config['registered_members']:
                    ign = registration_config['registered_members'][str(member.id)]['ign']
                else:
                    ign = current_nick  # Use current nickname as IGN
            
            new_nickname = f"[{member_gang}][{member_rank}]:{ign}"
            
            try:
                if member.nick != new_nickname:
                    await member.edit(nick=new_nickname)
                    fixed_count += 1
            except discord.Forbidden:
                error_count += 1
            except Exception as e:
                print(f'Error updating {member.name}: {e}')
                error_count += 1
    
    await ctx.send(f'✅ Nickname fix complete!\n'
                   f'• **Updated:** {fixed_count} members\n'
                   f'• **Errors:** {error_count} members')


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
async def on_member_update(before: discord.Member, after: discord.Member):
    """Prevent non-admin users from changing their nicknames."""
    # Only care about nickname changes
    if before.nick == after.nick:
        return
    
    # Allow admins to change nicknames
    if after.guild_permissions.administrator:
        return
    
    # Check if member is registered
    member_id = str(after.id)
    if member_id not in registration_config['registered_members']:
        return  # Not registered, allow change
    
    # Get their registration data
    reg_data = registration_config['registered_members'][member_id]
    expected_nickname = f"[{reg_data['gang_code']}][{reg_data['rank']}]:{reg_data['ign']}"
    
    # If they changed their nickname, revert it
    if after.nick != expected_nickname:
        try:
            await after.edit(nick=expected_nickname)
            # Try to DM the user
            try:
                await after.send(
                    '❌ You cannot change your nickname. '
                    'Please contact an administrator if you need to update your registration.'
                )
            except:
                pass  # User has DMs disabled
        except discord.Forbidden:
            print(f'Cannot revert nickname for {after.name} - missing permissions')
        except Exception as e:
            print(f'Error reverting nickname: {e}')


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
