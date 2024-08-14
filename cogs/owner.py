# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import discord
import ast
import sys

from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from utils import CONSTANTS, DBClient, Checks, CachedDB

client = DBClient.client
db = client.potatobot

def insert_returns(body):
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)

class Owner(commands.Cog, name="owner"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="dev",
        description="Commands for devs",
        usage="dev <subcommand> [args]",
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def dev(self, context: Context) -> None:
        prefix = await self.bot.get_prefix(context)

        cmds = "\n".join([f"{prefix}dev {cmd.name} - {cmd.description}" for cmd in self.dev.walk_commands()])

        embed = discord.Embed(
            title=f"Help: Dev", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{cmds}```", inline=False
        )

        await context.send(embed=embed)

    @dev.command(
        name="sync",
        description="Sync the slash commands.",
        usage="dev sync guild/global"
    )
    @app_commands.describe(scope="The scope of the sync. Can be `global` or `guild`")
    @commands.is_owner()
    async def sync(self, context: Context, scope: str) -> None:
        await context.defer()

        if scope == "global":
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands have been globally synchronized.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.copy_global_to(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Slash commands have been synchronized in this guild.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="The scope must be `global` or `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed)

    @dev.command(
        name="unsync",
        description="Unsync the slash commands",
        usage="dev unsync guild/global"
    )
    @commands.is_owner()
    async def unsync(self, context: Context, scope: str) -> None:
        await context.defer()

        if scope == "global":
            context.bot.tree.clear_commands(guild=None)
            await context.bot.tree.sync()
            embed = discord.Embed(
                description="Slash commands have been globally unsynchronized.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        elif scope == "guild":
            context.bot.tree.clear_commands(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
            embed = discord.Embed(
                description="Slash commands have been unsynchronized in this guild.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description="The scope must be `global` or `guild`.", color=0xE02B2B
        )
        await context.send(embed=embed)

    @dev.command(
        name="load",
        description="Load a cog",
        usage="dev load <cog>",
    )
    @commands.is_owner()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def load(self, context: Context, cog: str) -> None:
        try:
            await self.bot.load_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not load the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully loaded the `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @dev.command(
        name="unload",
        description="Unloads a cog.",
        usage="dev unload <cog>",
    )
    @commands.is_owner()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def unload(self, context: Context, cog: str) -> None:
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not unload the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully unloaded the `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @dev.command(
        name="reload",
        description="Reloads a cog",
        usage="dev reload <cog>",
    )
    @app_commands.describe(cog="The name of the cog to reload")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.is_owner()
    async def reload(self, context: Context, cog: str) -> None:
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
        except Exception:
            embed = discord.Embed(
                description=f"Could not reload the `{cog}` cog.", color=0xE02B2B
            )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            description=f"Successfully reloaded the `{cog}` cog.", color=0xBEBEFE
        )
        await context.send(embed=embed)

    @dev.command(
        name="shutdown",
        description="bye",
        usage="dev shutdown"
    )
    @commands.is_owner()
    async def shutdown(self, context: Context) -> None:
        embed = discord.Embed(description="Shutting down. Bye! :wave:", color=0xBEBEFE)
        await context.send(embed=embed)
        sys.exit(0)

    @commands.command(
        name="say",
        description="talk",
        usage="say <message>",
    )
    @commands.is_owner()
    async def say(self, context: Context, *, message: str) -> None:
        await context.channel.send(message)

    @commands.command(
        name="embed",
        description="say smth in embed",
        usage="embed <title> <description> [footer]",
    )
    @commands.is_owner()
    async def embed(self, context: Context, description: str = "", title: str = "", footer: str = "") -> None:
        embed = discord.Embed(
            title=title, description=description, color=0xBEBEFE
        )

        embed.set_footer(text=footer)

        await context.channel.send(embed=embed)

    @commands.command(
        name="reply",
        description="Reply to a message",
        usage="reply <channel_id> <message_id> <reply>",
    )
    @commands.is_owner()
    async def reply(self, context: Context, message: discord.Message, *, reply: str) -> None:
        await message.reply(reply)

    @dev.command(
        name="eval",
        description=":D",
        usage="eval <code>",
    )
    @commands.is_owner()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def eval(self, context, *, cmd: str):
        fn_name = "_eval_expr"

        cmd = cmd.strip("` ")

        # add a layer of indentation
        cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

        # wrap in async def body
        body = f"async def {fn_name}():\n{cmd}"

        parsed = ast.parse(body)
        body = parsed.body[0].body

        insert_returns(body)

        env = {
            'bot': context.bot,
            'discord': discord,
            'commands': commands,
            'context': context,
            'db': db,
            '__import__': __import__
        }
        exec(compile(parsed, filename="<ast>", mode="exec"), env)

        result = (await eval(f"{fn_name}()", env))
        await context.send(result)

    @dev.command(
        name="blacklist",
        description="Blacklist a user",
        usage="dev blacklist <user> [reason: optional]",
    )
    @commands.is_owner()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def blacklist(self, context, user: discord.User, *, reason: str = "No reason provided"):
        users_global = db["users_global"]
        user_data = users_global.find_one({"id": user.id})

        if user is None:
            user_data = CONSTANTS.user_global_data_template(user.id)
            users_global.insert_one(user_data)

        newdata = {
            "$set": {
                "blacklisted": True,
                "blacklist_reason": reason
            }
        }

        await CachedDB.update_one(users_global, {"id": user.id}, newdata)

        await context.send(f"{user} has been blacklisted.")

        embed = discord.Embed(
            title=f"You have been blacklisted from using the bot",
            color=0xE02B2B,
            description=f"Reason: {reason}"
        )

        try:
            await user.send(embed=embed)
        except Exception as e:
            await context.send(f"Could not send message to {user.mention} due to: {e}")

    @dev.command(
        name="unblacklist",
        description="Unblacklist a user",
        usage="dev unblacklist <user>",
    )
    @commands.is_owner()
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def unblacklist(self, context, user: discord.User):
        users_global = db["users_global"]
        user_data = users_global.find_one({"id": user.id})

        if user_data is None:
            user_data = CONSTANTS.user_global_data_template(user.id)
            users_global.insert_one(user_data)

        newdata = {
            "$set": {
                "blacklisted": False,
                "blacklist_reason": ""
            }
        }

        await CachedDB.update_one(users_global, {"id": user.id}, newdata)

        await context.send(f"{user} has been unblacklisted.")

        embed = discord.Embed(
            title=f"You have been unblacklisted from using the bot",
            color=0xBEBEFE,
        )

        try:
            await user.send(embed=embed)
        except Exception as e:
            await context.send(f"Could not send message to {user.mention} due to: {e}")

    @commands.command(
        name="dm",
        description="DM a user",
        usage="dev dm <user> <message>"
    )
    @commands.is_owner()
    async def dm(self, context: Context, user: discord.User, *, message: str) -> None:
        try:
            await user.send(message)
            await context.send(f"Sent message to {user.mention}")
        except Exception as e:
            await context.send(f"Could not send message to {user.mention} due to: {e}")

async def setup(bot) -> None:
    await bot.add_cog(Owner(bot))
