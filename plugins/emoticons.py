# Copyright 2018-2020 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from discord.ext import commands
from core import somsiad
from configuration import configuration


class Emoticons(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['lenny'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def lennyface(self, ctx):
        """( ͡° ͜ʖ ͡°)"""
        await self.bot.send(ctx, '( ͡° ͜ʖ ͡°)', mention=False)

    @commands.command(aliases=['lenno'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def lennoface(self, ctx):
        """( ͡ʘ ͜ʖ ͡ʘ)"""
        await self.bot.send(ctx, '( ͡ʘ ͜ʖ ͡ʘ)', mention=False)

    @commands.command(aliases=['wywróć'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def tableflip(self, ctx):
        """(╯°□°）╯︵ ┻━┻"""
        await self.bot.send(ctx, '(╯°□°）╯︵ ┻━┻', mention=False)

    @commands.command(aliases=['odstaw'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def unflip(self, ctx):
        """┬─┬ ノ( ゜-゜ノ)"""
        await self.bot.send(ctx, '┬─┬ ノ( ゜-゜ノ)', mention=False)

    @commands.command()
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def shrug(self, ctx):
        r"""¯\_(ツ)_/¯"""
        await self.bot.send(ctx, r'¯\_(ツ)_/¯', mention=False)

    @commands.command(aliases=['dej'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def gib(self, ctx, *, thing = None):
        """༼ つ ◕_◕ ༽つ"""
        if thing is None:
            await self.bot.send(ctx, '༼ つ ◕_◕ ༽つ', mention=False)
        elif 'fccchk' in thing:
            await self.bot.send(ctx, f'༼ つ :japanese_goblin: ༽つ {thing}', mention=False)
        else:
            await self.bot.send(ctx, f'༼ つ ◕_◕ ༽つ {thing}', mention=False)

    @commands.command()
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def fccchk(self, ctx):
        """:japanese_goblin:"""
        await self.bot.send(ctx, ':japanese_goblin:', mention=False)


somsiad.add_cog(Emoticons(somsiad))
