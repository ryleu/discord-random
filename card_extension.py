import logging
import secrets

import discord
import discord_slash
from discord.ext import commands
from discord_slash import cog_ext, model
from discord_slash.utils import manage_commands, manage_components
import json


class Card:
    def __init__(self, suit, value):
        """Initializes the card with a suit and a value."""
        self.suit = suit
        self.value = value

    def __str__(self):
        """Returns the type of card in the format {value} of {suit}."""
        return f"{self.val_char} of {self.suit}s"

    def __dict__(self):
        return {"suit": self.suit, "value": self.value}

    @property
    def val_char(self):
        return ['?', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'][self.value]

    @property
    def suit_char(self):
        return {"heart": "♥️", "club": "♣️", "diamond": "♦️", "spade": "♠️"}[self.suit]

    @property
    def art(self):
        return "```\n{suit}----{dash}{value}\n|     |\n|  {center} |\n|     |\n{value}{dash}----{suit}\n```".format(
            suit=self.suit_char,
            value=self.val_char,
            center=(self.val_char if len(self.val_char) > 1 else self.val_char + " "),
            dash="-" if len(self.val_char) == 1 else ""
        )

    @classmethod
    def from_dict(cls, data):
        return cls(data["suit"], data["value"])


class Deck:
    def __init__(self, *, shuffled=True, allow_private=False):
        """Initializes a card deck (basically a glorified list of cards)."""
        self.cards = []
        self.shuffled = shuffled
        self.allow_private = allow_private

    def __dict__(self):
        dict_cards = [dict(card) for card in self.cards]
        return {"shuffled": self.shuffled, "allow_private": self.allow_private, "cards": dict_cards}

    def populate(self, *, suits=None, values=range(1, 14), allow_private=None):
        if suits is None:
            suits = ["heart", "club", "diamond", "spade"]
        if allow_private is not None:
            self.allow_private = allow_private
        for i in suits:
            for j in values:
                self.cards.append(Card(i, j))
        return self

    async def draw(self, amount=1):
        drawn = []
        while amount > 0:
            amount -= 1
            try:
                if self.shuffled:
                    ind = secrets.randbelow(len(self.cards))
                    drawn.append(self.cards.pop(ind))
                else:
                    drawn.append(self.cards.pop())
            except IndexError:
                return drawn
        return drawn

    async def extend(self, to_add):
        self.cards.extend(to_add)
        return self

    @property
    def length(self):
        return len(self.cards)

    @classmethod
    def full(cls, *args, **kwargs):
        return cls(*args, **kwargs).populate()

    @classmethod
    def from_dict(cls, data):
        deck = cls(shuffled=data["shuffled"], allow_private=data["allow_private"])
        deck.cards = [Card.from_dict(card) for card in data["cards"]]
        return deck


class CardDeck(commands.Cog):
    def __init__(self, bot):
        """Cog that contains all the commands for drawing from a deck."""
        self.bot = bot
        try:
            if not isinstance(bot.decks, dict):
                logging.error("bot.decks should be a dict, but it got overwritten. Fix this.")
                bot.decks = {}
        except AttributeError:
            logging.info("bot.decks doesn't exist.")
            bot.decks = {}

    def json_write_out(self):
        data = {}
        for deck in self.bot.decks.keys():
            data[deck] = dict(self.bot.decks[deck])
        with open("decks.json", "w") as file:
            file.write(json.dumps(data))

    def json_read_in(self):
        self.bot.decks = {}
        data = {}
        try:
            with open("decks.json", "r") as file:
                data = json.loads(file.read())
        except json.JSONDecodeError as e:
            logging.error(e)
        except FileNotFoundError:
            open("decks.json", "x").close()
        for entry in data.keys():
            self.bot.decks[entry] = Deck.from_dict(data[entry])

    @cog_ext.cog_slash(name="draw", options=[
        manage_commands.create_option(
            name="private",
            description="Sends the result privately",
            option_type=bool,
            required=False
        )
    ])
    async def _slash_draw(self, ctx: discord_slash.SlashContext, private: bool = None):
        """Draws a card from the server specific deck."""
        await ctx.defer(hidden=private)

        # try to grab the deck for the guild
        deck = self.bot.decks.get(ctx.guild_id, None)

        # if there isn't one then make one
        if deck is None:
            self.bot.decks[ctx.guild_id] = Deck.full()
            deck = self.bot.decks[ctx.guild_id]
        # if it's empty then fail
        if not deck.cards:
            parsed = "There are no cards on this deck. Generate a new one with `/deck new`"

        elif private and not deck.allow_private:
            parsed = "This deck does not allow private drawing."

        else:
            cards = await deck.draw()
            if not cards:
                parsed = "Something went wrong. Please try again."
            else:
                card = cards[0]
                parsed = f"{ctx.author.mention} drew **{str(card)}**\n{card.art}"
        await ctx.send(parsed, hidden=private)

        self.json_write_out()

    @cog_ext.cog_subcommand(base="deck", name="new", options=[
        manage_commands.create_option(
            name="allow_private",
            description="Enables private drawing",
            option_type=bool,
            required=False
        ),
        manage_commands.create_option(
            name="mode",
            description="Changes the deck's mode",
            option_type=bool,
            required=False
        )
    ])
    async def _slash_deck_new(self, ctx: discord_slash.SlashContext, allow_private: bool = False):
        """Generates / regenerates the server specific deck."""
        await ctx.defer()
        buttons = [
            manage_components.create_button(
                style=model.ButtonStyle.green,
                label="Draw",
                custom_id="draw_button"
            )
        ]
        if allow_private:
            buttons.append(
                manage_components.create_button(
                    style=model.ButtonStyle.blue,
                    label="Draw Privately",
                    custom_id="draw_button_private"
                )
            )
        action_row = manage_components.create_actionrow(*buttons)
        deck = Deck.full(allow_private=allow_private)  # create a new, full deck
        # grabs the correct deck and fills it
        self.bot.decks[ctx.guild_id] = deck
        await ctx.send(f"**Successfully generated a new deck.**\n_{deck.length}_ card(s) remaining.",
                       components=[action_row])

        self.json_write_out()

    @cog_ext.cog_subcommand(base="deck", name="cards")
    async def _slash_deck_cards(self, ctx: discord_slash.SlashContext):
        """Checks the amount of cards left in the deck."""
        await ctx.defer()
        # get the deck
        deck = self.bot.decks.get(ctx.guild_id, None)
        # check if it's empty
        if deck is None or not deck.length:
            # create an embed saying there are no cards
            embed = discord.Embed(title="No cards left", description="The deck is empty. Generate a new one with "
                                                                     "`/deck new`", color=0xFF0000)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Card count", description=f"There are {str(deck.length)} card(s) left.",
                                  color=0x0000FF)
            await ctx.send(embed=embed)

    @cog_ext.cog_component(components="draw_button")
    async def _draw_button_response(self, ctx: discord_slash.ComponentContext):
        await self.draw_button_response(ctx, False)

    @cog_ext.cog_component(components="draw_button_private")
    async def _draw_button_private_response(self, ctx: discord_slash.ComponentContext):
        await self.draw_button_response(ctx, True)

    async def draw_button_response(self, ctx: discord_slash.ComponentContext, private: bool):
        """Draws a card from the server specific deck."""

        # try to grab the deck for the guild
        deck = self.bot.decks.get(ctx.guild_id, None)

        # if there isn't one then fail
        if deck is None or deck.cards == []:
            await ctx.send("There are no cards on this deck. Generate a new one with `/deck new`", hidden=True)
        else:
            await ctx.defer(edit_origin=True)
            cards = await deck.draw()
            if not cards:
                await ctx.send("Something went wrong. Please try again.", hidden=True)
            if private and not deck.allow_private:
                await ctx.send("This deck does not allow private drawing.", hidden=True)
            else:
                card = cards[0]
                await self.update_card_amount(ctx)
                await ctx.send(f"{ctx.author.mention} drew **{str(card)}**\n{card.art}", hidden=private)

        self.json_write_out()

    async def update_card_amount(self, ctx: discord_slash.ComponentContext):
        """Updates the message with the amount of cards left in the deck."""
        # get the deck
        deck = self.bot.decks.get(ctx.guild_id, None)
        # check if it's empty
        if deck is None or not deck.length:
            to_edit = "The deck is empty. Generate a new one with `/deck new`"
        else:
            to_edit = f"_{deck.length}_ card(s) remaining."
        await ctx.edit_origin(content=to_edit)


def setup(bot):
    cog = CardDeck(bot)
    bot.add_cog(CardDeck(bot))
    cog.json_read_in()
