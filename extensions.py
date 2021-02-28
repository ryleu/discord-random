from discord.ext.commands import when_mentioned_or, command, Cog, has_guild_permissions
from d20 import roll
from d20.errors import TooManyRolls
from random import randint
from discord import AllowedMentions, DMChannel
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

def configure_bot(bot):
    bot.allowed_mentions = AllowedMentions.none()
    bot.command_prefix = when_mentioned_or("?")

class Card():
    def __init__(self,suit,value):
        # initialize the card with a suit and a value
        self.suit = suit
        self.value = value

        # set the icon to the proper thing
        # [("1" + x if x == "0" else x + " ") for x in "?A234567890JQK"]

        id = ["heart","club","diamond","spade"].index(self.suit)
        self.suitChar = ["♥️","♣️","♦️","♠️"][id]

        #figure out the card art
        base = "```\n{suit}----{dash}{value}\n|     |\n|  {center} |\n|     |\n{value}{dash}----{suit}\n```"
        self.art = base.format(
                suit = self.suitChar,
                value = self.valChar,
                center = (self.valChar if len(self.valChar) > 1 else self.valChar + " "),
                dash = "-" if len(self.valChar) == 1 else ""
            )
    def __str__(self):
        return "{} of {}s".format(self.valChar,self.suit)
    @property
    def valChar(self):
        return ['?', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'][self.value]

class Deck():
    def __init__(self,*,shuffled = True,allow_private = False):
        self.cards = []
        self.shuffled = shuffled
        self.locked = 0
        self.allow_private = allow_private
    def populate(self,*,suits = ["heart","club","diamond","spade"],values = range(1,14),allow_private = None):
        if allow_private != None:
            self.allow_private = allow_private
        for i in suits:
            for j in values:
                self.cards.append(Card(i,j))
        return self
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
    def extend(self, list):
        self.cards.extend(list)
        return self
    def lock(self):
        self.locked = -1
        return self
    @classmethod
    def full(cls,*args,**kwargs):
        return cls(*args, **kwargs).populate()
    @classmethod
    def locked(cls):
        return cls().lock()

class CardDeck(Cog):
    def __init__(self,bot):
        self.bot = bot
        try:
            bot.decks
        except:
            bot.decks = {}

    def parse_draw(self,ctx,private = False):
        # try to grab the deck for the guild
        deck = self.bot.decks.get(ctx.channel.guild.id,None)

        # if there isn't one then fail
        if deck == None:
            return ["There is no deck for this server. Generate one with `newdeck`",False]

        if private and not deck.allow_private:
            return ["This deck does not allow private drawing.",False]

        # otherwise, make sure it isn't locked
        elif deck.locked != 0:
            # if it is then say so and drop the lock level by one
            if self.bot.decks[ctx.channel.guild.id].locked > 1:
                self.bot.decks[ctx.channel.guild.id].locked -= 1
            return ["The deck is currently locked. Wait for other commands to finish first.",False]

        # if it's empty then say so
        elif deck.cards == []:
            return ["There are no cards on this deck. Generate a new one with `newdeck`",False]

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

        return ["{} drew **{}**\n{}".format(ctx.author.mention,str(card),card.art),True,cards]

    @command()
    async def draw(self,ctx):
        """Draws a card from the server specific deck"""
        parsed = self.parse_draw(ctx)
        if parsed[1]:
            await ctx.reply(parsed[0])
        else:
            await ctx.reply(parsed[0])
            await ctx.message.add_reaction("❌")

    @cog_ext.cog_slash(name = "draw", options = [
            create_option("private","Sends the result privately",5,False)
            ])
    async def _slash_draw(self,ctx: SlashContext, private: bool = False):
        """Draws a card from the server specific deck"""
        parsed = self.parse_draw(ctx,private)
        await ctx.ack()
        await ctx.send(parsed[0], hidden = private)

    @command()
    async def pdraw(self,ctx):
        """Draws a card from the server specific deck and DMs the result"""
        parsed = self.parse_draw(ctx,True)
        if parsed[1]:
            try:
                await ctx.author.send(parsed[0])
                await ctx.message.add_reaction("✅")
            except:
                self.bot.decks[ctx.channel.guild.id].extend(parsed[2])
                await ctx.reply("I need to be able to DM you for a private draw.")
        else:
            await ctx.reply(parsed[0])
            await ctx.message.add_reaction("❌")

    @command()
    @has_guild_permissions(manage_messages = True)
    async def newdeck(self,ctx, allow_private = False):
        """Generates / regenerates the server specific deck"""
        #grabs the correct deck and fills it
        d = self.bot.decks.get(ctx.channel.guild.id, None)
        self.bot.decks[ctx.channel.guild.id] = Deck.locked() #prevent changes
        self.bot.decks[ctx.channel.guild.id] = Deck.full(allow_private = allow_private) #create a new, full deck
        await ctx.reply("Successfully generated a new deck.")

    @cog_ext.cog_subcommand(base = "deck", name = "new", options = [
            create_option("allow_private","Enables private drawing",5,False)
            ])
    async def _slash_newdeck(self,ctx: SlashContext, allow_private: bool = False):
        """Generates / regenerates the server specific deck"""
        await ctx.ack()
        message = await ctx.send("Working...")
        try:
            assert ctx.author.guild_permissions.manage_messages
        except AttributeError:
            await message.edit(content = "I need to be in the server to do this.")
        except AssertionError:
            await message.edit(content = "You need server-wide manage messages to do this.")
        else:
            #grabs the correct deck and fills it
            d = self.bot.decks.get(ctx.channel.guild.id, None)
            self.bot.decks[ctx.channel.guild.id] = Deck.locked() #prevent changes
            self.bot.decks[ctx.channel.guild.id] = Deck.full(allow_private = allow_private) #create a new, full deck
            await message.edit(content = "Successfully generated a new deck.")

    @command()
    async def deck(self,ctx):
        """Checks the amount of cards left in the deck"""
        #get the deck
        deck = self.bot.decks.get(ctx.channel.guild.id,None)
        #check if it's empty
        if deck == None or deck.cards == []:
            await ctx.reply("The deck is empty.")
        else:
            await ctx.reply("There are {} card(s) left.".format(str(len(deck.cards))))

    @cog_ext.cog_subcommand(base = "deck", name = "cards")
    async def _slash_deck(self,ctx: SlashContext):
        """Checks the amount of cards left in the deck"""
        print("hi")
        await ctx.ack()
        #get the deck
        deck = self.bot.decks.get(ctx.channel.guild.id,None)
        #check if it's empty
        if deck == None or deck.cards == []:
            await ctx.send("The deck is empty.")
        else:
            await ctx.send("There are {} card(s) left.".format(str(len(deck.cards))))

class DiceRolls(Cog):
    def __init__(self,bot):
        self.bot = bot
    def parse_roll(self,ctx,stringle):
        #separate the comment
        parsed = stringle.split("~")
        try:
            result = roll(parsed[0].replace(" ",""))
        except TooManyRolls:
            return "You can't roll more than 1000 total dice."
        if len(parsed) > 1:
            parsed[1] = "\nReason: `{}`".format(parsed[1])
            while parsed[1].startswith(" "):
                parsed[1] = parsed[1][1:]
        else:
            parsed.append("")
        #make sure the result isn't too long
        if len(str(result)) > 500:
            result = "{} = `{}`".format(parsed[0],result.total)
        return "{}'s roll:\n{}{}".format(ctx.author.mention,str(result),parsed[1])

    @command()
    async def roll(self,ctx,*,stringle):
        """Rolls dice"""
        parsed = self.parse_roll(ctx,stringle)#,options = [{""}]
        await ctx.reply(parsed)

    @cog_ext.cog_slash(name = "roll", options = [
            create_option("params","Dice to roll",3,True),
            create_option("comment","Comment to add to the end",3,False),
            create_option("private","Sends the result privately",5,False)
            ])
    async def _slash_roll(self,ctx: SlashContext,params: str,comment: str = None, private: bool = False):
        """Rolls dice"""
        toParse = (ctx,"{} ~ {}".format(params,comment) if comment else params)
        if private:
            await ctx.ack()
            if len(params) > 5:
                await ctx.send_hidden("Large private rolls are currently not supported.")
            else:
                await ctx.send_hidden(self.parse_roll(*toParse))
        else:
            message = await ctx.send("Calculating...")
            parsed = self.parse_roll(*toParse)
            await message.edit(content = parsed)

    @cog_ext.cog_slash(name = "dice", options = [
            create_option("type","Die type to roll",3,True,["d4 ","d6 ","d8 ","d10","d12","d20","d100"]),
            create_option("amount","Amount of dice to roll",4,False,[1,2,3,4,5,6,7,8,9]),
            create_option("comment","Comment to add to the end",3,False),
            create_option("private","Sends the result privately",5,False)
            ])
    async def _slash_dice(self,ctx: SlashContext, type: str, amount: int = 1, comment: str = None, private: bool = False):
        """Rolls dice (but for noobs)"""
        await ctx.send(self.parse_roll(*(ctx,"{} ~ {}".format(str(amount)+type,comment) if comment else str(amount)+type)), hidden = private)

    '''
    @cog_ext.cog_slash(name = "testroll",guild_ids = [712731280772694198], options = [
            create_option("params","Dice to roll",3,True),
            create_option("comment","Comment to add to the end",3,False),
            create_option("private","Sends the result privately",5,False)
            ])
    async def _t_slash_roll(self,ctx: SlashContext,params: str,comment: str = None, private: bool = False):
        """Rolls dice"""
        await ctx.ack()
        parsed = await self.parse_roll(ctx,"{} ~ {}".format(params,comment) if comment else params)
        await ctx.send(parsed,hidden = private)
    '''

    @command()
    async def proll(self,ctx,*,stringle):
        """Rolls dice and DMs the result"""
        parsed = self.parse_roll(ctx,stringle)
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
