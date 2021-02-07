import discord
from discord.ext import commands
import json
import random
from asyncio import sleep
import d20

with open("token.json","r") as file:
    token = json.loads(file.read())["token"]

me = commands.Bot(commands.when_mentioned_or("?"),allowed_mentions=discord.AllowedMentions.none())

me.load_extension("extensions")

@me.command(hidden = True)
async def rlext(ctx):
    if ctx.author.id == 600130839870963725:
        me.reload_extension("extensions")
        await ctx.send("Done!")

handle_errors = me.on_command_error

@me.event
async def on_command_error(ctx,err):
    if type(err) == discord.ext.commands.errors.CommandNotFound:
        return
    await ctx.send(str(err))
    #await handle_errors(ctx,err)

@me.event
async def on_ready():
    print("ready!")

me.run(token)
