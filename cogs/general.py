# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import random
import os
import time
import inspect

import logging
logger = logging.getLogger("discord_bot")

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from deep_translator import GoogleTranslator

from utils import DBClient, Checks

db = DBClient.db

class General(commands.Cog, name="⬜ General"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.get_prefix = bot.get_prefix

    @commands.hybrid_command(
        name="help",
        aliases=["h", "commands", "cmds"],
        description="Get help with commands",
        usage="help [optional: command]"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def help(self, context: Context, *, command: str = "none") -> None:
        if command != "none":
            cmd = self.bot.get_command(command)
            if cmd is None:
                await context.send("Command not found")
                return

            if cmd.cog_name == "owner" and not context.author.id in self.bot.owner_ids:
                await context.send("Command not found")
                return

            embed = discord.Embed(
                title=f"Command: {cmd.name}",
                description=cmd.description,
                color=0xBEBEFE
            )

            usage = cmd.usage if cmd.usage else "Not Set"
            example = cmd.extras["example"] if "example" in cmd.extras else "Not Set"
            embed.add_field(
                name="Usage",
                value=f"```Syntax: {usage}\nExample: {example}```",
                inline=False
            )

            aliases = ", ".join(cmd.aliases) if cmd.aliases else "None"
            embed.add_field(
                name="Aliases",
                value=f"```{aliases}```",
                inline=True
            )

            embed.add_field(
                name="Category",
                value=f"```{cmd.cog_name}```",
                inline=True
            )

            cmd_type = ""

            if isinstance(cmd, commands.HybridGroup):
                cmd_type = "Command Group"
            elif isinstance(cmd, commands.HybridCommand):
                cmd_type = "Chat+Slash Command"
            elif isinstance(cmd, commands.Command):
                cmd_type = "Chat Only Command"

            embed.add_field(
                name="Type",
                value=f"```{cmd_type}```",
                inline=True
            )

            params = inspect.signature(cmd.callback).parameters
            param_list = []
            for name, param in params.items():
                if name not in ["self", "context"]:
                    if param.default == inspect.Parameter.empty:
                        param_list.append(f"{name}: <Required>")
                    else:
                        param_list.append(f"{name}: [Optional, default: '{param.default}']")

            params_str = "\n".join(param_list) if param_list else "None"
            embed.add_field(
                name="Parameters",
                value=f"```{params_str}```",
                inline=False
            )

            if isinstance(cmd, commands.HybridGroup):
                    subcommands = ", ".join([sub.name for sub in cmd.commands])
                    embed.add_field(
                        name="Subcommands",
                        value=f"```{subcommands}```",
                        inline=False
                    )

            return await context.send(embed=embed)

        cogs = []

        for cog in self.bot.cogs:
            if cog.startswith("-"):
                continue

            if "owner" in cog and context.author.id != int(os.getenv("OWNER_ID")):
                continue

            cogs.append(cog)

        view = CogSelectView(cogs, context.author)

        await context.send('Pick a cog:', view=view)

    @commands.command(
        name="uptime",
        description="Get the bot's uptime",
        usage="uptime"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def uptime(self, context: Context):
        uptime = time.time() - self.bot.start_time
        str = time.strftime("%H:%M:%S", time.gmtime(uptime))
        await context.send("Uptime: " + str)

    @commands.hybrid_command(
        name="botinfo",
        description="See bot info",
        usage="botinfo"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def botinfo(self, context: Context) -> None:
        dpyVersion = discord.__version__
        serverCount = len(self.bot.guilds)
        memberCount = len(set(self.bot.get_all_members()))

        embed = discord.Embed(title=f'{self.bot.user.name} - Stats', color = discord.Color.blurple())

        command_count = len([command for command in self.bot.walk_commands()])

        embed.add_field(name="Discord.Py Version:", value=dpyVersion)
        embed.add_field(name="Ping:", value=f"{round(self.bot.latency * 1000)}ms")
        embed.add_field(name="Total Guilds:", value=serverCount)
        embed.add_field(name="Total Users:", value=memberCount)
        embed.add_field(name="Total Commands:", value=command_count)

        await context.send(embed=embed)

    @commands.hybrid_command(
        name="ping",
        description="Check if the bot is alive.",
        usage="ping"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ping(self, context: Context) -> None:
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="translate",
        description="Translate text to a specified language example: ;translate 'How are you' es",
        usage="translate <text> <language>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.describe(text="The text you want to translate.")
    @app_commands.describe(language="The language you want to translate the text to.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def translate(self, context: Context, text: str, language: str = "en") -> None:

        translated = GoogleTranslator(source='auto', target=language).translate(text)

        embed = discord.Embed(
            title="Translation",
            description=f"**Original text:**\n{text}\n\n**Translated text:**\n{translated}",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"Translated to {language}")
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="8ball",
        description="Ask any question to the bot.",
        usage="8ball <question>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.describe(question="The question you want to ask.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def eight_ball(self, context: Context, *, question: str) -> None:
        answers = [
            "It is certain.",
            "It is decidedly so.",
            "You may rely on it.",
            "Without a doubt.",
            "Yes - definitely.",
            "As I see, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again later.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
        ]
        embed = discord.Embed(
            title="**My Answer:**",
            description=f"{random.choice(answers)}",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"The question was: {question}")
        await context.send(embed=embed)

class CogSelect(discord.ui.Select):
    def __init__(self, cogs, author):
        options = [
            discord.SelectOption(label=cog, description=f"Show commands for {cog}")
            for cog in cogs
        ]
        super().__init__(placeholder='Choose a cog...', min_values=1, max_values=1, options=options)
        self.author = author

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot use this select.", ephemeral=True)
            return

        await interaction.response.defer()

        cog_name = self.values[0]
        cog = interaction.client.get_cog(cog_name)
        commands = cog.get_commands()
        data = []
        for command in commands:
            description = command.description.partition("\n")[0]
            data.append(f"{await interaction.client.get_prefix(interaction)}{command.name} - {description}")
        help_text = "\n".join(data)
        embed = discord.Embed(
            title=f"Help: {cog_name}", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name=cog_name.capitalize(), value=f"```{help_text}```", inline=False
        )
        embed.set_footer(text=f"To get more info on a command, use {await interaction.client.get_prefix(interaction)}help <command>")

        await interaction.message.edit(embed=embed)

class CogSelectView(discord.ui.View):
    def __init__(self, cogs, author):
        super().__init__(timeout=None)
        self.add_item(CogSelect(cogs, author))

async def setup(bot) -> None:
    await bot.add_cog(General(bot))
