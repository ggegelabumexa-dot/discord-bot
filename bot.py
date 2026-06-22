"""
Discord Bot - Dark Masculine Style  (Multi-Server)
Requirements: pip install discord.py
Run: python bot.py

Commands (admin only — work in ANY server):
  /setup-welcome  #channel  — post welcome panel
  /setup-boosts   #channel  — post boost notifications panel
  /setup-tickets  #channel  — post buy/sell ticket panel
  /setup-verify   #channel  — post verification panel
  /setup-roles    #channel  — post reaction roles panel

Note: Global slash commands take up to 1 hour to appear after first launch.
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio

# ─── CONFIG ──────────────────────────────────────────────────────────────────

TOKEN             = os.environ.get("DISCORD_TOKEN", "")
VERIFIED_ROLE     = "Verified"
BOOSTER_PERKS     = ["pic perms", "custom role", "priority support"]
CONFIG_FILE       = "config.json"

# Reaction roles: emoji → role name (used across all servers)
REACTION_ROLES = {
    "⚔️": "Warrior",
    "🔥": "Blazer",
    "💀": "Reaper",
    "🛡️": "Guardian",
    "⛓️": "Enforcer",
}

# ─── COLORS ──────────────────────────────────────────────────────────────────

CRIMSON  = 0x8B0000
DARK_RED = 0xCC0000

# ─── PER-GUILD CONFIG STORAGE ────────────────────────────────────────────────
# Config is stored per guild: { "GUILD_ID": { "welcome_channel": ..., ... } }

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_guild_config(guild_id: int) -> dict:
    return load_config().get(str(guild_id), {})

def set_guild_config(guild_id: int, key: str, value: str):
    config = load_config()
    gid = str(guild_id)
    if gid not in config:
        config[gid] = {}
    config[gid][key] = value
    save_config(config)

# ─── BOT SETUP ───────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot  = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ─── EMBEDS ──────────────────────────────────────────────────────────────────

def welcome_embed(member: discord.Member) -> discord.Embed:
    guild = member.guild
    embed = discord.Embed(
        title=f"⚔️  WELCOME TO {guild.name.upper()}",
        description=(
            f"Soldier **{member.mention}** has entered the ranks.\n\n"
            f"📜 Read the rules before anything else.\n"
            f"🎭 Grab your roles to unlock channels.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        ),
        color=CRIMSON,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="👥 Members", value=f"`{guild.member_count}`", inline=True)
    embed.add_field(name="📌 Get Started", value="➜ `#rules`  •  `#roles`", inline=True)
    embed.set_footer(
        text=f"{guild.name}  •  Stay sharp.",
        icon_url=guild.icon.url if guild.icon else None,
    )
    return embed


def boost_embed(member: discord.Member) -> discord.Embed:
    perks = "\n".join(f"🩸 **{p}**" for p in BOOSTER_PERKS)
    embed = discord.Embed(
        title="🔥  SERVER BOOST",
        description=(
            f"**{member.mention}** just powered up the server.\n\n"
            f"You now have access to:\n{perks}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        ),
        color=DARK_RED,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Respect earned. Power gained.")
    return embed


def verify_embed(guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(
        title="🛡️  VERIFICATION",
        description=(
            f"**{guild.name}**\n\n"
            "Click the button below to verify and gain access to the server.\n\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=CRIMSON,
    )
    embed.set_footer(text="One click. Full access.")
    return embed


def ticket_panel_embed(guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(
        title="🎟️  OPEN A TICKET",
        description=(
            "Need to buy or sell? Open a ticket.\n\n"
            "Fill out the form with what you're trading and your payment method.\n"
            "Staff will be with you shortly.\n\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=CRIMSON,
    )
    embed.set_footer(text=f"{guild.name}  •  Powered by the bot")
    return embed


def ticket_open_embed(member: discord.Member, what: str, payment: str, username: str) -> discord.Embed:
    embed = discord.Embed(
        title="🎟️  TICKET OPENED",
        description=(
            f"Welcome, **{member.mention}**.\n"
            "Thank you for opening a ticket. Please wait for staff.\n\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=CRIMSON,
    )
    embed.add_field(name="📦  What are you trading", value=f"```{what}```", inline=False)
    embed.add_field(name="💳  Payment method",        value=f"```{payment}```", inline=False)
    embed.add_field(name="🎮  Username",               value=f"```{username}```", inline=False)
    embed.set_footer(text="Do not share passwords or sensitive info.")
    return embed


def roles_embed(guild: discord.Guild) -> discord.Embed:
    roles_text = "\n".join(f"{emoji}  **{role}**" for emoji, role in REACTION_ROLES.items())
    embed = discord.Embed(
        title="⚔️  ROLES",
        description=(
            f"{roles_text}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "React below to claim your role."
        ),
        color=CRIMSON,
    )
    embed.set_footer(text=f"{guild.name}  •  React to get roles")
    return embed

# ─── VIEWS & MODALS ──────────────────────────────────────────────────────────

class TicketModal(discord.ui.Modal, title="🎟️  Open a Ticket"):
    what = discord.ui.TextInput(
        label="What are you buying / selling?",
        placeholder="e.g. Adopt Me pets, robux, gamepass...",
        style=discord.TextStyle.short,
        required=True,
    )
    payment = discord.ui.TextInput(
        label="Payment method",
        placeholder="e.g. PayPal, LTC, Robux...",
        style=discord.TextStyle.short,
        required=True,
    )
    username = discord.ui.TextInput(
        label="Your game username",
        placeholder="e.g. KairoXzz",
        style=discord.TextStyle.short,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild  = interaction.guild
        member = interaction.user

        category = discord.utils.get(guild.categories, name="TICKETS")
        if category is None:
            category = await guild.create_category("TICKETS")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member:             discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me:           discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        for role in guild.roles:
            if role.permissions.manage_guild:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{member.name}",
            category=category,
            overwrites=overwrites,
            topic=f"Ticket opened by {member} — {self.what.value}",
        )

        await channel.send(
            content=member.mention,
            embed=ticket_open_embed(member, self.what.value, self.payment.value, self.username.value),
            view=TicketCloseView(),
        )
        await interaction.response.send_message(
            f"✅  Your ticket is open: {channel.mention}", ephemeral=True
        )


class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎟️  Open Ticket", style=discord.ButtonStyle.danger, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal())


class TicketCloseReasonModal(discord.ui.Modal, title="Close Ticket — Reason"):
    reason = discord.ui.TextInput(
        label="Reason for closing",
        placeholder="Enter the reason...",
        style=discord.TextStyle.paragraph,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"🔒  Ticket closed by {interaction.user.mention}\n**Reason:** {self.reason.value}",
                color=CRIMSON,
            )
        )
        await asyncio.sleep(5)
        await interaction.channel.delete()


class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=discord.Embed(description="🔒  Closing ticket in 5 seconds...", color=CRIMSON),
        )
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="🔒 Close With Reason", style=discord.ButtonStyle.secondary, custom_id="close_with_reason")
    async def close_with_reason(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketCloseReasonModal())


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅  Verify", style=discord.ButtonStyle.danger, custom_id="verify_button")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild  = interaction.guild
        member = interaction.user
        role   = discord.utils.get(guild.roles, name=VERIFIED_ROLE)

        if role is None:
            role = await guild.create_role(
                name=VERIFIED_ROLE,
                color=discord.Color.from_rgb(139, 0, 0),
                reason="Auto-created by bot for verification",
            )

        if role in member.roles:
            await interaction.response.send_message("⚔️  You're already verified.", ephemeral=True)
        else:
            await member.add_roles(role)
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"🛡️  **{member.mention}** — verification complete. Welcome in.",
                    color=CRIMSON,
                ),
                ephemeral=True,
            )

# ─── EVENTS ──────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"⚔️  Bot online: {bot.user} ({bot.user.id})")
    print(f"📡  In {len(bot.guilds)} server(s): {[g.name for g in bot.guilds]}")
    bot.add_view(TicketOpenView())
    bot.add_view(TicketCloseView())
    bot.add_view(VerifyView())
    try:
        # Global sync — works in ALL servers, takes up to 1 hour to appear
        synced = await tree.sync()
        print(f"✅  Synced {len(synced)} global slash commands")
    except Exception as e:
        print(f"❌  Sync error: {e}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    print(f"➕  Joined new server: {guild.name} ({guild.id})")


@bot.event
async def on_member_join(member: discord.Member):
    cfg = get_guild_config(member.guild.id)
    channel_id = cfg.get("welcome_channel")
    if channel_id:
        channel = member.guild.get_channel(int(channel_id))
        if channel:
            await channel.send(embed=welcome_embed(member))


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.premium_since is None and after.premium_since is not None:
        cfg = get_guild_config(after.guild.id)
        channel_id = cfg.get("boost_channel")
        if channel_id:
            channel = after.guild.get_channel(int(channel_id))
            if channel:
                await channel.send(content=after.mention, embed=boost_embed(after))


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.member and payload.member.bot:
        return
    cfg = get_guild_config(payload.guild_id)
    roles_msg_id = cfg.get("roles_message_id")
    if not roles_msg_id or payload.message_id != int(roles_msg_id):
        return

    role_name = REACTION_ROLES.get(str(payload.emoji))
    if role_name:
        guild = bot.get_guild(payload.guild_id)
        role  = discord.utils.get(guild.roles, name=role_name)
        if role:
            await payload.member.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    cfg = get_guild_config(payload.guild_id)
    roles_msg_id = cfg.get("roles_message_id")
    if not roles_msg_id or payload.message_id != int(roles_msg_id):
        return

    role_name = REACTION_ROLES.get(str(payload.emoji))
    if role_name:
        guild  = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member and not member.bot:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.remove_roles(role)

# ─── SLASH COMMANDS (GLOBAL — all servers) ───────────────────────────────────

def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)


def apply_image(embed: discord.Embed, url: str) -> discord.Embed:
    url = url.strip()
    if url:
        embed.set_image(url=url)
    return embed


class WelcomeSetupModal(discord.ui.Modal, title="⚔️  Welcome Channel Setup"):
    intro = discord.ui.TextInput(
        label="Intro message",
        placeholder="e.g. Welcome to our server! Check #rules and #roles to get started.",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000,
    )
    image_url = discord.ui.TextInput(
        label="Image URL (optional — leave blank to skip)",
        placeholder="https://i.imgur.com/yourimage.png",
        style=discord.TextStyle.short,
        required=False,
    )

    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        set_guild_config(guild.id, "welcome_channel", str(self.channel.id))

        embed = discord.Embed(description=self.intro.value, color=CRIMSON)
        embed.set_footer(text=f"{guild.name}  •  Welcome channel")
        apply_image(embed, self.image_url.value or "")
        await self.channel.send(embed=embed)

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"⚔️  Welcome panel active. New members greeted in {self.channel.mention}.",
                color=CRIMSON,
            ),
            ephemeral=True,
        )


class BoostSetupModal(discord.ui.Modal, title="🔥  Boost Channel Setup"):
    intro = discord.ui.TextInput(
        label="Intro message",
        placeholder="e.g. Boosters get special perks! Thank you for supporting us.",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000,
    )
    image_url = discord.ui.TextInput(
        label="Image URL (optional — leave blank to skip)",
        placeholder="https://i.imgur.com/yourimage.png",
        style=discord.TextStyle.short,
        required=False,
    )

    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        set_guild_config(guild.id, "boost_channel", str(self.channel.id))

        embed = discord.Embed(description=self.intro.value, color=DARK_RED)
        embed.set_footer(text=f"{guild.name}  •  Boost notifications")
        apply_image(embed, self.image_url.value or "")
        await self.channel.send(embed=embed)

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"🔥  Boost notifications active in {self.channel.mention}.",
                color=CRIMSON,
            ),
            ephemeral=True,
        )


class TicketSetupModal(discord.ui.Modal, title="🎟️  Ticket Panel Setup"):
    intro = discord.ui.TextInput(
        label="Intro message (shown above the panel)",
        placeholder="e.g. Hello! This is where you can buy/sell. Open a ticket below!",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000,
    )
    image_url = discord.ui.TextInput(
        label="Image URL (optional — leave blank to skip)",
        placeholder="https://i.imgur.com/yourimage.png",
        style=discord.TextStyle.short,
        required=False,
    )

    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild

        embed = discord.Embed(description=self.intro.value, color=CRIMSON)
        embed.set_footer(text=f"{guild.name}  •  Read before opening a ticket")
        apply_image(embed, self.image_url.value or "")
        await self.channel.send(embed=embed)

        msg = await self.channel.send(embed=ticket_panel_embed(guild), view=TicketOpenView())
        set_guild_config(guild.id, "ticket_panel_message_id", str(msg.id))

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"🎟️  Ticket panel posted in {self.channel.mention}.",
                color=CRIMSON,
            ),
            ephemeral=True,
        )


class VerifySetupModal(discord.ui.Modal, title="🛡️  Verify Channel Setup"):
    intro = discord.ui.TextInput(
        label="Intro message",
        placeholder="e.g. Click below to verify and gain access to the server.",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000,
    )
    image_url = discord.ui.TextInput(
        label="Image URL (optional — leave blank to skip)",
        placeholder="https://i.imgur.com/yourimage.png",
        style=discord.TextStyle.short,
        required=False,
    )

    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild

        embed = discord.Embed(description=self.intro.value, color=CRIMSON)
        embed.set_footer(text=f"{guild.name}  •  Verification")
        apply_image(embed, self.image_url.value or "")
        await self.channel.send(embed=embed)

        await self.channel.send(embed=verify_embed(guild), view=VerifyView())

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"🛡️  Verify panel posted in {self.channel.mention}.",
                color=CRIMSON,
            ),
            ephemeral=True,
        )


class RolesSetupModal(discord.ui.Modal, title="⚔️  Roles Channel Setup"):
    intro = discord.ui.TextInput(
        label="Intro message",
        placeholder="e.g. React below to grab your roles!",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000,
    )
    image_url = discord.ui.TextInput(
        label="Image URL (optional — leave blank to skip)",
        placeholder="https://i.imgur.com/yourimage.png",
        style=discord.TextStyle.short,
        required=False,
    )

    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild

        embed = discord.Embed(description=self.intro.value, color=CRIMSON)
        embed.set_footer(text=f"{guild.name}  •  Roles")
        apply_image(embed, self.image_url.value or "")
        await self.channel.send(embed=embed)

        msg = await self.channel.send(embed=roles_embed(guild))
        for emoji in REACTION_ROLES:
            await msg.add_reaction(emoji)
        set_guild_config(guild.id, "roles_message_id", str(msg.id))

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"⚔️  Reaction roles panel posted in {self.channel.mention}.",
                color=CRIMSON,
            ),
            ephemeral=True,
        )


@tree.command(name="setup-welcome", description="Post the welcome panel in a channel")
@is_admin()
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_modal(WelcomeSetupModal(channel=channel))


@tree.command(name="setup-boosts", description="Set the channel for boost notifications")
@is_admin()
async def setup_boosts(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_modal(BoostSetupModal(channel=channel))


@tree.command(name="setup-tickets", description="Post the buy/sell ticket panel in a channel")
@is_admin()
async def setup_tickets(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_modal(TicketSetupModal(channel=channel))


@tree.command(name="setup-verify", description="Post the verification panel in a channel")
@is_admin()
async def setup_verify(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_modal(VerifySetupModal(channel=channel))


@tree.command(name="setup-roles", description="Post the reaction roles panel in a channel")
@is_admin()
async def setup_roles(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_modal(RolesSetupModal(channel=channel))

# ─── ERROR HANDLER ───────────────────────────────────────────────────────────

@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        msg = "❌  You need Administrator permission to use this."
    else:
        msg = f"❌  Error: `{error}`"
    await interaction.response.send_message(
        embed=discord.Embed(description=msg, color=CRIMSON), ephemeral=True
    )

# ─── RUN ─────────────────────────────────────────────────────────────────────

bot.run(TOKEN)
