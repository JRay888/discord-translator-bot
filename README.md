# Discord Translator Bot

A Discord bot that automatically translates messages to different languages based on channel settings. Perfect for multilingual Discord servers where different channels are dedicated to specific languages.

## New Features

### Translation Features
- 🌍 **Multi-language support** - Supports 100+ languages via Google Translate
- 👥 **Translation Groups** - Group multiple channels together for automatic cross-translation
- 🚩 **Flag Reactions** - React with flag emojis to translate messages on-demand
- 🤖 **Automatic translation** - Messages in grouped channels are automatically translated
- 💬 **Preserved context** - Shows original author and source/target languages

### Member Registration System
- 📝 **Interactive Registration** - New members register with In-Game Name, Gang Code, and Rank
- 🏷️ **Automatic Nickname Formatting** - Sets nicknames to `[GangCode][Rank]:IGN` format
- 👥 **Role Management** - Automatically assigns gang roles, rank roles (Pirate, R4, R5), and GenUser
- 🔒 **Nickname Protection** - Prevents non-admins from changing their nicknames
- ✅ **Configurable Approvals** - Any rank (R1-R5) can require approval before full access
- 📝 **Member Logging** - All registrations logged to dedicated channel with full details
- 🚪 **Auto Role Removal** - Removes DaviesLocker role upon successful registration
- 🧹 **Auto Cleanup** - Welcome messages deleted after registration
- 🔐 **Permission-based** - Admin commands for managing registration and fixing nicknames

## Commands

### Registration Setup Commands

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `!setholdingroom` | Set current channel as the holding room for new members | Administrator |
| `!setleadershipchannel` | Set current channel for approval requests | Administrator |
| `!setmemberlog` | Set current channel for member registration logs | Administrator |
| `!setroleschannel` | Set general roles channel (all members redirected here) | Administrator |
| `!setleadershiproleschannel` | Set leadership roles channel (R4/R5 only) | Administrator |
| `!requireapproval <rank> <on\|off>` | Toggle approval requirement for a rank (e.g., `!requireapproval R3 on`) | Administrator |
| `!approvalstatus` | View which ranks require approval | Administrator |

### Member Management Commands

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `!reregister` | Update your own profile (IGN, Gang, or Rank) | None |
| `!updateprofile @user` | Clear a member's registration so they can re-register | Administrator |
| `!syncmember @user` | Sync registration data based on member's current roles | Administrator |
| `!setmember @user <IGN> <gang> <rank>` | Directly set a member's profile and update roles (e.g., `!setmember @user PlayerName GNB R3`) | Administrator |
| `!fixnicknames` | Update all member nicknames and registration data based on their roles | Administrator |

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

### Telegram Bridge Commands

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `!linktelegram <tg_id> <discord_ch_id> <lang>` | Link a Telegram group to a Discord channel (e.g., `!linktelegram -1001234567890 1234567890123456789 es`) | Administrator |
| `!unlinktelegram <tg_id>` | Unlink a Telegram group from Discord | Administrator |
| `!listbridges` | List all active Telegram-Discord bridges | Administrator |
| `!telegramchats` | List all Telegram chats the bot can see (to get their IDs) | Administrator |

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

### 7. Configure Registration System (Optional)

If you want to use the member registration system:

#### Required Setup:
1. Create a **holding room channel** (e.g., `#holding-room`)
2. In the holding room, run: `!setholdingroom`

#### Optional Setup:
3. Create a **member log channel** (e.g., `#member-log`)
   - In that channel, run: `!setmemberlog`
   - All registrations will be logged here with full details

4. Create an **approval channel** (e.g., `#leadership-approvals`)
   - In that channel, run: `!setleadershipchannel`
   - Create a `LeadershipApproval` role and assign it to approvers

5. **Configure approval requirements** (default: R4 and R5 require approval):
   ```
   !approvalstatus              # Check current settings
   !requireapproval R1 on       # Require approval for R1
   !requireapproval R4 off      # Auto-approve R4 (no approval needed)
   ```

New members will now automatically receive a registration prompt when they join!

## Command Examples

### Registration Setup Commands

```bash
# Set up holding room for new members
# Run this in the channel where new members will register
!setholdingroom

# Set up leadership approval channel
# Run this in the channel where R4/R5 approval requests go
!setleadershipchannel

# Set up member log channel
# Run this in the channel where all registrations are logged
!setmemberlog

# Set up general roles channel (for all members)
!setroleschannel

# Set up leadership roles channel (for R4/R5 only)
!setleadershiproleschannel

# Configure which ranks require approval
!requireapproval R4 on      # R4 now requires approval
!requireapproval R1 off     # R1 auto-approved
!approvalstatus             # Check current approval settings
```

### Member Management Commands

```bash
# Let a member update their own profile
!reregister
# This opens a registration form for the user

# Force a member to re-register (clears their data)
!updateprofile @username

# Sync a member's registration based on their current roles
# Use this AFTER manually changing someone's roles
!syncmember @username
# Example: If you manually gave them GNB role and R4 role,
# this will update their registration data and nickname

# Directly set a member's complete profile
# Format: !setmember @user IGN GANG RANK
!setmember @username "Charles Vane" GNB R3
!setmember @username JohnDoe ABC R5
!setmember @username "Player Name" XYZ R1
# Note: Use quotes if IGN has spaces
# This updates roles, nickname, and registration data all at once

# Bulk update all members based on their current roles
!fixnicknames
# Scans all members, updates nicknames and registration data
```

### Translation Groups

```bash
# Create a group for general chat
!creategroup general

# In your #english channel, run:
!addchannel general en

# In your #spanish channel, run:
!addchannel general es

# In your #french channel, run:
!addchannel general fr

# Now messages in any of these channels will automatically 
# appear translated in the other channels!

# View all groups and their channels
!listgroups

# Remove current channel from its group
!removechannel

# Delete an entire group
!deletegroup general
```

### Flag Reactions

```bash
# Enable flag reactions in current channel
!enableflags
# Users can now react with flag emojis (🇪🇸, 🇫🇷, 🇯🇵, etc.) 
# to get instant translations

# Disable flag reactions
!disableflags
```

### Telegram Bridge

```bash
# First, get Telegram chat IDs by checking what the bot can see
!telegramchats
# Send a message in your Telegram group, then run this to see its ID

# Link a Telegram group to a Discord channel
# Format: !linktelegram <telegram_group_id> <discord_channel_id> <language>
!linktelegram -1001234567890 1234567890123456789 es

# List all active bridges
!listbridges

# Unlink a Telegram group
!unlinktelegram -1001234567890
```

### General Information Commands

```bash
# View current channel's translation settings
!channelinfo

# List all available language codes
!listlangs
```

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

## Registration System

### How It Works

1. **Member Joins** → Receives welcome message in holding room with registration button
2. **Click Register** → Modal form appears asking for:
   - In Game Name
   - Gang Code (3 letters)
   - Rank (R1-R5)
3. **Validation** → Bot validates inputs and sets nickname to `[GangCode][Rank]:IGN`
4. **Role Assignment**:
   - **Gang Role** - Automatically created/assigned based on 3-letter code
   - **If Approval NOT Required**:
     - R1-R3 → Pirate role + GenUser role
     - R4 → R4 role + GenUser role
     - R5 → R5 role + GenUser role
   - **If Approval Required**:
     - Only Gang role assigned (no GenUser or rank role yet)
     - Approval request sent to approval channel
     - Users with `LeadershipApproval` role can approve/deny
     - Upon approval → Rank role + GenUser role added
5. **Cleanup** → Welcome message automatically deleted
6. **Logging** → All registrations logged to member log channel

### Role Hierarchy

- **DaviesLocker** - Removed upon registration
- **Gang Roles** (e.g., ABC, XYZ) - Created automatically, assigned to all members of that gang
- **Rank Roles**:
  - **Pirate** - R1, R2, R3 ranks
  - **R4** - R4 rank
  - **R5** - R5 rank  
- **GenUser** - Only assigned after registration is complete (or approved)

### Managing Approvals

```bash
# View current approval settings
!approvalstatus

# Require approval for R1 rank
!requireapproval R1 on

# Turn off approval requirement for R5 (auto-approve)
!requireapproval R5 off

# Turn off all approvals (auto-approve everyone)
!requireapproval R1 off
!requireapproval R2 off
!requireapproval R3 off
!requireapproval R4 off
!requireapproval R5 off
```

### Managing Members

#### Bulk Update All Members
For members already in the server who didn't go through registration:

```bash
!fixnicknames
```

This will:
- Scan all members
- Read their gang code and rank from their roles
- Update their nicknames to `[GangCode][Rank]:IGN` format
- Update registration data to match their current roles
- Try to preserve existing IGN from their current nickname

#### Update Individual Members

**Common Scenarios:**

1. **User registered with wrong gang, you manually changed their gang role:**
   ```bash
   # After changing the gang role, sync their registration
   !syncmember @username
   ```

2. **User registered with wrong rank, you need to change it:**
   ```bash
   # Use setmember to change rank (updates roles + registration + nickname)
   !setmember @username "Charles Vane" GNB R3
   ```

3. **User has wrong everything (IGN, gang, rank):**
   ```bash
   # Set everything at once
   !setmember @username NewIGN XYZ R5
   ```

**Important Notes:**
- `!syncmember` reads from current roles → updates registration data
  - Use AFTER manually changing roles
  - **Limitation:** Can't distinguish R1/R2/R3 (all use Pirate role)
- `!setmember` sets everything → updates roles AND registration data
  - Use to change rank from R1→R3, R2→R3, etc.
  - Use quotes around IGN if it has spaces: `"Player Name"`

#### Allow Members to Update Themselves
Members can update their own profile:

```bash
!reregister
```

#### Force Re-registration
Clear a member's registration so they can register again:

```bash
!updateprofile @username
```

### Railway Deployment

If deploying to Railway:

1. **Create a Volume** in your Railway service:
   - Mount path: `/app/data`
   - Size: 1GB

2. **Why?** The bot stores configuration in JSON files:
   - `language_config.json` - Translation settings
   - `registration_config.json` - Registration settings, member data, approval requirements

3. **Without a volume**, these files will be deleted on every deploy and you'll lose:
   - Channel configurations
   - Registered member data
   - Approval settings
   - Pending approvals

The bot automatically detects `/app/data` and uses it for persistent storage!
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
