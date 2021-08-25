#!/usr/bin/env python3
from discord.ext import commands
import json
import logging
import traceback
import discord_slash
import datetime
import discord
import os

# all of this is protected under the license at https://github.com/ryleu/discord-cardic-inspiration/LICENSE

formatTime = lambda time: str(time)[:str(time).index(".")].replace(":","-").replace(" ","_")
try:
    fileName = f'logs/{formatTime(datetime.datetime.now())}.log'
    logging.basicConfig(filename=fileName, level=logging.INFO)
    print("Saving logs to",fileName)
except FileNotFoundError:
    logging.warning("No directory 'logs/' in the current working directory. Errors will not be saved.")

try:
    token = os.environ["BOT_TOKEN"]
    logging.info("Found BOT_TOKEN in environment variables.")
except KeyError:
    with open("token.json","r") as file:
        token = json.loads(file.read())["token"]

me = commands.Bot(commands.when_mentioned)
me.slash_handler = discord_slash.SlashCommand(me, sync_commands = True, sync_on_cog_reload = True, override_type = True, delete_from_unused_guilds = True)
me.allowed_mentions = discord.AllowedMentions.none()
me.help_command = None

me.load_extension("card_extension")
me.load_extension("dice_extension")
me.load_extension("miscibility_extension")

async def rlext(ctx: discord_slash.SlashContext):
    """Reloads the commands."""
    await ctx.defer(hidden = True)
    if await me.is_owner(ctx.author):
        try:
            me.reload_extension("extensions")
        except Exception as err:
            logging.critical("\n".join(traceback.format_tb(err.__traceback__)))
            await ctx.send("wow you killed me great thanks", hidden = True)
        else:
            await ctx.send("Reloaded all commands.", hidden = True)
        print("\n-----RELOAD-----\n")
    else:
        await ctx.send("You need to be the owner of the bot to use this command.", hidden = True)

me.slash_handler.add_slash_command(rlext)

@me.event
async def on_slash_command_error(ctx,err):
    logging.exception("\n".join(traceback.format_tb(err.__traceback__)))

@me.event
async def on_command_error(ctx,err):
    if isinstance(err,commands.errors.CommandNotFound):
        return
    logging.exception(err)
    await ctx.send(str(err))

@me.event
async def on_ready():
    print(f"Logged in as {me.user}")

me.run(token)
