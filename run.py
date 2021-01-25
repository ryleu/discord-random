import discord
from discord.ext import commands
import json
import random

me = commands.Bot("!")

class Card():
    def __init__(self,suit,value):
        self.suit = suit
        self.value = value
    def valChar(self):
        if self.value > 10:
            return ["J","Q","K"][self.value - 11]
        elif self.value == 0:
            return "A"
        else:
            return str(self.value)
    def suitChar(self):
        id = ["heart","club","diamond","spade"].index(self.suit)
        return ["♥️","♣️","♦️","♠️"][id]
    def art(self):
        base = "```\n{}----{}\n|    |\n| {} |\n|    |\n{}----{}\n```"
        dChar = self.valChar()
        if len(dChar) == 1:
            dChar = " " + dChar
        calculated = base.format()

@me.command()
async def deal(self, ctx, *, roles: discord.Role):
    members = {}
    if roles = None:
        rolesEdit = [ctx.guild.default_role]
    else:
        rolesEdit = roles
    for i in rolesEdit:
        for j in i.members:
            members[j.id] = j
