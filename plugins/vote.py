# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import asyncio
import datetime as dt
from typing import Optional
import discord
from somsiad import somsiad
from utilities import TextFormatter


@somsiad.bot.command(aliases=['głosowanie', 'glosowanie'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def vote(ctx, seconds: Optional[int] = 0, *, statement):
    """Holds a vote."""
    hours_minutes_seconds = TextFormatter.hours_minutes_seconds(seconds)
    if 0 < seconds <= 604800:
        embed = discord.Embed(
            title=f':ballot_box: {statement}',
            description=(
                'Zagłosuj w tej sprawie przy użyciu reakcji.\n'
                f'Wynik zostanie ogłoszony po {hours_minutes_seconds} od rozpoczęcia głosowania.'
            ),
            timestamp=dt.datetime.now().astimezone()+dt.timedelta(seconds=seconds),
            color=somsiad.color
        )
    else:
        embed = discord.Embed(
            title=f':ballot_box: {statement}',
            description='Zagłosuj w tej sprawie przy użyciu reakcji.',
            color=somsiad.color
        )

    message = await ctx.send(ctx.author.mention, embed=embed)
    await message.add_reaction('✅')
    await message.add_reaction('🔴')

    if 0 < seconds <= 604800:
        await asyncio.sleep(seconds)

        try:
            message_final = await ctx.channel.get_message(message.id)

            results = {reaction.emoji: reaction.count for reaction in message_final.reactions}

            if results["✅"] > results["🔴"]:
                results_emoji = ":white_check_mark:"
            elif results["✅"] < results["🔴"]:
                results_emoji = ":red_circle:"
            else:
                results_emoji = ":question:"

            embed_results = discord.Embed(
                title=f'{results_emoji} {statement}',
                description=(
                    f'Głosowanie zostało zakończone po {hours_minutes_seconds} od rozpoczęcia.'
                ),
                timestamp=dt.datetime.now().astimezone(),
                color=somsiad.color
            )
            embed_results.add_field(name='Za', value=results['✅']-1)
            embed_results.add_field(name='Przeciw', value=results['🔴']-1)

            await message_final.edit(embed=embed_results)
            await ctx.send(ctx.author.mention, embed=embed_results)
        except discord.NotFound:
            pass
