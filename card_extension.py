from discord.ext import commands
import secrets
import discord
import discord_slash
from discord_slash import cog_ext, model
from discord_slash.utils import manage_commands, manage_components
import logging

class  Card():
    def __init__(self,suit,value):
        """Initializes the card with a suit and a value."""
        self.suit = suit
        self.value = value
    def __str__(self):
        """Returns the type of card in the format {value} of {suit}."""
        return f"{self.valChar} of {self.suit}s"
    @property
    def valChar(self):
        return ['?', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'][self.value]
    @property
    def suitChar(self):
        return {"heart":"♥️","club":"♣️","diamond":"♦️","spade":"♠️"}[self.suit]
    @property
    def art(self):
        return "```\n{suit}----{dash}{value}\n|     |\n|  {center} |\n|     |\n{value}{dash}----{suit}\n```".format(
                suit = self.suitChar,
                value = self.valChar,
                center = (self.valChar if len(self.valChar) > 1 else self.valChar + " "),
                dash = "-" if len(self.valChar) == 1 else ""
            )

class Deck():
    def __init__(self,*,shuffled = True,allow_private = False):
        """Initializes a card deck (basically a glorified list of cards)."""
        self.cards = []
        self.shuffled = shuffled
        self.allow_private = allow_private
    def populate(self,*,suits = ["heart","club","diamond","spade"],values = range(1,14),allow_private = None):
        if allow_private != None:
            self.allow_private = allow_private
        for i in suits:
            for j in values:
                self.cards.append(Card(i,j))
        return self
    async def draw(self,amount=1):
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
    async def extend(self, toAdd):
        self.cards.extend(toAdd)
        return self
    @property
    def length(self):
        return len(self.cards)
    @classmethod
    def full(cls,*args,**kwargs):
        return cls(*args, **kwargs).populate()

class CardDeck(commands.Cog):
    def __init__(self,bot):
        """Cog that contains all of the commands for drawing from a deck."""
        self.bot = bot
        try:
            if not isinstance(bot.decks, dict):
                logging.error("bot.decks should be a dict, but it got overwritten. Fix this.")
        except AttributeError:
            logging.info("bot.decks doesn't exist.")
            bot.decks = {}

    @cog_ext.cog_slash(name = "draw", options = [
            manage_commands.create_option(
                name = "private",
                description = "Sends the result privately",
                option_type = bool,
                required = False
                )
            ])
    async def _slash_draw(self,ctx: discord_slash.SlashContext, private: bool = None):
        """Draws a card from the server specific deck."""
        await ctx.defer(hidden = private)

        # try to grab the deck for the guild
        deck = self.bot.decks.get(ctx.channel.guild.id,None)

        # if there isn't one then fail
        if deck == None or deck.cards == []:
            parsed = "There are no cards on this deck. Generate a new one with `/deck new`"

        elif private and not deck.allow_private:
            parsed = "This deck does not allow private drawing."

        else:
            cards = await deck.draw()
            if cards == []:
                parsed = "Something went wrong. Please try again."
            else:
                card = cards[0]
                parsed = f"{ctx.author.mention} drew **{str(card)}**\n{card.art}"
        await ctx.send(parsed, hidden = private)

    @cog_ext.cog_subcommand(base = "deck", name = "new", options = [
            manage_commands.create_option(
                name = "allow_private",
                description = "Enables private drawing",
                option_type = bool,
                required = False
                ),
            manage_commands.create_option(
                name = "mode",
                description = "Changes the deck's mode",
                option_type = bool,
                required = False
                )
            ])
    async def _slash_deck_new(self,ctx: discord_slash.SlashContext, allow_private: bool = True):
        """Generates / regenerates the server specific deck."""
        try:
            if not ctx.author.guild_permissions.manage_messages:
                return await ctx.send("You need server-wide manage messages to do this.", hidden = True)
        except AttributeError:
            await ctx.send("I need to be in a server with the bot scope to do this.", hidden = True)
        else:
            await ctx.defer()
            buttons = [
                manage_components.create_button(
                    style = model.ButtonStyle.green,
                    label = "Draw",
                    custom_id = "draw_button"
                )
            ]
            if allow_private:
                buttons.append(
                    manage_components.create_button(
                        style = model.ButtonStyle.blue,
                        label = "Draw Privately",
                        custom_id = "draw_button_private"
                    )
                )
            actionRow = manage_components.create_actionrow(*buttons)
            deck = Deck.full(allow_private = allow_private) #create a new, full deck
            #grabs the correct deck and fills it
            self.bot.decks[ctx.channel.guild.id] = deck
            await ctx.send(f"**Successfully generated a new deck.**\n_{deck.length}_ card(s) remaining.", components = [actionRow])

    @cog_ext.cog_subcommand(base = "deck", name = "cards")
    async def _slash_deck_cards(self,ctx: discord_slash.SlashContext):
        """Checks the amount of cards left in the deck."""
        await ctx.defer()
        #get the deck
        deck = self.bot.decks.get(ctx.channel.guild.id,None)
        #check if it's empty
        if deck == None or not deck.length:
            await ctx.send("The deck is empty. Generate a new one with `/deck new`")
        else:
            await ctx.send(f"There are {str(deck.length)} card(s) left.")

    @cog_ext.cog_component(components = "draw_button")
    async def _draw_button_response(self, ctx: discord_slash.ComponentContext):
        await self.draw_button_response(ctx,False)

    @cog_ext.cog_component(components = "draw_button_private")
    async def _draw_button_private_response(self, ctx: discord_slash.ComponentContext):
        await self.draw_button_response(ctx,True)

    async def draw_button_response(self, ctx: discord_slash.ComponentContext, private: bool):
        """Draws a card from the server specific deck."""

        # try to grab the deck for the guild
        deck = self.bot.decks.get(ctx.channel.guild.id,None)

        # if there isn't one then fail
        if deck == None or deck.cards == []:
            await ctx.send("There are no cards on this deck. Generate a new one with `/deck new`", hidden = True)

        else:
            await ctx.defer(edit_origin=True)
            cards = await deck.draw()
            if cards == []:
                await ctx.send("Something went wrong. Please try again.", hidden = True)
            else:
                card = cards[0]
                await self.update_card_amount(ctx)
                await ctx.send(f"{ctx.author.mention} drew **{str(card)}**\n{card.art}", hidden=private)

    async def update_card_amount(self,ctx: discord_slash.ComponentContext):
        """Updates the message with the amount of cards left in the deck."""
        #get the deck
        deck = self.bot.decks.get(ctx.channel.guild.id,None)
        #check if it's empty
        if deck == None or not deck.length:
            toEdit = "The deck is empty. Generate a new one with `/deck new`"
        else:
            toEdit = f"_{deck.length}_ card(s) remaining."
        await ctx.edit_origin(content = toEdit)

def setup(bot):
    bot.add_cog(CardDeck(bot))
