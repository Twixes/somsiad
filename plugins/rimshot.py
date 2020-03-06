# Copyright 2018-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from discord.ext import commands
from core import somsiad
from configuration import configuration


class Rimshot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['badum', 'badumtss'])
    @commands.cooldown(
        1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
    )
    async def rimshot(self, ctx):
        """Ba dum tss!"""
        file = discord.File(fp='./data/BA-DUM-TSS.mp3')
        await self.bot.send(ctx, file=file)


def setup(bot: commands.Bot):
    bot.add_cog(Rimshot(bot))
