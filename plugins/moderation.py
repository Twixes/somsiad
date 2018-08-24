# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import asyncio
import discord
from discord.ext import commands
from somsiad_helper import *


@somsiad.client.command(aliases=['wyczyść', 'wyczysc'])
@commands.cooldown(1, somsiad.conf['user_command_cooldown_seconds'], commands.BucketType.user)
@commands.guild_only()
async def purge(ctx, *args):
    """Removes last n messages in the channel."""
    if somsiad.does_member_have_elevated_permissions(ctx.author):
        number_of_messages_to_delete = 1
        if args:
            number_of_messages_to_delete = int(args[0]) if int(args[0]) < 50 else 50

        messages_noun_variant = Informator.noun_variant(number_of_messages_to_delete, 'wiadomość', 'wiadomości')
        last_adjective_variant = Informator.adjective_variant(
            number_of_messages_to_delete, 'ostatnią', 'ostatnie', 'ostatnich'
        )

        await ctx.channel.purge(limit=number_of_messages_to_delete+1)

        embed = discord.Embed(
            title=f':white_check_mark: Usunięto z kanału {number_of_messages_to_delete} {last_adjective_variant} '
            f'{messages_noun_variant}',
            description='Ta wiadomość ulegnie autodestrukcji w ciągu 5 sekund od wysłania.',
            color=somsiad.color)

        await ctx.send(embed=embed, delete_after=5)
