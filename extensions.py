from discord.ext.commands import when_mentioned_or, command, Cog
from d20 import roll
from random import randint
from discord import AllowedMentions, DMChannel
from discord_slash import cog_ext, SlashContext

def configure_bot(bot):
    bot.allowed_mentions = AllowedMentions.none()
    bot.command_prefix = when_mentioned_or("?")

class Card():
    def __init__(self,suit,value):
        # initialize the card with a suit and a value
        self.suit = suit
        self.value = value

        # set the icon to the proper thing
        if self.value > 10: # 11 = J, 12 = Q, 12 = K
            self.valChar = ["J","Q","K"][self.value - 11]
        elif self.value == 1:
            self.valChar = "A"
        else:
            self.valChar = str(self.value)
        id = ["heart","club","diamond","spade"].index(self.suit)
        self.suitChar = ["♥️","♣️","♦️","♠️"][id]

        #figure out the card art
        base = "```\n{}----{}{}\n|     |\n| {}  |\n|     |\n{}{}----{}\n```"
        dChar = self.valChar
        sChar = ""
        if len(dChar) == 1:
            dChar = " " + dChar
            sChar = "-"
        self.art = base.format(self.suitChar,sChar,self.valChar,dChar,self.valChar,sChar,self.suitChar)
    def __str__(self):
        return "{} of {}s".format(self.valChar,self.suit)

class Deck():
    def __init__(self,shuffled = True):
        self.cards = []
        self.shuffled = shuffled
        self.locked = 0
    def populate(self,*,suits = ["heart","club","diamond","spade"],values = range(1,14)):
        for i in suits:
            for j in values:
                self.cards.append(Card(i,j))
    def draw(self,amount=1):
        drawn = []
        for i in range(amount):
            try:
                if self.shuffled:
                    ind = randint(0,len(self.cards))
                    drawn.append(self.cards.pop(ind))
                else:
                    drawn.append(self.cards.pop())
            except IndexError:
                return drawn
        return drawn
    @classmethod
    def full(cls,shuffled = True):
        d = cls(shuffled = shuffled)
        d.populate()
        return d
    @classmethod
    def locked(cls):
        d = cls()
        d.locked = -1
        return d

class CardDeck(Cog):
    def __init__(self,bot):
        self.bot = bot
        try:
            bot.decks
        except:
            bot.decks = {}

    async def parse_draw(self,ctx):
        # try to grab the deck for the guild
        deck = self.bot.decks.get(ctx.channel.guild.id,None)

        # if there isn't one then fail
        if deck == None:
            return ["There is no deck for this server. Generate one with `{}newdeck`".format(ctx.prefix),False]

        # otherwise, make sure it isn't locked
        elif deck.locked != 0:
            # if it is then say so and drop the lock level by one
            if self.bot.decks[ctx.channel.guild.id].locked > 1:
                self.bot.decks[ctx.channel.guild.id].locked -= 1
            return ["The deck is currently locked. Wait for other commands to finish first.",False]

        # if it's empty then say so
        elif deck.cards == []:
            return ["There are no cards on this deck. Generate a new one with `{}newdeck`".format(ctx.prefix),False]

        # lock it and try to draw a card
        self.bot.decks[ctx.channel.guild.id].locked = 1
        cards = deck.draw()
        if cards == []:
            return ["Something went wrong. Please try again.",False]
        else:
            card = cards[0]

        # unlock the deck and save it then return the card
        self.bot.decks[ctx.channel.guild.id] = deck
        self.bot.decks[ctx.channel.guild.id].locked = 0

        return ["{} drew **{}**\n{}".format(ctx.author.mention,str(card),card.art),True]

    @command()
    async def draw(self,ctx):
        """Draws a card from the server specific deck"""
        parsed = await self.parse_draw(ctx)
        if parsed[1]:
            await ctx.reply(parsed[0])
        else:
            await ctx.reply(parsed[0])
            await ctx.message.add_reaction("❌")

    @command()
    async def pdraw(self,ctx):
        """Draws a card from the server specific deck and DMs the result"""
        parsed = await self.parse_draw(ctx)
        if parsed[1]:
            try:
                await ctx.author.send(parsed[0])
                await ctx.message.add_reaction("✅")
            except:
                await ctx.reply("I need to be able to DM you for a private draw.")
        else:
            await ctx.reply(parsed[0])
            await ctx.message.add_reaction("❌")

    @command()
    async def newdeck(self,ctx):
        """Generates / regenerates the server specific deck"""

        if type(ctx.channel) == DMChannel:
            return await ctx.send("This command doesn't work in DMs. Try again in a server.")

        #checks for correct permissions
        if not ctx.author.guild_permissions.manage_messages:
            return await ctx.author.send("You can't do that without the server-wide `manage_messages` permission.")

        #grabs the correct deck and fills it
        d = self.bot.decks.get(ctx.channel.guild.id, None)
        self.bot.decks[ctx.channel.guild.id] = Deck.locked() #prevent changes
        if d == None:
            self.bot.decks[ctx.channel.guild.id] = Deck.full() #create a new, full deck
        else:
            self.bot.decks[ctx.channel.guild.id].populate() #refill the current deck (saves memory)
        self.bot.decks[ctx.channel.guild.id].locked = 0 #allow changes
        await ctx.reply("Successfully generated a new deck.")

    @command()
    async def deck(self,ctx):
        """Checks the amount of cards left in the deck"""
        #get the deck
        deck = self.bot.decks.get(ctx.channel.guild.id,None)
        #check if it's empty
        if deck == None or deck.cards == []:
            return await ctx.reply("The deck is empty.")
        await ctx.reply("There are {} card(s) left.".format(str(len(deck.cards))))

class DiceRolls(Cog):
    def __init__(self,bot):
        self.bot = bot
    async def parse_roll(self,ctx,stringle):
        #separate the comment
        parsed = stringle.split("~")
        result = roll(parsed[0].replace(" ",""))
        if len(parsed) > 1:
            parsed[1] = "\nReason: `{}`".format(parsed[1])
        else:
            parsed.append("")
        #make sure the result isn't too long
        if len(str(result)) > 500:
            result = "{} = `{}`".format(parsed[0],result.total)
        return "{}'s roll:\n{}{}".format(ctx.author.mention,str(result),parsed[1])

    @command()
    async def roll(self,ctx,*,stringle):
        """Rolls dice"""
        parsed = await self.parse_roll(ctx,stringle)
        await ctx.reply(parsed)

    @cog_ext.cog_slash(name = "roll",guild_ids = [795347025428348948])
    async def _slash_roll(self,ctx: SlashContext,*,params,comment = None):
        """Rolls dice"""
        parsed = await self.parse_roll(ctx,"{} ~ {}".format(params,comment) if comment else params)
        await ctx.send(parsed)

    @command()
    async def proll(self,ctx,*,stringle):
        """Rolls dice and DMs the result"""
        parsed = await self.parse_roll(ctx,stringle)
        try:
            await ctx.author.send(parsed)
            await ctx.message.add_reaction("✅")
        except:
            await ctx.reply("I need to be able to DM you for a private roll.")

cogs = [CardDeck,DiceRolls]

def setup(bot):
    configure_bot(bot)
    for i in cogs:
        bot.add_cog(i(bot))
