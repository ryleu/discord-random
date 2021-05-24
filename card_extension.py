from discord.ext import commands
import secrets
import discord
import discord_slash
from discord_slash import cog_ext
from discord_slash.utils import manage_commands
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
            if isinstance(bot.decks, dict):
                logging.error("bot.decks should be a dict, but it got overwritten. Fix this.")
        except AttributeError:
            logging.info("bot.decks doesn't exist.")
            bot.decks = {}

    @cog_ext.cog_slash(name = "draw", options = [
            manage_commands.create_option("private","Sends the result privately",5,False)
            ])
    async def _slash_draw(self,ctx: discord_slash.SlashContext, private: bool = None):
        """Draws a card from the server specific deck."""
        await ctx.defer(hidden = private)

        # try to grab the deck for the guild
        deck = self.bot.decks.get(ctx.channel.guild.id,None)

        # if there isn't one then fail
        if deck == None or deck.cards == []:
            parsed = "There are no cards on this deck. Generate a new one with `newdeck`"

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
            manage_commands.create_option("allow_private","Enables private drawing",5,False),
            manage_commands.create_option("mode","Changes the deck's mode",5,False)
            ])
    async def _slash_newdeck(self,ctx: discord_slash.SlashContext, allow_private: bool = False):
        """Generates / regenerates the server specific deck."""
        await ctx.defer()
        try:
            if not ctx.author.guild_permissions.manage_messages:
                return await ctx.send("You need server-wide manage messages to do this.")
        except AttributeError:
            await ctx.send("I need to be in the server to do this.")
        else:
            #grabs the correct deck and fills it
            self.bot.decks[ctx.channel.guild.id] = Deck.full(allow_private = allow_private) #create a new, full deck
            await ctx.send("Successfully generated a new deck.")
    @cog_ext.cog_subcommand(base = "deck", name = "cards")
    async def _slash_deck(self,ctx: discord_slash.SlashContext):
        """Checks the amount of cards left in the deck."""
        await ctx.defer()
        #get the deck
        deck = self.bot.decks.get(ctx.channel.guild.id,None)
        #check if it's empty
        if deck == None or not deck.length:
            await ctx.send("The deck is empty.")
        else:
            await ctx.send(f"There are {str(deck.length)} card(s) left.")

def setup(bot):
    bot.add_cog(CardDeck(bot))
