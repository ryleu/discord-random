from discord.ext.commands import Bot, when_mentioned
from json import loads
from traceback import print_last
from discord.ext.commands.errors import CommandNotFound
from discord_slash import SlashCommand, SlashContext

with open("token.json","r") as file:
    config = loads(file.read())

owners = config.pop("owners",None)

me = Bot(when_mentioned,owner_ids=set(owners) if owners else None)
me.slash_handler = SlashCommand(me, sync_on_cog_reload = True, override_type = True, delete_from_unused_guilds = True)

try:
    me.load_extension("extensions")
except Exception:
    print("Failed to load extensions. Leaving them unloaded.")
    print_last()

@me.slash_handler.slash(name = "rlext")
async def _slash_rlext(ctx: SlashContext):
    """Reloads the commands."""
    await ctx.ack()
    if await me.is_owner(ctx.author):
        await ctx.send_hidden("Reloading all extensions and refreshing slash commands...")
        me.reload_extension("extensions")
        print("\n-----RELOAD-----\n")
    else:
        await ctx.send_hidden("You need to be the owner of the bot to use this command.")

@me.command(hidden = True)
async def rlext(ctx):
    if await me.is_owner(ctx.author):
        await ctx.send("Reloading all extensions and refreshing slash commands...")
        me.reload_extension("extensions")
        print("\n-----RELOAD-----\n")

@me.event
async def on_command_error(ctx,err):
    if isinstance(err,CommandNotFound):
        return
    await ctx.send(str(err))

@me.event
async def on_ready():
    print("ready!")

me.run(config["token"])
