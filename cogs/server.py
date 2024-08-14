# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord

from discord.ext import commands
from discord.ext.commands import Context

from utils import Checks, DBClient, CONSTANTS


db = DBClient.db

class Server(commands.Cog, name="⚙️ Server"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.prefixDB = bot.prefixDB

    @commands.command(
        name="prefix",
        description="Change the bot prefix",
        usage="prefix <symbol>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    async def prefix(self, context: commands.Context, prefix: str = "none"):
        if prefix == "none":
            return await context.send("Current prefix is: `" + self.prefixDB.get(str(context.guild.id)) + "`")

        if prefix == "/":
            return await context.send("Prefix cannot be `/`")

        guild_id = str(context.guild.id)
        self.prefixDB.set(guild_id, prefix)
        self.prefixDB.dump()
        await context.send(f"Prefix set to {prefix}")

    @commands.hybrid_command(
        name="stealemoji",
        description="Steal an emoji from another server.",
        usage="stealemoji <emoji> <name>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    async def stealemoji(self, context: Context, emoji: discord.PartialEmoji, name: str) -> None:
        try:
            emoji_bytes = await emoji.read()
            await context.guild.create_custom_emoji(
                name=name if name else emoji.name,
                image=emoji_bytes,
                reason=f"Emoji yoinked by {context.author} VIA {context.guild.me.name}",
            )
            await context.send(
                embed=discord.Embed(
                    description=f"Emoji Stolen",
                    color=discord.Color.random(),
                ).set_image(url=emoji.url)
            )
        except Exception as e:
            await context.send(str(e))

    @commands.hybrid_group(
        name="settings",
        description="Command to change server settings",
        aliases=["setting"],
        usage="settings <subcommand> [args]"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    async def settings(self, context: Context) -> None:
        subcommands = [cmd for cmd in self.settings.walk_commands()]

        data = []

        for subcommand in subcommands:
            description = subcommand.description.partition("\n")[0]
            data.append(f"{await self.bot.get_prefix(context)}settings {subcommand.name} - {description}")

        help_text = "\n".join(data)
        embed = discord.Embed(
            title=f"Help: Settings", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{help_text}```", inline=False
        )

        await context.send(embed=embed)

    @settings.command(
        name="show",
        description="Show server settings",
        usage="settings show"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    async def show(self, context: Context) -> None:
        c = db["guilds"]
        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        embed = discord.Embed(
            title="Server Settings",
            color=discord.Color.blue()
        )

        embed.add_field( name="Daily Cash", value=data["daily_cash"] )
        embed.add_field( name="Log Channel", value=context.guild.get_channel(data["log_channel"]).mention if data["log_channel"] else "None" )
        await context.send(embed=embed)

    @settings.command(
        name="daily-cash",
        description="Set daily cash amount",
        usage="settings daily-cash <amount>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(administrator=True)
    async def daily_cash(self, context: Context, amount: int) -> None:
        c = db["guilds"]

        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        newdata = { "$set": { "daily_cash": amount } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set daily cash to {amount}")

    @settings.command(
        name="log-channel",
        description="Set log channel",
        usage="settings log-channel <channel>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @commands.has_permissions(manage_channels=True)
    async def log_channel(self, context: Context, channel: discord.TextChannel) -> None:
        c = db["guilds"]

        data = c.find_one({"id": context.guild.id})

        if not data:
            data = CONSTANTS.guild_data_template(context.guild.id)
            c.insert_one(data)

        newdata = { "$set": { "log_channel": channel.id } }

        c.update_one({"id": context.guild.id}, newdata)

        await context.send(f"Set log channel to {channel.mention}")

async def setup(bot) -> None:
    await bot.add_cog(Server(bot))
