import discord
import discord_slash
from discord.ext import commands
from discord_slash import cog_ext


class Info(commands.Cog):
    """Class to display the info of the bot."""

    @cog_ext.cog_slash(name="info")
    async def _info(self, ctx: discord_slash.SlashContext):
        """Displays the info of the bot."""
        await ctx.defer()
        # Create an embed to store the info
        embed = discord.Embed(title="D&D Random Info", color=discord.Color(0x00FFFF))
        # Add the source code link to the embed
        embed.add_field(name="Source Code", value="[Click here to view the source code.]("
                                                  "https://github.com/ryleu/discord-cardic-inspiration)")
        # Add the invite link to the embed
        embed.add_field(name="Invite", value="[Click here to invite me.]("
                                             "https://discord.com/api/oauth2/authorize?client_id=803318907950596106"
                                             "&permissions=0&scope=applications.commands%20bot)")
        # Add the syntax link to the embed
        embed.add_field(name="Syntax", value="[Click here to see the syntax.]("
                                             "https://github.com/avrae/d20#dice-syntax)")
        # Add the bot author to the embed
        embed.set_footer(text="Created by ryleu#0001")

        # Send the embed
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    """Cog setup function."""
    bot.add_cog(Info())
