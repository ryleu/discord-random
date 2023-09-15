#!/bin/env -S poetry run python3

import interactions
import os
import d20
import random

bot = interactions.Client()

# get the token. first try envars then try token.txt
token = os.environ.get("TOKEN", False)

if not (token):
    with open("token.txt") as file:
        token = file.read().strip()


@bot.listen()
async def on_startup():
    print("Bot is ready!")


@bot.command(name="info", description="Send information about this bot.")
async def info(ctx: interactions.SlashContext):
    """Displays the info of the bot."""
    await ctx.defer()
    # Create an embed to store the info
    embed = interactions.Embed(
        title="D&D Random Info", color=interactions.Color(0x00FFFF)
    )
    # Add the source code link to the embed
    embed.add_field(
        name="Source Code",
        value="[View on GitHub]("
        "https://github.com/ryleu/discord-cardic-inspiration)",
    )
    # Add the invite link to the embed
    embed.add_field(
        name="Invite",
        value="[Add me to your own server]("
        "https://discord.com/api/oauth2/authorize?client_id=803318907950596106"
        "&permissions=0&scope=applications.commands%20bot)",
    )
    # Add the syntax link to the embed
    embed.add_field(
        name="Syntax",
        value="[View the `/roll` syntax](" "https://github.com/avrae/d20#dice-syntax)",
    )
    # Add the bot author to the embed
    embed.set_footer(text="Created by ryleu")

    # Send the embed
    await ctx.send(embed=embed)


@bot.command(
    name="roll",
    description="Rolls dice using d20's roll string format.",
    options=[
        interactions.SlashCommandOption(
            name="roll_string", type=interactions.OptionType.STRING, required=True
        )
    ],
)
async def roll(ctx: interactions.SlashCommand, roll_string: str):
    try:
        roll_result = str(d20.roll(roll_string))
    except d20.errors.TooManyRolls:
        roll_result = "You can't roll more than 1000 total dice."
    except d20.errors.RollSyntaxError as err:
        escaped_params = roll_string.replace("`", "\\`")
        roll_result = f"""{str(err)}```\n{escaped_params}\n{(err.col - 1) * " " + len(err.got) * "^"}\n```"""
    except Exception as err:
        roll_result = str(err)

    await ctx.send(str(roll_result), ephemeral=True)


@bot.command(
    name="init_channel", description="Set up a channel for rolling dice with buttons."
)
async def init_channel(ctx: interactions.SlashContext):
    print(ctx.__dict__)
    buttons = interactions.spread_to_rows(
        *[
            interactions.Button(
                style=interactions.ButtonStyle.PRIMARY, label=f"d{x}", custom_id=str(x)
            )
            for x in (2, 4, 6, 8, 10, 12, 20, 100)
        ]
    )
    await ctx.send("Press a button to roll a die:", components=buttons)


@bot.listen()
async def button_pressed(event: interactions.events.ButtonPressed):
    ctx = event.ctx
    number = int(ctx.custom_id)
    await ctx.send(f"d{number} = `{random.randint(1, number)}`", ephemeral=True)


bot.start(token)
