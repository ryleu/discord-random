from discord.ext import commands
import d20
import discord
import discord_slash
from discord_slash import cog_ext, model
from discord_slash.utils import manage_commands, manage_components
import logging
import secrets

class DiceRolls(commands.Cog):
    def __init__(self,bot):
        """Cog that contains all of the commands for rolling dice."""
        self.bot = bot
    # pylint: disable=no-self-use
    def parse_roll(self,params,*,comment=None,adv = d20.AdvType.NONE):
        try:
            result = d20.roll(params,None,False,{"Advantage":d20.AdvType.ADV,"Disadvantage":d20.AdvType.DIS,"None":d20.AdvType.NONE}[adv if adv else "None"])
        except d20.errors.TooManyRolls:
            return "You can't roll more than 1000 total dice."
        except d20.errors.RollSyntaxError as err:
            return f"""{str(err)}```\n{params}\n{(err.col-1)*" "+len(err.got)*"^"}\n```"""

        #make sure the result isn't too long
        if len(str(result)) > 500:
            result = f"{params} = `{result.total}`"
        return f"""
{str(result)}
{("Reason: "+ comment) if comment else ""}
"""

    @cog_ext.cog_slash(name = "roll", options = [
            manage_commands.create_option(
                name = "params",
                description = "Dice to roll",
                option_type = str,
                required = True
                ),
            manage_commands.create_option(
                name = "comment",
                description = "Comment to add to the end",
                option_type = str,
                required = False
                ),
            manage_commands.create_option(
                name = "private",
                description = "Sends the result privately",
                option_type = bool,
                required = False
                )
            ])
    async def _slash_roll(self,ctx: discord_slash.SlashContext,**kwargs):
        """Rolls dice."""
        private = kwargs.pop("private",None)
        await ctx.defer(hidden = private)
        await ctx.send(self.parse_roll(**kwargs), hidden = private)

    @cog_ext.cog_slash(name = "dice", options = [
            manage_commands.create_option(
                name = "size",
                description = "The die size",
                option_type = str,
                required = True,
                choices = ["d4","d6","d8","d10","d12","d20","d100"]
                ),
            manage_commands.create_option(
                name = "amount",
                description = "The amount of dice to roll (number)",
                option_type = int,
                required = False
                ),
            manage_commands.create_option(
                name = "private",
                description = "Sends the result privately",
                option_type = bool,
                required = False
                )
            ])
    async def _slash_dice(self, ctx: discord_slash.SlashContext, **kwargs):
        """Rolls dice (but for noobs)."""
        private = kwargs.pop("private",None)
        await ctx.defer(hidden = private)
        params = str(kwargs.pop("amount",1)) + kwargs.pop("size")
        await ctx.send(self.parse_roll(params = params,**kwargs),hidden = private,components=self.roll_components)

    roll_components = [
        manage_components.create_actionrow(
            manage_components.create_button(
                style = model.ButtonStyle.blurple,
                label = "d4",
                custom_id = "roll_d4"
            ),
            manage_components.create_button(
                style = model.ButtonStyle.blurple,
                label = "d6",
                custom_id = "roll_d6"
            ),
            manage_components.create_button(
                style = model.ButtonStyle.blurple,
                label = "d8",
                custom_id = "roll_d8"
            ),
            manage_components.create_button(
                style = model.ButtonStyle.blurple,
                label = "d10",
                custom_id = "roll_d10"
            ),
            manage_components.create_button(
                style = model.ButtonStyle.blurple,
                label = "d12",
                custom_id = "roll_d12"
            )
        ),
        manage_components.create_actionrow(
            manage_components.create_button(
                style = model.ButtonStyle.blurple,
                label = "d20",
                custom_id = "roll_d20"
            ),
            manage_components.create_button(
                style = model.ButtonStyle.blurple,
                label = "d100",
                custom_id = "roll_d100"
            )
        )
    ]

    async def button_roll_manager(self, ctx: discord_slash.ComponentContext, size: int):
        await ctx.defer()
        content = f"""{ctx.author.mention}'s roll:
1d{str(size)} = `{secrets.randbelow(size)+1}`"""
        await ctx.edit_origin(ctx.origin_message.content,components=[])
        await ctx.send(content,components=self.roll_components)

    @cog_ext.cog_component(components = "roll_d4")
    async def _d4_button_response(self, ctx: discord_slash.ComponentContext):
        await self.button_roll_manager(ctx,4)
    @cog_ext.cog_component(components = "roll_d6")
    async def _d6_button_response(self, ctx: discord_slash.ComponentContext):
        await self.button_roll_manager(ctx,6)
    @cog_ext.cog_component(components = "roll_d8")
    async def _d8_button_response(self, ctx: discord_slash.ComponentContext):
        await self.button_roll_manager(ctx,8)
    @cog_ext.cog_component(components = "roll_d10")
    async def _d10_button_response(self, ctx: discord_slash.ComponentContext):
        await self.button_roll_manager(ctx,10)
    @cog_ext.cog_component(components = "roll_d12")
    async def _d12_button_response(self, ctx: discord_slash.ComponentContext):
        await self.button_roll_manager(ctx,12)
    @cog_ext.cog_component(components = "roll_d20")
    async def _d20_button_response(self, ctx: discord_slash.ComponentContext):
        await self.button_roll_manager(ctx,20)
    @cog_ext.cog_component(components = "roll_d100")
    async def _d100_button_response(self, ctx: discord_slash.ComponentContext):
        await self.button_roll_manager(ctx,100)

def setup(bot):
    bot.add_cog(DiceRolls(bot))
