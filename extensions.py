from discord.ext.commands import when_mentioned, Cog
from d20 import roll, AdvType
from d20.errors import TooManyRolls, RollSyntaxError
from random import randint
from discord import AllowedMentions
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option
import logging

def configure_bot(bot):
    bot.allowed_mentions = AllowedMentions.none()
    bot.command_prefix = when_mentioned
    bot.help_command = None

class Card():
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
                    ind = randint(0,len(self.cards))
                    drawn.append(self.cards.pop(ind))
                else:
                    drawn.append(self.cards.pop())
            except IndexError:
                return drawn
        return drawn
    def extend(self, toAdd):
        self.cards.extend(toAdd)
        return self
    @classmethod
    def full(cls,*args,**kwargs):
        return cls(*args, **kwargs).populate()

class CardDeck(Cog):
    def __init__(self,bot):
        """Cog that contains all of the commands for drawing from a deck."""
        self.bot = bot
        try:
            if isinstance(bot.decks, dict):
                logging.error("bot.decks needs to be a dict, but it got overwritten. Fix this.")
        except AttributeError:
            bot.decks = {}

    @cog_ext.cog_slash(name = "draw", options = [
            create_option("private","Sends the result privately",5,False)
            ])
    async def _slash_draw(self,ctx: SlashContext, private: bool = False):
        """Draws a card from the server specific deck."""
        await ctx.defer()

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
            create_option("allow_private","Enables private drawing",5,False),
            create_option("mode","Changes the deck's mode",5,False)
            ])
    async def _slash_newdeck(self,ctx: SlashContext, allow_private: bool = False):
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
    async def _slash_deck(self,ctx: SlashContext):
        """Checks the amount of cards left in the deck."""
        await ctx.defer()
        #get the deck
        deck = self.bot.decks.get(ctx.channel.guild.id,None)
        #check if it's empty
        if deck == None or deck.cards == []:
            await ctx.send("The deck is empty.")
        else:
            await ctx.send(f"There are {str(len(deck.cards))} card(s) left.")

class DiceRolls(Cog):
    def __init__(self,bot):
        """Cog that contains all of the commands for rolling dice."""
        self.bot = bot
    # pylint: disable=no-self-use
    def parse_roll(self,params,*,comment=None,adv = AdvType.NONE):
        try:
            result = roll(params,None,False,{"Advantage":AdvType.ADV,"Disadvantage":AdvType.DIS,"None":AdvType.NONE}[adv if adv else "None"])
        except TooManyRolls:
            return "You can't roll more than 1000 total dice."
        except RollSyntaxError as err:
            return f"""{str(err)}```\n{params}\n{(err.col-1)*" "+len(err.got)*"^"}\n```"""

        #make sure the result isn't too long
        if len(str(result)) > 500:
            result = f"{params} = `{result.total}`"
        return f"""
{str(result)}
{("Reason: "+ comment) if comment else ""}
"""

    @cog_ext.cog_slash(name = "roll", options = [
            create_option("params","Dice to roll",3,True),
            create_option("comment","Comment to add to the end",3,False),
            create_option("private","Sends the result privately",5,False)
            ])
    async def _slash_roll(self,ctx: SlashContext,**kwargs):
        """Rolls dice."""
        await ctx.defer()
        private = kwargs.pop("private",False)
        await ctx.send(self.parse_roll(**kwargs), hidden = private)

    @cog_ext.cog_slash(name = "dice", options = [
            create_option("size","The die size",3,True,["d4","d6","d8","d10","d12","d20","d100"]),
            create_option("amount","The amount of dice to roll (number)",4,False),
            create_option("private","Sends the result privately",5,False)
            ])
    async def _slash_dice(self, ctx: SlashContext, **kwargs):
        """Rolls dice (but for noobs)."""
        await ctx.defer()
        private = kwargs.pop("private",False)
        params = str(kwargs.pop("amount",1)) + kwargs.pop("size")
        await ctx.send(self.parse_roll(params = params,**kwargs),hidden = private)

cogs = [CardDeck,DiceRolls]

def setup(bot):
    configure_bot(bot)
    for i in cogs:
        bot.add_cog(i(bot))
