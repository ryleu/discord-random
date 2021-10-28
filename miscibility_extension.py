import logging
import secrets

import discord_slash
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils import manage_commands


class ValueRange:
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def __contains__(self, number):
        return self.low <= number <= self.high


class MiscibilityTable:
    def __init__(self, effect_dict):
        """Initializes a miscibility table with ranges and formatting."""
        self.effect_dict = effect_dict

    def format_results(self, number, potion1, potion2):
        if number == 0:
            number = 100
        if number > 100 or number < 0:
            raise ValueError("number must be between 00 and 99")
        for valRange in self.effect_dict:
            if number in valRange:
                return self.effect_dict[valRange].format(pot1=potion1, pot2=potion2)


class RandomFormat:
    def __init__(self, text):
        self.text = text

    def format(self, potion1, potion2):
        if secrets.randbelow(2):
            return self.text.format(pot1=potion1, pot2=potion2)


tables = {
    "Basic": MiscibilityTable({
        ValueRange(1,
                   8): "Immiscible. The ingredients of **{pot1}** and **{pot2}** combine to make a deadly acid. The "
                       "user takes 4d10 acid damage.",
        ValueRange(9,
                   20): "Immiscible. The ingredients of **{pot1}** and **{pot2}** combine to make a poisonous toxin. "
                        "The user takes 3d8 poison damage, and must succeed a DC 13 Constitution saving throw or be "
                        "Poisoned for 1 minute.",
        ValueRange(21, 34): "Immiscible. **{pot1}** and **{pot2}** are destroyed, as they cancel each other.",
        ValueRange(35, 70): RandomFormat("Immiscible. **{pot1}** is destroyed, and **{pot2}** functions normally"),
        ValueRange(71,
                   80): "Miscible, with Side Effects. **{pot1}** and **{pot2}** work normally, but the imbiber takes "
                        "one level of exhaustion, which lasts until after the potions' effects have expired and they "
                        "finish a Short Rest.",
        ValueRange(81,
                   92): "Miscible, with Side Effects. **{pot1}** and **{pot2}**, but their durations are each halved.",
        ValueRange(92,
                   100): "Miscible. **{pot1}** and **{pot2}** work normally unless their effects are contradictory, "
                         "e.g. diminution / growth. "
    }),
    "Permanent Variant": MiscibilityTable({
        ValueRange(1,
                   8): "Immiscible. The ingredients of **{pot1}** and **{pot2}** combine to make a deadly acid. The "
                       "user takes 4d10 acid damage.",
        ValueRange(9,
                   20): "Immiscible. The ingredients of **{pot1}** and **{pot2}** combine to make a poisonous toxin. "
                        "The user takes 3d8 poison damage, and must succeed a DC 13 Constitution saving throw or be "
                        "Poisoned for 1 minute.",
        ValueRange(21, 34): "Immiscible. **{pot1}** and **{pot2}** are destroyed, as they cancel each other.",
        ValueRange(35, 70): RandomFormat("Immiscible. **{pot1}** is destroyed, and **{pot2}** functions normally"),
        ValueRange(71,
                   80): "Miscible, with Side Effects. **{pot1}** and **{pot2}** work normally, but the imbiber takes "
                        "one level of exhaustion, which lasts until after the potions' effects have expired and they "
                        "finish a Short Rest.",
        ValueRange(81,
                   92): "Miscible, with Side Effects. **{pot1}** and **{pot2}**, but their durations are each halved.",
        ValueRange(92,
                   99): "Miscible. **{pot1}** and **{pot2}** work normally unless their effects are contradictory, "
                        "e.g. diminution / growth.",
        ValueRange(100, 100): RandomFormat("Miscible. **{pot1}** becomes permanent and **{pot2}** is destroyed.")
    })
}


class Miscibility(commands.Cog):
    def __init__(self, bot):
        """Cog that contains all of the commands for drawing from a deck."""
        self.bot = bot
        try:
            if isinstance(bot.decks, dict):
                logging.error("bot.decks should be a dict, but it got overwritten. Fix this.")
        except AttributeError:
            logging.info("bot.decks doesn't exist.")
            bot.decks = {}

    @cog_ext.cog_slash(name="potionmix", options=[
        manage_commands.create_option(
            name="table",
            description="Miscibility table to use",
            option_type=str,
            required=True,
            choices=[x for x in tables]
        ),
        manage_commands.create_option(
            name="pot1",
            description="First potion",
            option_type=str,
            required=True
        ),
        manage_commands.create_option(
            name="pot2",
            description="First potion",
            option_type=str,
            required=True
        ),
        manage_commands.create_option(
            name="private",
            description="Sends the result privately",
            option_type=bool,
            required=False
        )
    ])
    async def _slash_potionmix(
            self,
            ctx: discord_slash.SlashContext,
            table: str,
            pot1: str,
            pot2: str,
            private: bool = None
    ):
        """Mixes potions."""
        await ctx.defer(hidden=private)

        parsed = tables[table].format_results(secrets.randbelow(100), pot1, pot2)

        await ctx.send(parsed, hidden=private)


def setup(bot):
    bot.add_cog(Miscibility(bot))
