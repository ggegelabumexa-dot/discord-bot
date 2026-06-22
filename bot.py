"""
Discord Bot - Dark Masculine Style
Requirements: pip install discord.py
Run: python bot.py

Commands (admin only):
  /setup-welcome  #channel  — post welcome panel
  /setup-boosts   #channel  — post boost notifications panel
  /setup-tickets  #channel  — post buy/sell ticket panel
  /setup-verify   #channel  — post verification panel
  /setup-roles    #channel  — post reaction roles panel
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from typing import Optional

# ─── CONFIG ──────────────────────────────────────────────────────────────────

TOKEN = os.environ.get("DISCORD_TOKEN", "")
GUILD_ID = int(os.environ.get("GUILD_ID", "0"))
VERIFIED_ROLE_NAME = "Verified"         # Role given on verify
BOOSTER_PERKS = ["pic perms", "custom role", "priority support"]
CONFIG_FILE = "config.json"

# Roles for reaction-role panel  (emoji: role name)
REACTION_ROLES = {
    "⚔️": "Warrior",
    "🔥": "Blazer",
    "💀": "Reaper",
    "🛡️": "Guardian",
    "⛓️": "Enforcer",
}

# ─── COLORS ──────────────────────────────────────────────────────────────────

CRIMSON     = 0x8B0000
DARK_RED    = 0xCC0000
BLACK       = 0x0D0D0D
DARK_GRAY   = 0x1A1A1A

# ─── CONFIG STORAGE ──────────────────────────────────────────────────────────

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─── BOT SETUP ───────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)
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
    embed.set_footer(text=f"{guild.name}  •  Stay sharp.", icon_url=guild.icon.url if guild.icon else None)
    embed.set_image(url="https://i.imgur.com/placeholder_dark_banner.png")  # Replace with your banner URL
    return embed


def boost_embed(member: discord.Member) -> discord.Embed:
    perks_text = "\n".join(f"🩸 **{p}**" for p in BOOSTER_PERKS)
    embed = discord.Embed(
        title="🔥  SERVER BOOST",
        description=(
            f"**{member.mention}** just powered up the server.\n\n"
            f"You now have access to:\n{perks_text}\n\n"
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
    embed.add_field(name="💳  Payment method", value=f"```{payment}```", inline=False)
    embed.add_field(name="🎮  Username", value=f"```{username}```", inline=False)
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
        guild = interaction.guild
        member = interaction.user

        category = discord.utils.get(guild.categories, name="TICKETS")
        if category is None:
            category = await guild.create_category("TICKETS")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
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

        embed = ticket_open_embed(member, self.what.value, self.payment.value, self.username.value)
        view = TicketCloseView()
        await channel.send(content=member.mention, embed=embed, view=view)
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
        guild = interaction.guild
        member = interaction.user
        role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)

        if role is None:
            role = await guild.create_role(
                name=VERIFIED_ROLE_NAME,
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
    # Re-register persistent views so buttons work after restarts
    bot.add_view(TicketOpenView())
    bot.add_view(TicketCloseView())
    bot.add_view(VerifyView())
    try:
        guild = discord.Object(id=GUILD_ID)
        synced = await tree.sync(guild=guild)
        print(f"✅  Synced {len(synced)} slash commands to guild {GUILD_ID}")
    except Exception as e:
        print(f"❌  Sync error: {e}")


@bot.event
async def on_member_join(member: discord.Member):
    config = load_config()
    channel_id = config.get("welcome_channel")
    if channel_id:
        channel = member.guild.get_channel(int(channel_id))
        if channel:
            await channel.send(embed=welcome_embed(member))


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    # Detect new boost
    if before.premium_since is None and after.premium_since is not None:
        config = load_config()
        channel_id = config.get("boost_channel")
        if channel_id:
            channel = after.guild.get_channel(int(channel_id))
            if channel:
                await channel.send(content=after.mention, embed=boost_embed(after))


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    config = load_config()
    roles_msg_id = config.get("roles_message_id")
    if not roles_msg_id or payload.message_id != int(roles_msg_id):
        return
    if payload.member.bot:
        return

    emoji = str(payload.emoji)
    role_name = REACTION_ROLES.get(emoji)
    if role_name:
        guild = bot.get_guild(payload.guild_id)
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await payload.member.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    config = load_config()
    roles_msg_id = config.get("roles_message_id")
    if not roles_msg_id or payload.message_id != int(roles_msg_id):
        return

    emoji = str(payload.emoji)
    role_name = REACTION_ROLES.get(emoji)
    if role_name:
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member and not member.bot:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.remove_roles(role)

# ─── SLASH COMMANDS ──────────────────────────────────────────────────────────

def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)


@tree.command(
    name="setup-welcome",
    description="Post the welcome panel in a channel",
    guild=discord.Object(id=GUILD_ID),
)
@is_admin()
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    config = load_config()
    config["welcome_channel"] = str(channel.id)
    save_config(config)
    embed = discord.Embed(
        description=(
            "⚔️  Welcome panel active.\n"
            f"New members will be greeted in {channel.mention}."
        ),
        color=CRIMSON,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(
    name="setup-boosts",
    description="Post the boost notifications panel in a channel",
    guild=discord.Object(id=GUILD_ID),
)
@is_admin()
async def setup_boosts(interaction: discord.Interaction, channel: discord.TextChannel):
    config = load_config()
    config["boost_channel"] = str(channel.id)
    save_config(config)
    embed = discord.Embed(
        description=(
            "🔥  Boost notifications active.\n"
            f"Boost events will be posted in {channel.mention}."
        ),
        color=CRIMSON,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(
    name="setup-tickets",
    description="Post the buy/sell ticket panel in a channel",
    guild=discord.Object(id=GUILD_ID),
)
@is_admin()
async def setup_tickets(interaction: discord.Interaction, channel: discord.TextChannel):
    view = TicketOpenView()
    msg = await channel.send(embed=ticket_panel_embed(interaction.guild), view=view)
    config = load_config()
    config["ticket_panel_message_id"] = str(msg.id)
    save_config(config)
    await interaction.response.send_message(
        embed=discord.Embed(description=f"🎟️  Ticket panel posted in {channel.mention}.", color=CRIMSON),
        ephemeral=True,
    )


@tree.command(
    name="setup-verify",
    description="Post the verification panel in a channel",
    guild=discord.Object(id=GUILD_ID),
)
@is_admin()
async def setup_verify(interaction: discord.Interaction, channel: discord.TextChannel):
    view = VerifyView()
    await channel.send(embed=verify_embed(interaction.guild), view=view)
    await interaction.response.send_message(
        embed=discord.Embed(description=f"🛡️  Verify panel posted in {channel.mention}.", color=CRIMSON),
        ephemeral=True,
    )


@tree.command(
    name="setup-roles",
    description="Post the reaction roles panel in a channel",
    guild=discord.Object(id=GUILD_ID),
)
@is_admin()
async def setup_roles(interaction: discord.Interaction, channel: discord.TextChannel):
    msg = await channel.send(embed=roles_embed(interaction.guild))
    for emoji in REACTION_ROLES.keys():
        await msg.add_reaction(emoji)
    config = load_config()
    config["roles_message_id"] = str(msg.id)
    save_config(config)
    await interaction.response.send_message(
        embed=discord.Embed(description=f"⚔️  Reaction roles panel posted in {channel.mention}.", color=CRIMSON),
        ephemeral=True,
    )

# ─── ERROR HANDLER ───────────────────────────────────────────────────────────

@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            embed=discord.Embed(description="❌  You don't have permission to use this.", color=CRIMSON),
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            embed=discord.Embed(description=f"❌  Error: `{error}`", color=CRIMSON),
            ephemeral=True,
        )

# ─── RUN ─────────────────────────────────────────────────────────────────────

bot.run(TOKEN)
