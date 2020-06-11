# Copyright 2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from collections import Counter
from discord.ext import commands
from core import cooldown
from utilities import word_number_form


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['role'])
    @cooldown()
    @commands.guild_only()
    async def roles(self, ctx):
        roles_counter = Counter((role for member in ctx.guild.members for role in member.roles))
        roles = reversed(ctx.guild.roles[1:])
        role_parts = [
            f'{role.mention} – `{str(role.color).upper()}` – 👥 {roles_counter[role]}' for role in roles
        ]
        embed = self.bot.generate_embed(
            '🔰', word_number_form(len(role_parts), 'rola', 'role', 'ról'),
            '\n'.join(role_parts) if role_parts else None
        )
        await self.bot.send(ctx, embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Roles(bot))
