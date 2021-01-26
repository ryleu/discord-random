import discord
from discord.ext import commands
import json
import random
from asyncio import sleep

with open("token.json","r") as file:
    token = json.loads(file.read())["token"]

me = commands.Bot("!")

me.decks = {}

# A  2  3  4  5  6  7  8  9 10  J  Q  K
# 1  2  3  4  5  6  7  8  9 10 11 12 13

class Card():
    def __init__(self,suit,value):
        self.suit = suit
        self.value = value
        if self.value > 10:
            self.valChar = ["J","Q","K"][self.value - 11]
        elif self.value == 1:
            self.valChar = "A"
        else:
            self.valChar = str(self.value)
        id = ["heart","club","diamond","spade"].index(self.suit)
        self.suitChar = ["♥️","♣️","♦️","♠️"][id]

        #figure out the card art
        base = "```\n{}----{}\n|     |\n| {}  |\n|     |\n{}----{}\n```"
        dChar = self.valChar
        if len(dChar) == 1:
            dChar = " " + dChar
        self.art = base.format(self.suitChar,self.valChar,dChar,self.valChar,self.suitChar)
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
                    ind = random.randint(0,len(self.cards))
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


@me.command()
async def draw(ctx):
    deck = me.decks.get(ctx.channel.id,None)
    if deck == None:
        return await ctx.send("There is no deck for this channel. Generate one with `!newdeck`")
    elif deck.locked != 0:
        await ctx.send("The deck is currently locked. Wait for other commands to finish first.")
        await sleep(1)
        if me.decks[ctx.channel.id].locked > 1:
            me.decks[ctx.channel.id].locked -= 1
        return
    elif deck.cards == []:
        return await ctx.send("There are no cards on this deck. Generate a new one with `!newdeck`")

    me.decks[ctx.channel.id].locked = 1
    cards = deck.draw()
    if cards == []:
        return await ctx.send("Something went wrong. Please try again.")
    else:
        card = cards[0]
    me.decks[ctx.channel.id] = deck
    me.decks[ctx.channel.id].locked = 0

    await ctx.send("{} drew **{}**\n{}".format(ctx.author.mention,str(card),card.art),allowed_mentions = discord.AllowedMentions.none())

@me.command()
async def newdeck(ctx):
    if not ctx.author.permissions_in(ctx.channel).manage_messages:
        return await ctx.author.send("You can't do that without the `manage_messages` permission.")
    d = me.decks.get(ctx.channel.id, None)
    me.decks[ctx.channel.id] = Deck.locked()
    if d == None:
        me.decks[ctx.channel.id] = Deck.full()
    else:
        me.decks[ctx.channel.id].populate()
    me.decks[ctx.channel.id].locked = 0
    await ctx.send("Successfully generated a new deck.")

@me.command()
async def deck(ctx):
    deck = me.decks.get(ctx.channel.id,None)
    if deck == None or deck.cards == []:
        return await ctx.send("The deck is empty.")
    await ctx.send("There are {} card(s) left.".format(str(len(deck.cards))))

handle_errors = me.on_command_error

@me.event
async def on_command_error(ctx,err):
    if type(err) == discord.ext.commands.errors.CommandNotFound:
        return
    await ctx.send("Something went wrong, please try again.")
    await handle_errors(ctx,err)

@me.event
async def on_ready():
    print("ready!")

me.run(token)
