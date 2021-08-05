# Copyright 2018-2020 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from somsiad import SomsiadMixin
from discord.ext import commands

from core import cooldown


class Emoticons(commands.Cog, SomsiadMixin):

    @commands.command(aliases=['lenny'])
    @cooldown()
    async def lennyface(self, ctx):
        """( ͡° ͜ʖ ͡°)"""
        await self.bot.send(ctx, '( ͡° ͜ʖ ͡°)', mention=False)

    @commands.command(aliases=['lenno'])
    @cooldown()
    async def lennoface(self, ctx):
        """( ͡ʘ ͜ʖ ͡ʘ)"""
        await self.bot.send(ctx, '( ͡ʘ ͜ʖ ͡ʘ)', mention=False)

    @commands.command(aliases=['wywróć'])
    @cooldown()
    async def tableflip(self, ctx):
        """(╯°□°）╯︵ ┻━┻"""
        await self.bot.send(ctx, '(╯°□°）╯︵ ┻━┻', mention=False)

    @commands.command(aliases=['odstaw'])
    @cooldown()
    async def unflip(self, ctx):
        """┬─┬ ノ( ゜-゜ノ)"""
        await self.bot.send(ctx, '┬─┬ ノ( ゜-゜ノ)', mention=False)

    @commands.command()
    @cooldown()
    async def shrug(self, ctx):
        r"""¯\_(ツ)_/¯"""
        await self.bot.send(ctx, r'¯\_(ツ)_/¯', mention=False)

    @commands.command(aliases=['dej'])
    @cooldown()
    async def gib(self, ctx, *, thing=None):
        """༼ つ ◕_◕ ༽つ"""
        if thing is None:
            await self.bot.send(ctx, '༼ つ ◕_◕ ༽つ', mention=False)
        elif 'fccchk' in thing:
            await self.bot.send(ctx, f'༼ つ :japanese_goblin: ༽つ {thing}', mention=False)
        else:
            await self.bot.send(ctx, f'༼ つ ◕_◕ ༽つ {thing}', mention=False)

    @commands.command()
    @cooldown()
    async def fccchk(self, ctx):
        """:japanese_goblin:"""
        await self.bot.send(ctx, ':japanese_goblin:', mention=False)


def setup(bot: commands.Bot):
    bot.add_cog(Emoticons(bot))
