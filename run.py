from discord.ext.commands import Bot, when_mentioned
from json import loads

with open("token.json","r") as file:
    config = loads(file.read())

owners = config.pop("owners",None)

me = Bot(when_mentioned,owner_ids=set(owners) if owners else None)

me.load_extension("extensions")

@me.command(hidden = True)
async def rlext(ctx):
    if await me.is_owner(ctx.author):
        me.reload_extension("extensions")
        await ctx.send("Done!")

@me.event
async def on_ready():
    print("ready!")

me.run(config["token"])
