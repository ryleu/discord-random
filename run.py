from discord.ext.commands import Bot, when_mentioned
from json import loads
import logging
from traceback import format_tb
from discord.ext.commands.errors import CommandNotFound
from discord_slash import SlashCommand, SlashContext
from discord import Forbidden
from datetime import datetime

def formatTime(time):
    timeStr = str(time)
    return timeStr[:timeStr.index(".")].replace(":","-").replace(" ","_")
logging.basicConfig(filename=f'logs/{formatTime(datetime.now())}.log', encoding='utf-8', level=logging.INFO)

with open("token.json","r") as file:
    config = loads(file.read())

owners = config.pop("owners",None)

me = Bot(when_mentioned,owner_ids=set(owners) if owners else None)
me.slash_handler = SlashCommand(me, sync_on_cog_reload = True, override_type = True, delete_from_unused_guilds = True)

me.load_extension("extensions")

async def rlext(ctx: SlashContext):
    """Reloads the commands."""
    await ctx.ack()
    if await me.is_owner(ctx.author):
        try:
            me.reload_extension("extensions")
        except Exception as err:
            logging.critical("\n".join(format_tb(err.__traceback__)))
            await ctx.send_hidden("wow you killed me great thanks")
        else:
            await ctx.send_hidden("Reloaded all commands.")
        print("\n-----RELOAD-----\n")
    else:
        await ctx.send_hidden("You need to be the owner of the bot to use this command.")

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
    print("ready!")

me.run(config["token"])
