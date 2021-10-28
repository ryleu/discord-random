#!/usr/bin/env python3
import datetime
import json
import logging
import os
import traceback

import discord
import discord_slash
from discord.ext import commands


me = commands.Bot(commands.when_mentioned)


def format_time(time):
    return str(time)[:str(time).index(".")].replace(":", "-").replace(" ", "_")


async def rlext(ctx: discord_slash.SlashContext):
    """Reloads the commands."""
    await ctx.defer(hidden=True)
    if await me.is_owner(ctx.author):
        try:
            me.reload_extension("extensions")
        except Exception as err:
            logging.critical("\n".join(traceback.format_tb(err.__traceback__)))
            await ctx.send("wow you killed me great thanks", hidden=True)
        else:
            await ctx.send("Reloaded all commands.", hidden=True)
        print("\n-----RELOAD-----\n")
    else:
        await ctx.send("You need to be the owner of the bot to use this command.", hidden=True)


def main():
    try:
        file_name = f'logs/{format_time(datetime.datetime.now())}.log'
        logging.basicConfig(filename=file_name, level=logging.INFO)
        print("Saving logs to", file_name)
    except FileNotFoundError:
        logging.warning("No directory 'logs/' in the current working directory. Errors will not be saved.")

    try:
        token = os.environ["BOT_TOKEN"]
        logging.info("Found BOT_TOKEN in environment variables.")
    except KeyError:
        with open("token.json", "r") as file:
            token = json.loads(file.read())["token"]

    me.slash_handler = discord_slash.SlashCommand(
        me, sync_commands=True, sync_on_cog_reload=True, override_type=True, delete_from_unused_guilds=True)
    me.allowed_mentions = discord.AllowedMentions.none()
    me.help_command = None

    me.load_extension("card_extension")
    me.load_extension("dice_extension")
    me.load_extension("miscibility_extension")
    me.load_extension("info_extension")

    me.slash_handler.add_slash_command(rlext)

    @me.event
    async def on_slash_command_error(ctx, err):
        logging.exception("\n".join(traceback.format_tb(err.__traceback__)))

    @me.event
    async def on_command_error(ctx, err):
        if isinstance(err, commands.errors.CommandNotFound):
            return
        logging.exception(err)
        await ctx.send(str(err))

    @me.event
    async def on_ready():
        print(f"Logged in as {me.user}")

    me.run(token)


if __name__ == "__main__":
    main()
