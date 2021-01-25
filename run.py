import discord
from discord.ext import commands
import json
import random

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
    def __init__(self,shuffled = True,*,suits = ["heart","club","diamond","spade"],values = range(1,14)):
        self.cards = []
        for i in suits:
            for j in values:
                self.cards.append(Card(i,j))
        self.shuffled = shuffled
        self.locked = 0
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

@me.command()
async def draw(ctx):
    deck = me.decks.get(ctx.channel.id,None)
    if deck == None:
        return await ctx.send("There is no deck for this channel. Generate one with `!newdeck`")
    elif deck.locked:
        me.decks[ctx.channel.id].locked -= 1
        return await ctx.send("The deck is currently locked. Wait for other commands to finish first ({}).".format(str(deck.locked)))
    elif deck.cards == []:
        return await ctx.send("There are no cards on this deck. Generate a new one with `!newdeck`")

    me.decks[ctx.channel.id].locked = 3
    card = deck.draw()[0]
    me.decks[ctx.channel.id] = deck
    me.decks[ctx.channel.id].locked = 0

    await ctx.send("{} drew **{}**\n{}".format(ctx.author.mention,str(card),card.art))

@me.command()
async def newdeck(ctx):
    if not ctx.author.permissions_in(ctx.channel).manage_messages:
        return await ctx.author.send("You can't do that without the `manage_messages` permission.")
    me.decks[ctx.channel.id] = Deck()
    await ctx.send("Successfully generated a new deck.")

@me.command()
async def deck(ctx):
    deck = me.decks.get(ctx.channel.id,None)
    if deck == None or deck.cards == []:
        return await ctx.send("The deck is empty.")
    await ctx.send("There are {} card(s) left.".format(str(len(deck.cards))))

@me.event
async def on_ready():
    print("ready!")

me.run(token)
