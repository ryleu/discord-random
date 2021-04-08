#!/usr/bin/env python3
from discord.ext.commands import Bot, when_mentioned
from json import loads
import logging
from traceback import format_tb
from discord.ext.commands.errors import CommandNotFound
from discord_slash import SlashCommand, SlashContext
from datetime import datetime
from discord import Activity, ActivityType, CustomActivity

formatTime = lambda time: str(time)[:str(time).index(".")].replace(":","-").replace(" ","_")
try:
    logging.basicConfig(filename=f'logs/{formatTime(datetime.now())}.log', level=logging.INFO)
except FileNotFoundError:
    logging.warning("No directory 'logs/' in the current working directory. Errors will not be saved.")

with open("token.json","r") as file:
    config = loads(file.read())

owners = config.pop("owners",None)

me = Bot(when_mentioned,owner_ids=set(owners) if owners else None,
    activity = CustomActivity(name = "Secretly put this as your status and don’t mention it to me or anyone and we can watch it silently spread."))
me.slash_handler = SlashCommand(me, sync_on_cog_reload = True, override_type = True, delete_from_unused_guilds = True)

me.load_extension("extensions")

async def rlext(ctx: SlashContext):
    """Reloads the commands."""
    await ctx.defer(hidden = True)
    if await me.is_owner(ctx.author):
        try:
            me.reload_extension("extensions")
        except Exception as err:
            logging.critical("\n".join(format_tb(err.__traceback__)))
            await ctx.send("wow you killed me great thanks", hidden = True)
        else:
            await ctx.send("Reloaded all commands.", hidden = True)
        print("\n-----RELOAD-----\n")
    else:
        await ctx.send("You need to be the owner of the bot to use this command.", hidden = True)

me.slash_handler.add_slash_command(rlext)

@me.event
async def on_slash_command_error(ctx,err):
    logging.exception("\n".join(format_tb(err.__traceback__)))

@me.event
async def on_command_error(ctx,err):
    if isinstance(err,CommandNotFound):
        return
    logging.exception(err)
    await ctx.send(str(err))

@me.event
async def on_ready():
    print(f"Logged in as {me.user}")

me.run(config["token"])
