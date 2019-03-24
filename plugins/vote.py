# Copyright 2018-2019 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import asyncio
import locale
import datetime as dt
from typing import Union, Optional
import discord
from somsiad import somsiad
from utilities import TextFormatter, interpret_str_as_datetime


@somsiad.bot.command(aliases=['głosowanie', 'glosowanie'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def vote(
        ctx, duration: Optional[Union[float, locale.atof, interpret_str_as_datetime]] = None,
        *, statement: discord.ext.commands.clean_content(fix_channel_mentions=True)
    ):
    """Holds a vote."""
    now_datetime = dt.datetime.now().astimezone()
    if isinstance(duration, dt.datetime) and now_datetime < duration <= now_datetime + dt.timedelta(days=7):
        results_datetime = duration
        results_and_now_timedelta = results_datetime - now_datetime
        seconds = results_and_now_timedelta.total_seconds()
        human_readable_time = TextFormatter.human_readable_time(seconds)
        embed = discord.Embed(
            title=f':ballot_box: {statement}',
            description=(
                'Zagłosuj w tej sprawie przy użyciu reakcji.\n'
                f'Wynik zostanie ogłoszony {duration.strftime("%-d %B %Y o %H:%M")}.'
            ),
            timestamp=results_datetime,
            color=somsiad.color
        )
    elif isinstance(duration, float) and 0.0 < duration <= 10080.0:
        seconds = duration * 60.0
        results_datetime = now_datetime + dt.timedelta(seconds=seconds)
        human_readable_time = TextFormatter.human_readable_time(seconds)
        embed = discord.Embed(
            title=f':ballot_box: {statement}',
            description=(
                'Zagłosuj w tej sprawie przy użyciu reakcji.\n'
                f'Wynik zostanie ogłoszony po {TextFormatter.human_readable_time(seconds)} od rozpoczęcia głosowania.'
            ),
            timestamp=results_datetime,
            color=somsiad.color
        )
    else:
        seconds = None
        embed = discord.Embed(
            title=f':ballot_box: {statement}',
            description='Zagłosuj w tej sprawie przy użyciu reakcji.',
            color=somsiad.color
        )

    message = await ctx.send(ctx.author.mention, embed=embed)
    await message.add_reaction('✅')
    await message.add_reaction('🔴')

    if seconds is not None:
        await asyncio.sleep(seconds)

        try:
            message_final = await ctx.channel.get_message(message.id)
        except discord.NotFound:
            pass
        else:
            results = {reaction.emoji: reaction.count for reaction in message_final.reactions}

            if results["✅"] > results["🔴"]:
                results_emoji = ':white_check_mark:'
            elif results["✅"] < results["🔴"]:
                results_emoji = ':red_circle:'
            else:
                results_emoji = ':question:'

            embed_results = discord.Embed(
                title=f'{results_emoji} {statement}',
                description=(
                    f'Głosowanie zostało zakończone po {human_readable_time} od rozpoczęcia.'
                ),
                timestamp=results_datetime,
                color=somsiad.color
            )
            embed_results.add_field(name='Za', value=results['✅']-1)
            embed_results.add_field(name='Przeciw', value=results['🔴']-1)

            await message_final.edit(embed=embed_results)
            await ctx.send(ctx.author.mention, embed=embed_results)


@vote.error
async def vote_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        embed = discord.Embed(
            title=f':warning: Nie podano sprawy w jakiej ma się odbyć głosowanie!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)
