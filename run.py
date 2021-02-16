from discord.ext.commands import Bot, when_mentioned
from json import loads
from traceback import print_last
from discord.ext.commands.errors import CommandNotFound

with open("token.json","r") as file:
    config = loads(file.read())

owners = config.pop("owners",None)

me = Bot(when_mentioned,owner_ids=set(owners) if owners else None)
try:
    me.load_extension("extensions")
except Exception:
    print("Failed to load extensions. Leaving them unloaded.")
    print_last()

@me.command(hidden = True)
async def rlext(ctx):
    if await me.is_owner(ctx.author):
        me.reload_extension("extensions")
        await ctx.send("Done!")
@me.event
async def on_command_error(ctx,err):
    if type(err) == CommandNotFound:
        return
    await ctx.send(str(err))

@me.event
async def on_ready():
    print("ready!")

me.run(config["token"])
